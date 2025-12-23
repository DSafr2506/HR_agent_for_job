"""
Сервис для работы с LLM (Strategy Pattern)
"""
import logging
import json
from typing import Dict, List, Any
from openai import AsyncOpenAI
from config.settings import get_settings
from domain.entities import UserProfile, Resource

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для работы с LLM"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """
        Инициализация сервиса LLM
        
        Args:
            api_key: API ключ
            base_url: Базовый URL API
            model: Название модели
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.scibox_api_key
        self.base_url = base_url or settings.scibox_api_url
        self.model = model or settings.scibox_model
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        logger.info(f"LLM сервис инициализирован: {self.model}")
    
    async def call_llm(self, prompt: str, system_prompt: str = None, temperature: float = 0.1) -> str:
        """
        Вызов LLM модели
        
        Args:
            prompt: Промпт пользователя
            system_prompt: Системный промпт (опционально)
            temperature: Температура генерации
            
        Returns:
            Ответ модели
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка при вызове LLM: {e}")
            raise RuntimeError(f"Ошибка при вызове LLM: {e}")
    
    async def analyze_dialog(self, dialog_text: str) -> Dict[str, Any]:
        """
        Анализирует диалог и извлекает профиль пользователя
        
        Args:
            dialog_text: Текст диалога
            
        Returns:
            Словарь с данными профиля
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
            return analysis
        except json.JSONDecodeError as e:
            logger.warning(f"Не удалось распарсить ответ LLM как JSON: {e}")
            return {
                "goals": "Не удалось извлечь цели",
                "skills": [],
                "experience": "Не удалось извлечь опыт",
                "challenges": "Не удалось извлечь проблемы",
                "missing_skills": []
            }
    
    async def generate_recommendations(
        self,
        user_profile: UserProfile,
        resources: Dict[str, List[Resource]]
    ) -> str:
        """
        Генерирует финальные рекомендации
        
        Args:
            user_profile: Профиль пользователя
            resources: Ресурсы по категориям
            
        Returns:
            Текст с рекомендациями
        """
        prompt = self._format_recommendations_prompt(user_profile, resources)
        
        try:
            return await self.call_llm(prompt)
        except Exception as e:
            logger.error(f"Ошибка генерации рекомендаций: {e}")
            return self._format_fallback_recommendations(user_profile, resources)
    
    async def match_vacancy(
        self,
        user_profile: UserProfile,
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
        profile_text = self._profile_to_text(user_profile)
        
        prompt = f"""
        **ПРОФИЛЬ КАНДИДАТА:**
        {profile_text}
        
        **ИНФОРМАЦИЯ О ВАКАНСИИ:**
        {vacancy_info}
        
        Проанализируй соответствие профиля кандидата требованиям вакансии.
        Дай оценку от 0 до 100 (score), прими решение о соответствии (decision: "подходит"/"не подходит"/"частично подходит"),
        и составь развернутый отчет (reasoning_report).
        
        Ответ должен быть в формате JSON с полями: score, decision, reasoning_report.
        """
        
        system_prompt = """Ты — карьерный помощник, который анализирует соответствие между профилем пользователя и вакансией.
        Используй поддерживающий, мотивационный тон. Акцент на развитии и улучшении навыков."""
        
        try:
            result_text = await self.call_llm(prompt, system_prompt=system_prompt)
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {
                "score": 0,
                "decision": "Не удалось проанализировать",
                "reasoning_report": "Ошибка при парсинге ответа модели"
            }
    
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
        prompt = f"""
        Пользователь имеет следующие цели в карьере: {goals}
        Текущие навыки: {', '.join(skills)}
        Текущие проблемы: {challenges if challenges else "Не указаны"}
        
        Предоставь персональные карьерные советы:
        1. Какие навыки стоит развивать в первую очередь
        2. Конкретные шаги для достижения целей
        3. Рекомендации по преодолению текущих проблем
        4. План развития на ближайшие 6-12 месяцев
        """
        
        return await self.call_llm(prompt)
    
    def _format_recommendations_prompt(
        self,
        user_profile: UserProfile,
        resources: Dict[str, List[Resource]]
    ) -> str:
        """Форматирует промпт для генерации рекомендаций"""
        intro = (
            f"Пользователь стремится: {user_profile.goals}.\n"
            f"Текущие трудности: {user_profile.challenges}.\n"
            f"Выявленные пробелы в навыках: {', '.join(user_profile.missing_skills)}.\n\n"
        )
        
        intro += (
            "На основании этого, сгенерируй персональные рекомендации для пользователя. "
            "Представь их структурировано по категориям (курсы, статьи, вакансии, проекты, соревнования) "
            "и поясни, как каждый пункт поможет закрыть пробелы и достичь целей.\n\n"
        )
        
        prompt_lines = [intro, "Ресурсы для рекомендаций:\n"]
        
        category_names = {
            "courses": "Курсы",
            "articles": "Статьи",
            "vacancies": "Вакансии",
            "projects": "Проекты",
            "competitions": "Соревнования"
        }
        
        for category, items in resources.items():
            if items:
                prompt_lines.append(f"\n{category_names.get(category, category)}:\n")
                for item in items[:10]:
                    prompt_lines.append(f"- {item.title} ({item.url})")
                    if item.description:
                        prompt_lines.append(f"  {item.description}")
        
        prompt_lines.append("\nТеперь составь итоговое сообщение для пользователя:")
        return "\n".join(prompt_lines)
    
    def _format_fallback_recommendations(
        self,
        user_profile: UserProfile,
        resources: Dict[str, List[Resource]]
    ) -> str:
        """Форматирует базовые рекомендации без LLM"""
        message = (
            f"Основываясь на ваших целях ({user_profile.goals}) и выявленных пробелах в навыках "
            f"({', '.join(user_profile.missing_skills)}), рекомендую следующие ресурсы:\n\n"
        )
        
        category_names = {
            "courses": "Курсы",
            "articles": "Статьи",
            "vacancies": "Вакансии",
            "projects": "Проекты",
            "competitions": "Соревнования"
        }
        
        for category, items in resources.items():
            if items:
                message += f"{category_names.get(category, category)}:\n"
                for item in items[:5]:
                    message += f"- {item.title}: {item.url}\n"
                message += "\n"
        
        return message
    
    def _profile_to_text(self, profile: UserProfile) -> str:
        """Преобразует профиль в текст"""
        parts = [
            f"Цели: {profile.goals}",
            f"Навыки: {', '.join(profile.skills)}",
            f"Опыт: {profile.experience}",
            f"Проблемы: {profile.challenges}",
            f"Недостающие навыки: {', '.join(profile.missing_skills)}"
        ]
        return "\n".join(parts)

