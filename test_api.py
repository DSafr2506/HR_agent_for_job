#!/usr/bin/env python3
"""
Тестовый скрипт для проверки настройки API ключей CareerAgent
"""

import os
import asyncio
from career_advisor_agent import CareerAgent

def check_environment():
    """Проверяет настройку переменных окружения"""
    print("🔍 Проверка переменных окружения...")
    
    scibox_key = os.getenv("SCIBOX_API_KEY")
    scibox_url = os.getenv("SCIBOX_API_URL", "https://llm.t1v.scibox.tech/v1")
    scibox_model = os.getenv("SCIBOX_MODEL", "Qwen2.5-72B-Instruct-AWQ")
    github_token = os.getenv("GITHUB_TOKEN")
    
    print(f"  SCIBOX_API_KEY: {' Настроен' if scibox_key else ' Не настроен'}")
    print(f"  SCIBOX_API_URL: {scibox_url}")
    print(f"  SCIBOX_MODEL: {scibox_model}")
    print(f"  GITHUB_TOKEN: {' Настроен' if github_token else ' Не настроен (опционально)'}")
    
    return scibox_key is not None

async def test_agent_initialization():
    """Тестирует инициализацию агента"""
    print("\n🤖 Тестирование инициализации CareerAgent...")
    
    try:
        # Попытка создать агента с переменной окружения
        agent = CareerAgent()
        print(" CareerAgent успешно инициализирован с переменной окружения!")
        return True
    except Exception as e:
        print(f" Ошибка инициализации: {e}")
        return False

async def test_simple_llm_call():
    """Тестирует простой вызов LLM"""
    print("\n Тестирование вызова LLM...")
    
    try:
        agent = CareerAgent()
        
        # Простой тестовый запрос
        test_messages = [
            {"role": "user", "content": "Привет! Как дела?"}
        ]
        
        import json
        response = await agent.get_response(json.dumps(test_messages))
        print(" LLM успешно ответил!")
        print(f"Ответ: {response[:100]}...")
        return True
        
    except Exception as e:
        print(f" Ошибка вызова LLM: {e}")
        return False

async def test_dialog_analysis():
    """Тестирует анализ диалога"""
    print("\n Тестирование анализа диалога...")
    
    try:
        agent = CareerAgent()
        
        # Тестовый диалог
        test_dialog = """
        Пользователь: Хочу стать Python разработчиком
        Консультант: Расскажите о вашем текущем опыте программирования
        Пользователь: Изучаю Python 6 месяцев, знаю основы
        """
        
        profile = await agent.analyze_dialog(test_dialog)
        print(" Анализ диалога успешен!")
        print(f"Извлеченные навыки: {profile.get('missing_skills', [])}")
        return True
        
    except Exception as e:
        print(f" Ошибка анализа диалога: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print(" Тестирование CareerAgent API\n")
    
    # Проверка окружения
    env_ok = check_environment()
    
    if not env_ok:
        print("\n Проблема с настройкой API ключей!")
        print("\n Как исправить:")
        print("1. Установите переменную окружения:")
        print("   export SCIBOX_API_KEY='ваш-ключ-от-scibox'")
        print("2. Или передайте ключ напрямую:")
        print("   agent = CareerAgent('ваш-ключ-от-scibox')")
        return
    
    # Тестирование инициализации
    init_ok = await test_agent_initialization()
    if not init_ok:
        return
    
    # Тестирование LLM
    llm_ok = await test_simple_llm_call()
    if not llm_ok:
        return
    
    # Тестирование анализа
    analysis_ok = await test_dialog_analysis()
    
    # Итоговый результат
    print("\n" + "="*50)
    if env_ok and init_ok and llm_ok and analysis_ok:
        print(" Все тесты пройдены! CareerAgent готов к работе!")
    else:
        print(" Некоторые тесты не пройдены. Проверьте настройки API.")

if __name__ == "__main__":
    asyncio.run(main())
