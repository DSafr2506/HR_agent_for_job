#!/usr/bin/env python3
"""
Тестовый клиент для проверки Career Advisor API
Показывает, как frontend должен взаимодействовать с API
"""

import requests
import json
import asyncio
from typing import Dict, List, Any

class CareerAdvisorAPIClient:
    """Клиент для работы с Career Advisor API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка работоспособности API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Анализ диалога
        
        Args:
            messages: Список сообщений [{"role": "user", "message": "..."}]
        """
        try:
            response = self.session.post(
                f"{self.base_url}/api/analyze-conversation",
                json={"messages": messages}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_user_profile(self, dialog_text: str) -> Dict[str, Any]:
        """Извлечение профиля пользователя"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/get-user-profile",
                json={"dialog_text": dialog_text}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def find_resources(self, skills: List[str]) -> Dict[str, Any]:
        """Поиск ресурсов для навыков"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/find-resources",
                json={"skills": skills}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def match_vacancy(self, user_profile: Dict[str, Any], vacancy_info: str) -> Dict[str, Any]:
        """Анализ соответствия вакансии"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/match-vacancy",
                json={
                    "user_profile": user_profile,
                    "vacancy_info": vacancy_info
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_career_advice(self, goals: str, skills: List[str], challenges: str = "") -> Dict[str, Any]:
        """Получение карьерных советов"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/career-advice",
                json={
                    "user_goals": goals,
                    "current_skills": skills,
                    "challenges": challenges
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def test_api():
    """Тестирование всех endpoints API"""
    print(" Тестирование Career Advisor API\n")
    
    client = CareerAdvisorAPIClient()
    
    # 1. Проверка здоровья API
    print("1. Проверка работоспособности API...")
    health = client.health_check()
    if "error" in health:
        print(f" API недоступен: {health['error']}")
        print("Убедитесь, что сервер запущен: python example_api_server.py")
        return
    else:
        print(f" API работает: {health['status']}")
    
    # 2. Тест анализа диалога
    print("\n2. Тест анализа диалога...")
    test_messages = [
        {"role": "user", "message": "Хочу стать Python разработчиком"},
        {"role": "assistant", "message": "Расскажите о вашем текущем опыте программирования"},
        {"role": "user", "message": "Изучаю Python 6 месяцев, знаю основы"}
    ]
    
    result = client.analyze_conversation(test_messages)
    if "error" in result:
        print(f" Ошибка анализа диалога: {result['error']}")
    else:
        print(" Анализ диалога успешен")
        print(f"Рекомендации: {result['recommendations'][:100]}...")
    
    # 3. Тест извлечения профиля
    print("\n3. Тест извлечения профиля...")
    test_dialog = """
    Пользователь: Хочу стать Python разработчиком
    Консультант: Расскажите о вашем опыте
    Пользователь: Изучаю Python 6 месяцев, знаю основы
    """
    
    profile_result = client.get_user_profile(test_dialog)
    if "error" in profile_result:
        print(f" Ошибка извлечения профиля: {profile_result['error']}")
    else:
        print(" Профиль извлечен успешно")
        profile = profile_result['profile']
        print(f"Цели: {profile.get('goals', 'Не указаны')}")
        print(f"Недостающие навыки: {profile.get('missing_skills', [])}")
    
    # 4. Тест поиска ресурсов
    print("\n4. Тест поиска ресурсов...")
    test_skills = ["Python", "Django"]
    
    resources_result = client.find_resources(test_skills)
    if "error" in resources_result:
        print(f" Ошибка поиска ресурсов: {resources_result['error']}")
    else:
        print(" Поиск ресурсов успешен")
        resources = resources_result['resources']
        print(f"Найдено курсов: {len(resources.get('courses', []))}")
        print(f"Найдено статей: {len(resources.get('articles', []))}")
        print(f"Найдено вакансий: {len(resources.get('vacancies', []))}")
    
    # 5. Тест соответствия вакансии
    print("\n5. Тест соответствия вакансии...")
    test_profile = {
        "skills": ["Python", "Django"],
        "experience": "2 года разработки",
        "education": "Высшее техническое"
    }
    test_vacancy = "Требуется Python разработчик с опытом 3+ года, знание Django, PostgreSQL"
    
    match_result = client.match_vacancy(test_profile, test_vacancy)
    if "error" in match_result:
        print(f" Ошибка анализа соответствия: {match_result['error']}")
    else:
        print(" Анализ соответствия успешен")
        match = match_result['match']
        print(f"Оценка: {match.get('score', 0)}/100")
        print(f"Решение: {match.get('decision', 'Не определено')}")
    
    # 6. Тест карьерных советов
    print("\n6. Тест карьерных советов...")
    advice_result = client.get_career_advice(
        goals="Стать senior Python разработчиком",
        skills=["Python", "Django"],
        challenges="Недостаток опыта в тестировании"
    )
    
    if "error" in advice_result:
        print(f" Ошибка генерации советов: {advice_result['error']}")
    else:
        print(" Карьерные советы сгенерированы")
        print(f"Советы: {advice_result['advice'][:100]}...")
    
    print("\n Тестирование завершено!")

def example_frontend_usage():
    """Пример использования API из frontend (JavaScript)"""
    print("\n Пример использования из frontend (JavaScript):")
    
    js_code = '''
// Анализ диалога
const analyzeConversation = async (messages) => {
    const response = await fetch('/api/analyze-conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ messages })
    });
    
    const result = await response.json();
    return result;
};

// Поиск ресурсов
const findResources = async (skills) => {
    const response = await fetch('/api/find-resources', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ skills })
    });
    
    const result = await response.json();
    return result;
};

// Использование
const messages = [
    { role: "user", message: "Хочу стать Python разработчиком" },
    { role: "assistant", message: "Расскажите о вашем опыте" }
];

analyzeConversation(messages)
    .then(result => {
        console.log('Рекомендации:', result.recommendations);
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
'''
    
    print(js_code)

if __name__ == "__main__":
    test_api()
    example_frontend_usage()
