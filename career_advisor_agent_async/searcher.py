import asyncio
import os
from typing import Dict, List
import aiohttp
from bs4 import BeautifulSoup

COURSES_SEARCH_URLS = {
    "coursera": "https://www.coursera.org/search?query={query}",
    "stepik": "https://stepik.org/catalog/search?query={query}"
}
HABR_ARTICLES_SEARCH_URL = "https://habr.com/ru/search/?q={query}&target_type=posts&order=relevance"
HABR_VACANCY_SEARCH_URL = "https://career.habr.com/vacancies?keywords={query}"
GITHUB_SEARCH_API = "https://api.github.com/search/repositories?q={query}+in:name,description&sort=stars"
KAGGLE_COMPETITIONS_URL = "https://www.kaggle.com/competitions?search={query}"

async def fetch_text(session: aiohttp.ClientSession, url: str) -> str:
    """Вспомогательная корутина для получения текста страницы по URL."""
    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
        if response.status != 200:
            return ""
        return await response.text()

def parse_courses_from_coursera(html: str) -> List[Dict]:
    """Извлекает несколько курсов из HTML поисковой выдачи Coursera (топ-3)."""
    courses = []
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('h2', class_='card-title')
    for res in results[:3]:
        title = res.get_text().strip()
        link_tag = res.find_parent('a')
        link = "https://www.coursera.org" + link_tag['href'] if link_tag else ""
        if title:
            courses.append({"title": title, "url": link})
    return courses

def parse_courses_from_stepik(html: str) -> List[Dict]:
    """Извлекает несколько курсов из HTML поиска Stepik (топ-3)."""
    courses = []
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('a', class_='course-card__title')
    for res in results[:3]:
        title = res.get_text().strip()
        link = "https://stepik.org" + res['href']
        courses.append({"title": title, "url": link})
    return courses

def parse_articles_from_habr(html: str) -> List[Dict]:
    """Извлекает статьи из поисковой выдачи Хабра (топ-3)."""
    articles = []
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('article', class_='post')
    for res in results[:3]:
        title_tag = res.find('h2')
        title = title_tag.get_text().strip() if title_tag else "Статья"
        link_tag = res.find('a', class_='post__title_link')
        link = link_tag['href'] if link_tag else ""
        articles.append({"title": title, "url": link})
    return articles

def parse_vacancies_from_habr(html: str) -> List[Dict]:
    """Извлекает вакансии из выдачи Habr Career (топ-3)."""
    vacancies = []
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all('div', class_='vacancy-card__title')
    for card in cards[:3]:
        title_tag = card.find('a')
        title = title_tag.get_text().strip() if title_tag else "Вакансия"
        link = "https://career.habr.com" + title_tag['href'] if title_tag else ""
        vacancies.append({"title": title, "url": link})
    return vacancies

def parse_projects_from_github(json_data: dict) -> List[Dict]:
    """Извлекает топ-3 репозитория из ответа GitHub Search API (JSON)."""
    projects = []
    items = json_data.get('items', [])[:3]
    for repo in items:
        projects.append({
            "title": repo.get('name'),
            "url": repo.get('html_url'),
            "description": repo.get('description', '')
        })
    return projects

def parse_competitions_from_kaggle(html: str) -> List[Dict]:
    """Извлекает список соревнований с Kaggle (топ-3)."""
    comps = []
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.find_all('div', class_='competition-card__header')
    for card in cards[:3]:
        title_tag = card.find('div', class_='title')
        title = title_tag.get_text().strip() if title_tag else "Competition"
        link_tag = card.find_parent('a')
        link = "https://www.kaggle.com" + link_tag['href'] if link_tag else ""
        comps.append({"title": title, "url": link})
    return comps

async def find_resources_for_skill(skill: str, session: aiohttp.ClientSession) -> Dict[str, List[Dict]]:
    """
    Ищет ресурсы для указанного навыка по всем категориям (курсы, статьи, вакансии, проекты, соревнования).
    Возвращает словарь со списками найденных ресурсов по категориям.
    """
    query = skill
    tasks = []
    # Задачи для поиска курсов (Coursera и Stepik)
    tasks.append(fetch_text(session, COURSES_SEARCH_URLS["coursera"].format(query=query)))
    tasks.append(fetch_text(session, COURSES_SEARCH_URLS["stepik"].format(query=query)))
    # Задачи для статей и вакансий (Хабр)
    tasks.append(fetch_text(session, HABR_ARTICLES_SEARCH_URL.format(query=query)))
    tasks.append(fetch_text(session, HABR_VACANCY_SEARCH_URL.format(query=query)))
    # Задача для GitHub API (репозитории, с токеном при наличии)
    github_headers = {}
    gh_token = os.getenv("GITHUB_TOKEN")
    if gh_token:
        github_headers["Authorization"] = f"token {gh_token}"
    tasks.append(session.get(GITHUB_SEARCH_API.format(query=skill), headers=github_headers))
    # Задача для Kaggle (соревнования)
    tasks.append(fetch_text(session, KAGGLE_COMPETITIONS_URL.format(query=query)))

    # Выполняем все запросы параллельно (ошибки отдельных запросов не прерывают другие)
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    # Распаковываем результаты (или заменяем на пустое значение при ошибке)
    coursera_html = responses[0] if isinstance(responses[0], str) else ""
    stepik_html = responses[1] if isinstance(responses[1], str) else ""
    habr_articles_html = responses[2] if isinstance(responses[2], str) else ""
    habr_vacancies_html = responses[3] if isinstance(responses[3], str) else ""
    github_resp = responses[4]
    kaggle_html = responses[5] if isinstance(responses[5], str) else ""

    # Обрабатываем ответ GitHub API (получаем JSON или пустой словарь при ошибке)
    github_data = {}
    if isinstance(github_resp, aiohttp.ClientResponse):
        try:
            github_data = await github_resp.json()
        except Exception:
            github_data = {}
        finally:
            github_resp.close()
    else:
        github_data = {}

    # Парсим полученные данные по категориям
    resources = {
        "courses": parse_courses_from_coursera(coursera_html) + parse_courses_from_stepik(stepik_html),
        "articles": parse_articles_from_habr(habr_articles_html),
        "vacancies": parse_vacancies_from_habr(habr_vacancies_html),
        "projects": parse_projects_from_github(github_data),
        "competitions": parse_competitions_from_kaggle(kaggle_html)
    }
    return resources
