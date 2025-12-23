
import asyncio
import json
from typing import Dict, List, Any, Optional, Union
from .career_agent import CareerAgent
from .prepare_profile import get_text_profile


class CareerAdvisorInterface:
    """
    Единый интерфейс для работы с карьерным агентом.
    Предоставляет методы для различных сценариев использования.
    """
    
    def __init__(self, api_key: str):
        """
        Инициализация интерфейса.
        
        Args:
            api_key: API ключ для OpenAI-совместимого сервиса
        """
        self.career_agent = CareerAgent(api_key)
    
    async def process_conversation_file(self, json_path: str) -> str:
        """
        Обрабатывает диалог из JSON-файла и возвращает рекомендации.
        
        Args:
            json_path: Путь к JSON-файлу с диалогом
            
        Returns:
            Финальное рекомендательное сообщение
            
        Example:
            >>> interface = CareerAdvisorInterface("your-api-key")
            >>> recommendations = await interface.process_conversation_file("conversation.json")
            >>> print(recommendations)
        """
        return await self.career_agent.analyze_conversation(json_path)
    
    async def process_conversation_data(self, messages: List[Dict]) -> str:
        """
        Обрабатывает диалог из списка сообщений и возвращает рекомендации.
        
        Args:
            messages: Список сообщений с полями 'role' и 'message'
            
        Returns:
            Финальное рекомендательное сообщение с курсами, статьями и т.д.
            
        Example:
            >>> messages = [
            ...     {"role": "user", "message": "Хочу стать Python разработчиком"},
            ...     {"role": "assistant", "message": "Расскажите о вашем опыте"},
            ...     {"role": "user", "message": "Изучаю Python 6 месяцев"}
            ... ]
            >>> recommendations = await interface.process_conversation_data(messages)
            >>> print(recommendations)
        """
        return await self.career_agent.analyze_messages(messages)
    
    async def get_user_profile(self, dialog_text: str) -> Dict[str, Any]:
        """
        Извлекает профиль пользователя из текста диалога.
        
        Args:
            dialog_text: Текст диалога для анализа
            
        Returns:
            Словарь с профилем: goals, skills, experience, challenges, missing_skills
            
        Example:
            >>> dialog = "Пользователь: Хочу стать Python разработчиком\\nКонсультант: Расскажите о вашем опыте"
            >>> profile = await interface.get_user_profile(dialog)
            >>> print(profile["missing_skills"])
        """
        return await self.career_agent.get_user_profile(dialog_text)
    
    async def find_resources_for_skills(self, skills: List[str]) -> Dict[str, List[Dict]]:
        """
        Ищет карьерные ресурсы для указанных навыков.
        
        Args:
            skills: Список навыков для поиска ресурсов
            
        Returns:
            Словарь с ресурсами по категориям: courses, articles, vacancies, projects, competitions
            
        Example:
            >>> skills = ["Python", "Machine Learning", "Data Science"]
            >>> resources = await interface.find_resources_for_skills(skills)
            >>> print(f"Найдено курсов: {len(resources['courses'])}")
        """
        return await self.career_agent.find_career_resources(skills)
    
    async def get_simple_response(self, json_history: str) -> str:
        """
        Получает простой ответ от LLM на основе истории сообщений.
        
        Args:
            json_history: JSON-строка с историей сообщений
            
        Returns:
            Ответ модели в виде строки
            
        Example:
            >>> history = json.dumps([
            ...     {"role": "user", "content": "Привет"},
            ...     {"role": "assistant", "content": "Привет! Как дела?"}
            ... ])
            >>> response = await interface.get_simple_response(history)
        """
        return await self.career_agent.get_response(json_history)
    
    async def match_user_to_vacancy(self, user_profile: Dict, vacancy_info: str) -> Dict[str, Any]:
        """
        Анализирует соответствие пользователя вакансии.
        
        Args:
            user_profile: Профиль пользователя
            vacancy_info: Информация о вакансии
            
        Returns:
            Словарь с результатами анализа: score, decision, reasoning_report
            
        Example:
            >>> profile = {"skills": ["Python"], "experience": "2 года"}
            >>> vacancy = "Требуется Python разработчик с опытом 3+ года"
            >>> match = await interface.match_user_to_vacancy(profile, vacancy)
            >>> print(f"Оценка соответствия: {match['score']}/100")
        """
        from .prompts import user_matching_prompt, system_user_matching_prompt
        
        profile_text = get_text_profile(user_profile)
        prompt = user_matching_prompt.format(profile=profile_text, vacancy=vacancy_info)
        
        messages = [
            {"role": "system", "content": system_user_matching_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.get_simple_response(json.dumps(messages))
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {
                "score": 0,
                "decision": "Не удалось проанализировать",
                "reasoning_report": "Ошибка при парсинге ответа модели"
            }
    
    async def get_career_advice(self, user_goals: str, current_skills: List[str], 
                              challenges: str = "") -> str:
        """
        Получает карьерные советы на основе целей и навыков пользователя.
        
        Args:
            user_goals: Цели пользователя в карьере
            current_skills: Текущие навыки пользователя
            challenges: Текущие проблемы/вызовы (опционально)
            
        Returns:
            Текст с карьерными советами
            
        Example:
            >>> goals = "Стать senior Python разработчиком"
            >>> skills = ["Python", "Django", "PostgreSQL"]
            >>> advice = await interface.get_career_advice(goals, skills)
        """
        prompt = f"""
        Пользователь имеет следующие цели в карьере: {user_goals}
        Текущие навыки: {', '.join(current_skills)}
        Текущие проблемы: {challenges if challenges else "Не указаны"}
        
        Предоставь персональные карьерные советы:
        1. Какие навыки стоит развивать в первую очередь
        2. Конкретные шаги для достижения целей
        3. Рекомендации по преодолению текущих проблем
        4. План развития на ближайшие 6-12 месяцев
        """
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        return await self.get_simple_response(json.dumps(messages))


# Функции для быстрого доступа (без создания экземпляра класса)
async def quick_analyze_conversation(json_path: str, api_key: str) -> str:
    """
    Быстрый анализ диалога из JSON-файла.
    
    Args:
        json_path: Путь к JSON-файлу с диалогом
        api_key: API ключ
        
    Returns:
        Финальное рекомендательное сообщение
    """
    interface = CareerAdvisorInterface(api_key)
    return await interface.process_conversation_file(json_path)


async def quick_get_profile(dialog_text: str, api_key: str) -> Dict[str, Any]:
    """
    Быстрое извлечение профиля пользователя из диалога.
    
    Args:
        dialog_text: Текст диалога
        api_key: API ключ
        
    Returns:
        Профиль пользователя
    """
    interface = CareerAdvisorInterface(api_key)
    return await interface.get_user_profile(dialog_text)


async def quick_find_resources(skills: List[str], api_key: str) -> Dict[str, List[Dict]]:
    """
    Быстрый поиск ресурсов для навыков.
    
    Args:
        skills: Список навыков
        api_key: API ключ
        
    Returns:
        Ресурсы по категориям
    """
    interface = CareerAdvisorInterface(api_key)
    return await interface.find_resources_for_skills(skills)


async def quick_analyze_messages(messages: List[Dict[str, str]], api_key: str) -> str:
    """
    Быстрый анализ готового списка сообщений.
    
    Args:
        messages: Список сообщений в формате [{"role": "user", "message": "..."}]
        api_key: API ключ
        
    Returns:
        Финальное рекомендательное сообщение с курсами, статьями и т.д.
        
    Example:
        >>> messages = [
        ...     {"role": "user", "message": "Хочу стать Python разработчиком"},
        ...     {"role": "assistant", "message": "Расскажите о вашем опыте"},
        ...     {"role": "user", "message": "Изучаю Python 6 месяцев"}
        ... ]
        >>> recommendations = await quick_analyze_messages(messages, "your-api-key")
        >>> print(recommendations)
    """
    interface = CareerAdvisorInterface(api_key)
    return await interface.process_conversation_data(messages)


# Пример использования
async def example_usage():
    """Пример использования интерфейса."""
    api_key = "your-api-key-here"
    interface = CareerAdvisorInterface(api_key)
    
    # Пример 1: Анализ диалога из файла
    try:
        recommendations = await interface.process_conversation_file("conversation.json")
        print("Рекомендации:", recommendations)
    except FileNotFoundError:
        print("Файл conversation.json не найден")
    
    # Пример 2: Анализ диалога из данных
    messages = [
        {"role": "user", "message": "Хочу стать Python разработчиком"},
        {"role": "assistant", "message": "Расскажите о вашем текущем опыте программирования"},
        {"role": "user", "message": "Изучаю Python 6 месяцев, знаю основы"}
    ]
    
    recommendations = await interface.process_conversation_data(messages)
    print("Рекомендации из данных:", recommendations)
    
    # Пример 3: Поиск ресурсов для навыков
    skills = ["Python", "Machine Learning", "Data Analysis"]
    resources = await interface.find_resources_for_skills(skills)
    print(f"Найдено курсов: {len(resources['courses'])}")
    print(f"Найдено статей: {len(resources['articles'])}")
    
    # Пример 4: Соответствие вакансии
    profile = {
        "skills": ["Python", "Django", "PostgreSQL"],
        "experience": "2 года разработки",
        "education": "Высшее техническое"
    }
    vacancy = "Требуется Python разработчик с опытом 3+ года, знание Django, PostgreSQL"
    
    match = await interface.match_user_to_vacancy(profile, vacancy)
    print(f"Оценка соответствия: {match['score']}/100")
    print(f"Решение: {match['decision']}")


if __name__ == "__main__":
    # Запуск примера
    asyncio.run(example_usage())
