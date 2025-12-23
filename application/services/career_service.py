"""
Сервис карьерного консультирования (Application Service)
Объединяет бизнес-логику и работу с репозиториями
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from domain.entities import UserProfile, Resource, Conversation, ResourceType
from domain.repositories import (
    IUserProfileRepository,
    IResourceRepository,
    IConversationRepository,
    IVacancyRepository
)
from infrastructure.llm.llm_service import LLMService
from infrastructure.searcher.web_searcher import WebSearcher

logger = logging.getLogger(__name__)


class CareerService:
    """Сервис карьерного консультирования"""
    
    def __init__(
        self,
        user_profile_repo: IUserProfileRepository,
        resource_repo: IResourceRepository,
        conversation_repo: IConversationRepository,
        vacancy_repo: IVacancyRepository,
        llm_service: LLMService,
        web_searcher: Optional[WebSearcher] = None
    ):
        """
        Инициализация сервиса
        
        Args:
            user_profile_repo: Репозиторий профилей пользователей
            resource_repo: Репозиторий ресурсов
            conversation_repo: Репозиторий диалогов
            vacancy_repo: Репозиторий вакансий
            llm_service: Сервис для работы с LLM
            web_searcher: Сервис для поиска ресурсов в интернете (опционально)
        """
        self.user_profile_repo = user_profile_repo
        self.resource_repo = resource_repo
        self.conversation_repo = conversation_repo
        self.vacancy_repo = vacancy_repo
        self.llm_service = llm_service
        self.web_searcher = web_searcher
    
    async def analyze_conversation(self, messages: List[Dict[str, str]], user_id: str) -> Dict[str, Any]:
        """
        Анализирует диалог и возвращает рекомендации
        
        Args:
            messages: Список сообщений диалога
            user_id: ID пользователя
            
        Returns:
            Словарь с рекомендациями и профилем пользователя
        """
        # Сохраняем диалог
        conversation = Conversation(
            user_id=user_id,
            messages=messages
        )
        conversation_id = await self.conversation_repo.save(conversation)
        
        # Форматируем диалог в текст
        dialog_text = self._format_conversation(messages)
        
        # Анализируем диалог с помощью LLM
        profile_data = await self.llm_service.analyze_dialog(dialog_text)
        
        # Создаем профиль пользователя
        user_profile = UserProfile(
            user_id=user_id,
            goals=profile_data.get("goals", ""),
            skills=profile_data.get("skills", []),
            experience=profile_data.get("experience", ""),
            challenges=profile_data.get("challenges", ""),
            missing_skills=profile_data.get("missing_skills", [])
        )
        
        # Сохраняем профиль
        await self.user_profile_repo.save(user_profile)
        
        # Ищем ресурсы для недостающих навыков
        resources = await self._find_resources_for_skills(user_profile.missing_skills)
        
        # Генерируем финальные рекомендации
        recommendations = await self.llm_service.generate_recommendations(
            user_profile=user_profile,
            resources=resources
        )
        
        return {
            "conversation_id": conversation_id,
            "profile": user_profile.to_dict(),
            "resources": {k: [r.to_dict() for r in v] for k, v in resources.items()},
            "recommendations": recommendations
        }
    
    async def get_user_profile(self, dialog_text: str, user_id: str) -> Dict[str, Any]:
        """
        Извлекает профиль пользователя из диалога
        
        Args:
            dialog_text: Текст диалога
            user_id: ID пользователя
            
        Returns:
            Профиль пользователя
        """
        # Анализируем диалог
        profile_data = await self.llm_service.analyze_dialog(dialog_text)
        
        # Создаем профиль
        user_profile = UserProfile(
            user_id=user_id,
            goals=profile_data.get("goals", ""),
            skills=profile_data.get("skills", []),
            experience=profile_data.get("experience", ""),
            challenges=profile_data.get("challenges", ""),
            missing_skills=profile_data.get("missing_skills", [])
        )
        
        # Сохраняем профиль
        await self.user_profile_repo.save(user_profile)
        
        return user_profile.to_dict()
    
    async def find_resources_for_skills(self, skills: List[str]) -> Dict[str, List[Dict]]:
        """
        Ищет ресурсы для указанных навыков
        
        Args:
            skills: Список навыков
            
        Returns:
            Ресурсы по категориям
        """
        resources = await self._find_resources_for_skills(skills)
        return {k: [r.to_dict() for r in v] for k, v in resources.items()}
    
    async def match_vacancy(
        self,
        user_profile: Dict[str, Any],
        vacancy_info: str
    ) -> Dict[str, Any]:
        """
        Анализирует соответствие пользователя вакансии
        
        Args:
            user_profile: Профиль пользователя
            vacancy_info: Информация о вакансии
            
        Returns:
            Результат анализа соответствия
        """
        # Создаем объект профиля
        profile = UserProfile.from_dict(user_profile)
        
        # Анализируем соответствие с помощью LLM
        match_result = await self.llm_service.match_vacancy(profile, vacancy_info)
        
        return match_result
    
    async def get_career_advice(
        self,
        goals: str,
        skills: List[str],
        challenges: str = ""
    ) -> str:
        """
        Получает карьерные советы
        
        Args:
            goals: Цели пользователя
            skills: Текущие навыки
            challenges: Проблемы/вызовы
            
        Returns:
            Текст с карьерными советами
        """
        return await self.llm_service.get_career_advice(goals, skills, challenges)
    
    async def _find_resources_for_skills(
        self,
        skills: List[str]
    ) -> Dict[str, List[Resource]]:
        """Внутренний метод для поиска ресурсов"""
        resources_by_category = {
            "courses": [],
            "articles": [],
            "vacancies": [],
            "projects": [],
            "competitions": []
        }
        
        for skill in skills:
            # Сначала ищем в векторном хранилище
            courses = await self.resource_repo.search_by_skill(
                skill,
                resource_type=ResourceType.COURSE.value,
                limit=5
            )
            articles = await self.resource_repo.search_by_skill(
                skill,
                resource_type=ResourceType.ARTICLE.value,
                limit=5
            )
            projects = await self.resource_repo.search_by_skill(
                skill,
                resource_type=ResourceType.PROJECT.value,
                limit=5
            )
            competitions = await self.resource_repo.search_by_skill(
                skill,
                resource_type=ResourceType.COMPETITION.value,
                limit=5
            )
            
            # Если ресурсов мало, ищем в интернете
            if len(courses) + len(articles) + len(projects) + len(competitions) < 5 and self.web_searcher:
                try:
                    web_resources = await self.web_searcher.find_resources_for_skill(skill)
                    courses.extend(web_resources.get("courses", []))
                    articles.extend(web_resources.get("articles", []))
                    projects.extend(web_resources.get("projects", []))
                    competitions.extend(web_resources.get("competitions", []))
                except Exception as e:
                    logger.warning(f"Ошибка поиска ресурсов в интернете для {skill}: {e}")
            
            resources_by_category["courses"].extend(courses)
            resources_by_category["articles"].extend(articles)
            resources_by_category["projects"].extend(projects)
            resources_by_category["competitions"].extend(competitions)
        
        # Удаляем дубликаты
        seen_urls = set()
        for category in resources_by_category:
            unique_resources = []
            for resource in resources_by_category[category]:
                if resource.url and resource.url not in seen_urls:
                    seen_urls.add(resource.url)
                    unique_resources.append(resource)
            resources_by_category[category] = unique_resources[:10]  # Ограничиваем до 10
        
        return resources_by_category
    
    def _format_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Форматирует список сообщений в текст диалога"""
        formatted_lines = []
        for msg in messages:
            role = msg.get("role", "unknown").lower()
            content = msg.get("message", "") or msg.get("content", "")
            
            if role == "user":
                formatted_lines.append(f"Пользователь: {content}")
            elif role in ("assistant", "ai"):
                formatted_lines.append(f"Консультант: {content}")
            else:
                formatted_lines.append(f"{role.capitalize()}: {content}")
        
        return "\n".join(formatted_lines)

