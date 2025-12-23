"""
Сервис для поиска ресурсов в интернете и сохранения в векторное хранилище
"""
import asyncio
import logging
import os
from typing import Dict, List
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from domain.entities import Resource, ResourceType
from domain.repositories import IResourceRepository

logger = logging.getLogger(__name__)

COURSES_SEARCH_URLS = {
    "coursera": "https://www.coursera.org/search?query={query}",
    "stepik": "https://stepik.org/catalog/search?query={query}"
}
HABR_ARTICLES_SEARCH_URL = "https://habr.com/ru/search/?q={query}&target_type=posts&order=relevance"
HABR_VACANCY_SEARCH_URL = "https://career.habr.com/vacancies?keywords={query}"
GITHUB_SEARCH_API = "https://api.github.com/search/repositories?q={query}+in:name,description&sort=stars"
KAGGLE_COMPETITIONS_URL = "https://www.kaggle.com/competitions?search={query}"


class WebSearcher:
    """Сервис для поиска ресурсов в интернете"""
    
    def __init__(self, resource_repository: IResourceRepository):
        """
        Инициализация сервиса поиска
        
        Args:
            resource_repository: Репозиторий ресурсов для сохранения
        """
        self.resource_repository = resource_repository
    
    async def fetch_text(self, session: aiohttp.ClientSession, url: str) -> str:
        """Получить текст страницы по URL"""
        try:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return ""
                return await response.text()
        except Exception as e:
            logger.warning(f"Ошибка получения {url}: {e}")
            return ""
    
    def parse_courses_from_coursera(self, html: str) -> List[Resource]:
        """Извлекает курсы из HTML Coursera"""
        courses = []
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('h2', class_='card-title')
        for res in results[:3]:
            title = res.get_text().strip()
            link_tag = res.find_parent('a')
            link = "https://www.coursera.org" + link_tag['href'] if link_tag else ""
            if title:
                courses.append(Resource(
                    title=title,
                    url=link,
                    resource_type=ResourceType.COURSE,
                    metadata={"source": "coursera"}
                ))
        return courses
    
    def parse_courses_from_stepik(self, html: str) -> List[Resource]:
        """Извлекает курсы из HTML Stepik"""
        courses = []
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('a', class_='course-card__title')
        for res in results[:3]:
            title = res.get_text().strip()
            link = "https://stepik.org" + res['href']
            courses.append(Resource(
                title=title,
                url=link,
                resource_type=ResourceType.COURSE,
                metadata={"source": "stepik"}
            ))
        return courses
    
    def parse_articles_from_habr(self, html: str) -> List[Resource]:
        """Извлекает статьи из HTML Хабра"""
        articles = []
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('article', class_='post')
        for res in results[:3]:
            title_tag = res.find('h2')
            title = title_tag.get_text().strip() if title_tag else "Статья"
            link_tag = res.find('a', class_='post__title_link')
            link = link_tag['href'] if link_tag else ""
            articles.append(Resource(
                title=title,
                url=link,
                resource_type=ResourceType.ARTICLE,
                metadata={"source": "habr"}
            ))
        return articles
    
    def parse_vacancies_from_habr(self, html: str) -> List[Resource]:
        """Извлекает вакансии из HTML Habr Career"""
        vacancies = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='vacancy-card__title')
        for card in cards[:3]:
            title_tag = card.find('a')
            title = title_tag.get_text().strip() if title_tag else "Вакансия"
            link = "https://career.habr.com" + title_tag['href'] if title_tag else ""
            vacancies.append(Resource(
                title=title,
                url=link,
                resource_type=ResourceType.VACANCY,
                metadata={"source": "habr_career"}
            ))
        return vacancies
    
    def parse_projects_from_github(self, json_data: dict) -> List[Resource]:
        """Извлекает проекты из ответа GitHub API"""
        projects = []
        items = json_data.get('items', [])[:3]
        for repo in items:
            projects.append(Resource(
                title=repo.get('name', ''),
                url=repo.get('html_url', ''),
                description=repo.get('description', ''),
                resource_type=ResourceType.PROJECT,
                metadata={"source": "github", "stars": repo.get('stargazers_count', 0)}
            ))
        return projects
    
    def parse_competitions_from_kaggle(self, html: str) -> List[Resource]:
        """Извлекает соревнования из HTML Kaggle"""
        comps = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='competition-card__header')
        for card in cards[:3]:
            title_tag = card.find('div', class_='title')
            title = title_tag.get_text().strip() if title_tag else "Competition"
            link_tag = card.find_parent('a')
            link = "https://www.kaggle.com" + link_tag['href'] if link_tag else ""
            comps.append(Resource(
                title=title,
                url=link,
                resource_type=ResourceType.COMPETITION,
                metadata={"source": "kaggle"}
            ))
        return comps
    
    async def find_resources_for_skill(self, skill: str) -> Dict[str, List[Resource]]:
        """
        Ищет ресурсы для указанного навыка и сохраняет в векторное хранилище
        
        Args:
            skill: Навык для поиска
            
        Returns:
            Словарь с ресурсами по категориям
        """
        query = skill
        tasks = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            # Задачи для поиска курсов
            tasks.append(self.fetch_text(session, COURSES_SEARCH_URLS["coursera"].format(query=query)))
            tasks.append(self.fetch_text(session, COURSES_SEARCH_URLS["stepik"].format(query=query)))
            
            # Задачи для статей и вакансий
            tasks.append(self.fetch_text(session, HABR_ARTICLES_SEARCH_URL.format(query=query)))
            tasks.append(self.fetch_text(session, HABR_VACANCY_SEARCH_URL.format(query=query)))
            
            # Задача для GitHub API
            github_headers = {}
            gh_token = os.getenv("GITHUB_TOKEN")
            if gh_token:
                github_headers["Authorization"] = f"token {gh_token}"
            tasks.append(session.get(GITHUB_SEARCH_API.format(query=skill), headers=github_headers))
            
            # Задача для Kaggle
            tasks.append(self.fetch_text(session, KAGGLE_COMPETITIONS_URL.format(query=query)))
            
            # Выполняем все запросы параллельно
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            coursera_html = responses[0] if isinstance(responses[0], str) else ""
            stepik_html = responses[1] if isinstance(responses[1], str) else ""
            habr_articles_html = responses[2] if isinstance(responses[2], str) else ""
            habr_vacancies_html = responses[3] if isinstance(responses[3], str) else ""
            github_resp = responses[4]
            kaggle_html = responses[5] if isinstance(responses[5], str) else ""
            
            # Обрабатываем ответ GitHub API
            github_data = {}
            if isinstance(github_resp, aiohttp.ClientResponse):
                try:
                    github_data = await github_resp.json()
                except Exception:
                    github_data = {}
                finally:
                    github_resp.close()
            
            # Парсим данные
            courses = self.parse_courses_from_coursera(coursera_html) + self.parse_courses_from_stepik(stepik_html)
            articles = self.parse_articles_from_habr(habr_articles_html)
            vacancies = self.parse_vacancies_from_habr(habr_vacancies_html)
            projects = self.parse_projects_from_github(github_data)
            competitions = self.parse_competitions_from_kaggle(kaggle_html)
            
            # Добавляем навык ко всем ресурсам
            all_resources = courses + articles + vacancies + projects + competitions
            for resource in all_resources:
                resource.skill = skill
            
            # Сохраняем в векторное хранилище
            if all_resources:
                await self.resource_repository.save_batch(all_resources)
                logger.info(f"Сохранено {len(all_resources)} ресурсов для навыка {skill}")
            
            return {
                "courses": courses,
                "articles": articles,
                "vacancies": vacancies,
                "projects": projects,
                "competitions": competitions
            }

