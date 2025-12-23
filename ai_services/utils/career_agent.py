

import asyncio
import json
import os
import aiohttp
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from openai import AsyncOpenAI


SCIBOX_API_URL = os.getenv("sk-1NTKTnsPLi-onek5rVQ5dw", "https://llm.t1v.scibox.tech/v1")
SCIBOX_API_KEY = os.getenv("sk-1NTKTnsPLi-onek5rVQ5dw")
SCIBOX_MODEL = os.getenv("SCIBOX_MODEL", "Qwen2.5-72B-Instruct-AWQ")


COURSES_SEARCH_URLS = {
    "coursera": "https://www.coursera.org/search?query={query}",
    "stepik": "https://stepik.org/catalog/search?query={query}"
}
HABR_ARTICLES_SEARCH_URL = "https://habr.com/ru/search/?q={query}&target_type=posts&order=relevance"
HABR_VACANCY_SEARCH_URL = "https://career.habr.com/vacancies?keywords={query}"
GITHUB_SEARCH_API = "https://api.github.com/search/repositories?q={query}+in:name,description&sort=stars"
KAGGLE_COMPETITIONS_URL = "https://www.kaggle.com/competitions?search={query}"


class CareerAgent:
    """
    Объединенный карьерный агент с поддержкой async-операций.
    Объединяет простые вызовы LLM и полный пайплайн анализа диалогов.
    """
    
    def __init__(self, api_key: str):
        """
        Инициализация агента.
        
        Args:
            api_key: API ключ для OpenAI-совместимого сервиса
        """
        self.api_key = api_key or SCIBOX_API_KEY
        self.llm_client = AsyncOpenAI(
            api_key=self.api_key, 
            base_url=SCIBOX_API_URL
        )
        self.model_name = SCIBOX_MODEL
    
    async def call_llm(self, prompt: str) -> str:
        """
        Вызов LLM-модели через OpenAI-совместимый API.
        
        Args:
            prompt: Текст промпта для модели
            
        Returns:
            Ответ модели в виде строки
        """
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Ошибка при вызове LLM: {e}")
    
    async def get_response(self, json_history: str) -> str:
        """
        Получает ответ от LLM на основе истории сообщений.
        
        Args:
            json_history: JSON-строка с историей сообщений
            
        Returns:
            Ответ модели в виде строки
        """
        message_history = json.loads(json_history)

        response = await self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=message_history,
            temperature=0.1,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    async def load_conversation(self, json_path: str) -> List[Dict]:
        """
        Загружает историю диалога из JSON-файла.
        
        Args:
            json_path: Путь к JSON-файлу с диалогом
            
        Returns:
            Список сообщений с полями 'role' и 'message'
        """
        def _load_file(path: str) -> List[Dict]:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        data = await asyncio.to_thread(_load_file, json_path)
        
        # Валидация структуры данных
        if not isinstance(data, list):
            raise ValueError("JSON файл должен содержать список сообщений")
        
        for msg in data:
            if 'role' not in msg or 'message' not in msg:
                raise ValueError("Сообщения должны содержать поля 'role' и 'message'")
        
        return data
    
    def format_conversation(self, messages: List[Dict]) -> str:
        """
        Преобразует список сообщений в единый текстовый диалог.
        
        Args:
            messages: Список сообщений диалога
            
        Returns:
            Форматированный текст диалога
        """
        formatted_lines = []
        for msg in messages:
            role = msg['role'].lower()
            content = msg['message']
            
            if role == 'user':
                formatted_lines.append(f"Пользователь: {content}")
            elif role in ('assistant', 'ai'):
                formatted_lines.append(f"Консультант: {content}")
            else:
                formatted_lines.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted_lines)
    
    async def analyze_dialog(self, dialog_text: str) -> Dict[str, Any]:
        """
        Анализирует диалог и извлекает профиль пользователя.
        
        Args:
            dialog_text: Текст диалога для анализа
            
        Returns:
            Словарь с профилем пользователя: goals, skills, experience, challenges, missing_skills
        """
        prompt = (
            "Проанализируй следующий диалог между карьерным консультантом и пользователем. "
            "Извлеки из диалога и перечисли:\n"
            "1. Цели пользователя в карьере.\n"
            "2. Его текущие навыки и опыт работы.\n"
            "3. Проблемы или затруднения, с которыми он сталкивается на текущей работе.\n"
            "4. Ключевые навыки или знания, которых ему не хватает для достижения целей.\n\n"
            "Дай ответ в формате JSON с полями: goals, skills, experience, challenges, missing_skills.\n"
            f"Диалог:\n{dialog_text}"
        )
        
        try:
            result_text = await self.call_llm(prompt)
            analysis = json.loads(result_text)
        except json.JSONDecodeError as e:
            print(f"Предупреждение: Не удалось распарсить ответ LLM как JSON: {e}")
            analysis = {
                "goals": "Не удалось извлечь цели",
                "skills": "Не удалось извлечь навыки", 
                "experience": "Не удалось извлечь опыт",
                "challenges": "Не удалось извлечь проблемы",
                "missing_skills": []
            }
        
        return analysis
    
    async def get_user_profile(self, dialog_text: str) -> Dict[str, Any]:
        """
        Извлекает профиль пользователя из текста диалога.
        
        Args:
            dialog_text: Текст диалога для анализа
            
        Returns:
            Словарь с профилем пользователя
        """
        return await self.analyze_dialog(dialog_text)
    
    async def fetch_text(self, session: aiohttp.ClientSession, url: str) -> str:
        """Получает текст страницы по URL."""
        try:
            async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status != 200:
                    return ""
                return await response.text()
        except Exception:
            return ""
    
    def parse_courses_from_coursera(self, html: str) -> List[Dict]:
        """Извлекает курсы из HTML Coursera."""
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
    
    def parse_courses_from_stepik(self, html: str) -> List[Dict]:
        """Извлекает курсы из HTML Stepik."""
        courses = []
        soup = BeautifulSoup(html, 'html.parser')
        results = soup.find_all('a', class_='course-card__title')
        for res in results[:3]:
            title = res.get_text().strip()
            link = "https://stepik.org" + res['href']
            courses.append({"title": title, "url": link})
        return courses
    
    def parse_articles_from_habr(self, html: str) -> List[Dict]:
        """Извлекает статьи из HTML Хабра."""
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
    
    def parse_vacancies_from_habr(self, html: str) -> List[Dict]:
        """Извлекает вакансии из HTML Habr Career."""
        vacancies = []
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.find_all('div', class_='vacancy-card__title')
        for card in cards[:3]:
            title_tag = card.find('a')
            title = title_tag.get_text().strip() if title_tag else "Вакансия"
            link = "https://career.habr.com" + title_tag['href'] if title_tag else ""
            vacancies.append({"title": title, "url": link})
        return vacancies
    
    def parse_projects_from_github(self, json_data: dict) -> List[Dict]:
        """Извлекает проекты из ответа GitHub API."""
        projects = []
        items = json_data.get('items', [])[:3]
        for repo in items:
            projects.append({
                "title": repo.get('name'),
                "url": repo.get('html_url'),
                "description": repo.get('description', '')
            })
        return projects
    
    def parse_competitions_from_kaggle(self, html: str) -> List[Dict]:
        """Извлекает соревнования из HTML Kaggle."""
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
    
    async def find_resources_for_skill(self, skill: str, session: aiohttp.ClientSession) -> Dict[str, List[Dict]]:
        """
        Ищет ресурсы для указанного навыка.
        
        Args:
            skill: Навык для поиска ресурсов
            session: HTTP сессия для запросов
            
        Returns:
            Словарь с ресурсами по категориям
        """
        query = skill
        tasks = []
        
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
        
        # Парсим полученные данные
        resources = {
            "courses": self.parse_courses_from_coursera(coursera_html) + self.parse_courses_from_stepik(stepik_html),
            "articles": self.parse_articles_from_habr(habr_articles_html),
            "vacancies": self.parse_vacancies_from_habr(habr_vacancies_html),
            "projects": self.parse_projects_from_github(github_data),
            "competitions": self.parse_competitions_from_kaggle(kaggle_html)
        }
        
        return resources
    
    async def find_career_resources(self, skills: List[str]) -> Dict[str, List[Dict]]:
        """
        Ищет карьерные ресурсы для указанных навыков.
        
        Args:
            skills: Список навыков для поиска ресурсов
            
        Returns:
            Словарь с ресурсами по категориям
        """
        combined_recommendations = {
            "courses": [], "articles": [], "vacancies": [], 
            "projects": [], "competitions": []
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            tasks = [self.find_resources_for_skill(skill, session) for skill in skills]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for skill, result in zip(skills, results):
                if isinstance(result, Exception):
                    continue
                
                for course in result.get("courses", []):
                    course["skill"] = skill
                    combined_recommendations["courses"].append(course)
                
                for article in result.get("articles", []):
                    article["skill"] = skill
                    combined_recommendations["articles"].append(article)
                
                for vac in result.get("vacancies", []):
                    vac["skill"] = skill
                    combined_recommendations["vacancies"].append(vac)
                
                for proj in result.get("projects", []):
                    proj["skill"] = skill
                    combined_recommendations["projects"].append(proj)
                
                for comp in result.get("competitions", []):
                    comp["skill"] = skill
                    combined_recommendations["competitions"].append(comp)
        
        return combined_recommendations
    
    def format_recommendations(self, user_profile: dict, recommendations: Dict[str, List[Dict]]) -> str:
        """
        Формирует промпт для генерации финальных рекомендаций.
        
        Args:
            user_profile: Профиль пользователя
            recommendations: Собранные рекомендации по категориям
            
        Returns:
            Форматированный промпт для LLM
        """
        goals = user_profile.get("goals", "")
        challenges = user_profile.get("challenges", "")
        missing_skills = user_profile.get("missing_skills", [])
        
        intro = (f"Пользователь стремится: {goals}.\n"
                 f"Текущие трудности: {challenges}.\n"
                 f"Выявленные пробелы в навыках: {', '.join(missing_skills)}.\n\n")
        
        intro += "На основании этого, сгенерируй персональные рекомендации для пользователя. " \
                 "Представь их структурировано по категориям (курсы, статьи, вакансии, проекты, соревнования) " \
                 "и поясни, как каждый пункт поможет закрыть пробелы и достичь целей.\n\n"
        
        prompt_lines = [intro, "Ресурсы для рекомендаций:\n"]
        
        if recommendations.get("courses"):
            prompt_lines.append("Курсы:\n")
            for c in recommendations["courses"]:
                prompt_lines.append(f"- {c['title']} ({c['url']})")
        
        if recommendations.get("articles"):
            prompt_lines.append("\nСтатьи:\n")
            for a in recommendations["articles"]:
                prompt_lines.append(f"- {a['title']} ({a['url']})")
        
        if recommendations.get("vacancies"):
            prompt_lines.append("\nВакансии:\n")
            for v in recommendations["vacancies"]:
                prompt_lines.append(f"- {v['title']} ({v['url']})")
        
        if recommendations.get("projects"):
            prompt_lines.append("\nOpen-source проекты:\n")
            for p in recommendations["projects"]:
                title = p['title']
                url = p['url']
                prompt_lines.append(f"- {title} ({url})")
        
        if recommendations.get("competitions"):
            prompt_lines.append("\nСоревнования:\n")
            for comp in recommendations["competitions"]:
                prompt_lines.append(f"- {comp['title']} ({comp['url']})")
        
        prompt_lines.append("\nТеперь составь итоговое сообщение для пользователя:")
        return "\n".join(prompt_lines)
    
    async def generate_final_message(self, user_profile: dict, all_recommendations: Dict[str, List[Dict]]) -> str:
        """
        Генерирует финальное сообщение с рекомендациями.
        
        Args:
            user_profile: Профиль пользователя
            all_recommendations: Все собранные рекомендации
            
        Returns:
            Финальное сообщение с рекомендациями
        """
        try:
            prompt = self.format_recommendations(user_profile, all_recommendations)
            result_text = await self.call_llm(prompt)
            return result_text
        except Exception as e:
            print(f"Предупреждение: Не удалось сгенерировать финальное сообщение через LLM: {e}")
            return self.format_fallback_recommendations(user_profile, all_recommendations)
    
    def format_fallback_recommendations(self, user_profile: dict, all_recommendations: Dict[str, List[Dict]]) -> str:
        """
        Формирует базовое сообщение с рекомендациями без использования LLM.
        
        Args:
            user_profile: Профиль пользователя
            all_recommendations: Все рекомендации
            
        Returns:
            Базовое сообщение с рекомендациями
        """
        goals = user_profile.get("goals", "развитие карьеры")
        missing_skills = user_profile.get("missing_skills", [])
        
        message = f"Основываясь на ваших целях ({goals}) и выявленных пробелах в навыках ({', '.join(missing_skills)}), "
        message += "рекомендую следующие ресурсы:\n\n"
        
        category_names = {
            "courses": "Курсы",
            "articles": "Статьи", 
            "vacancies": "Вакансии",
            "projects": "Проекты",
            "competitions": "Соревнования"
        }
        
        for category, items in all_recommendations.items():
            if items:
                message += f"{category_names.get(category, category)}:\n"
                for item in items[:3]:  # Показываем только топ-3
                    message += f"- {item['title']}: {item['url']}\n"
                message += "\n"
        
        return message
    
    async def analyze_conversation(self, json_path: str) -> str:
        """
        Анализирует диалог из JSON-файла и возвращает рекомендации.
        
        Args:
            json_path: Путь к JSON-файлу с диалогом
            
        Returns:
            Финальное рекомендательное сообщение
        """
        return await self.run_agent_async(json_path)
    
    async def analyze_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        Анализирует готовый список сообщений и возвращает рекомендации.
        
        Args:
            messages: Список сообщений в формате [{"role": "user", "message": "..."}]
            
        Returns:
            Финальное рекомендательное сообщение с курсами, статьями и т.д.
            
        Example:
            >>> messages = [
            ...     {"role": "user", "message": "Хочу стать Python разработчиком"},
            ...     {"role": "assistant", "message": "Расскажите о вашем опыте"},
            ...     {"role": "user", "message": "Изучаю Python 6 месяцев"}
            ... ]
            >>> recommendations = await agent.analyze_messages(messages)
            >>> print(recommendations)
        """
        # 1. Форматируем сообщения в текст диалога
        dialog_text = self.format_conversation(messages)
        
        # 2. Анализируем диалог и извлекаем профиль
        profile = await self.analyze_dialog(dialog_text)
        if not profile or "missing_skills" not in profile:
            raise ValueError("Не удалось извлечь профиль или недостающие навыки")
        
        missing_skills = profile["missing_skills"]
        
        # 3. Поиск ресурсов по недостающим навыкам
        resources_by_skill = {}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            tasks = [self.find_resources_for_skill(skill, session) for skill in missing_skills]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for skill, result in zip(missing_skills, results):
                if isinstance(result, Exception):
                    resources_by_skill[skill] = {
                        "courses": [], "articles": [], "vacancies": [], 
                        "projects": [], "competitions": []
                    }
                else:
                    resources_by_skill[skill] = result
        
        # 4. Объединение результатов по всем навыкам
        combined_recommendations = {
            "courses": [], "articles": [], "vacancies": [], 
            "projects": [], "competitions": []
        }
        
        for skill, res in resources_by_skill.items():
            for course in res.get("courses", []):
                course["skill"] = skill
                combined_recommendations["courses"].append(course)
            
            for article in res.get("articles", []):
                article["skill"] = skill
                combined_recommendations["articles"].append(article)
            
            for vac in res.get("vacancies", []):
                vac["skill"] = skill
                combined_recommendations["vacancies"].append(vac)
            
            for proj in res.get("projects", []):
                proj["skill"] = skill
                combined_recommendations["projects"].append(proj)
            
            for comp in res.get("competitions", []):
                comp["skill"] = skill
                combined_recommendations["competitions"].append(comp)

                
        
        # 5. Генерация финального сообщения
        final_message = await self.generate_final_message(profile, combined_recommendations)
        return final_message
    
    async def run_agent_async(self, json_path: str) -> str:
        """
        Основной метод для запуска полного пайплайна агента.
        
        Args:
            json_path: Путь к JSON-файлу с диалогом
            
        Returns:
            Финальное рекомендательное сообщение
            
        Raises:
            ValueError: Если не удалось извлечь профиль или недостающие навыки
        """
        #  Загрузка и форматирование диалога
        messages = await self.load_conversation(json_path)
        dialog_text = self.format_conversation(messages)
        
        #  Анализ диалога и извлечение профиля
        profile = await self.analyze_dialog(dialog_text)
        if not profile or "missing_skills" not in profile:
            raise ValueError("Не удалось извлечь профиль или недостающие навыки")
        
        missing_skills = profile["missing_skills"]
        
        # поиск недостающих навыков
        resources_by_skill = {}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            tasks = [self.find_resources_for_skill(skill, session) for skill in missing_skills]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for skill, result in zip(missing_skills, results):
                if isinstance(result, Exception):
                    resources_by_skill[skill] = {
                        "courses": [], "articles": [], "vacancies": [], 
                        "projects": [], "competitions": []
                    }
                else:
                    resources_by_skill[skill] = result
        
        # 4. Объединение результатов по всем навыкам
        combined_recommendations = {
            "courses": [], "articles": [], "vacancies": [], 
            "projects": [], "competitions": []
        }
        
        for skill, res in resources_by_skill.items():
            for course in res.get("courses", []):
                course["skill"] = skill
                combined_recommendations["courses"].append(course)
            
            for article in res.get("articles", []):
                article["skill"] = skill
                combined_recommendations["articles"].append(article)
            
            for vac in res.get("vacancies", []):
                vac["skill"] = skill
                combined_recommendations["vacancies"].append(vac)
            
            for proj in res.get("projects", []):
                proj["skill"] = skill
                combined_recommendations["projects"].append(proj)
            
            for comp in res.get("competitions", []):
                comp["skill"] = skill
                combined_recommendations["competitions"].append(comp)
        
        # 5. Генерация финального сообщения
        final_message = await self.generate_final_message(profile, combined_recommendations)
        return final_message


# Функции для обратной совместимости
async def run_agent_async(json_path: str, api_key: Optional[str] = None) -> str:
    """
    Функция для запуска агента (обратная совместимость).
    
    Args:
        json_path: Путь к JSON-файлу с диалогом
        
        
    Returns:
        Финальное рекомендательное сообщение
    """
    agent = CareerAgent(api_key)
    return await agent.run_agent_async(json_path)


async def load_conversation(json_path: str) -> List[Dict]:
    """Функция для загрузки диалога (обратная совместимость)."""
    agent = CareerAgent()
    return await agent.load_conversation(json_path)


def format_conversation(messages: List[Dict]) -> str:
    """Функция для форматирования диалога (обратная совместимость)."""
    agent = CareerAgent()
    return agent.format_conversation(messages)


async def analyze_dialog(dialog_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Функция для анализа диалога (обратная совместимость)."""
    agent = CareerAgent(api_key)
    return await agent.analyze_dialog(dialog_text)


async def find_resources_for_skill(skill: str, session: aiohttp.ClientSession) -> Dict[str, List[Dict]]:
    """Функция для поиска ресурсов (обратная совместимость)."""
    agent = CareerAgent()
    return await agent.find_resources_for_skill(skill, session)


async def generate_final_message(user_profile: dict, all_recommendations: Dict[str, List[Dict]], api_key: Optional[str] = None) -> str:
    """Функция для генерации финального сообщения (обратная совместимость)."""
    agent = CareerAgent(api_key)
    return await agent.generate_final_message(user_profile, all_recommendations)
