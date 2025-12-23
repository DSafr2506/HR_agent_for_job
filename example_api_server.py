#!/usr/bin/env python3
"""
Пример API сервера для интеграции карьерного агента
Backend разработчик может использовать этот код как основу
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import os
import logging
from datetime import datetime

# Импорт вашего карьерного агента
from career_advisor_agent import CareerAdvisorInterface

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Career Advisor API",
    description="API для карьерного агента",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация карьерного агента
try:
    api_key = os.getenv("SCIBOX_API_KEY")
    if not api_key:
        raise ValueError("SCIBOX_API_KEY не найден в переменных окружения")
    
    career_interface = CareerAdvisorInterface(api_key)
    logger.info("Career Advisor успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка инициализации Career Advisor: {e}")
    career_interface = None

# Модели данных для API
class ConversationMessage(BaseModel):
    role: str  # "user" или "assistant"
    message: str

class ConversationRequest(BaseModel):
    messages: List[ConversationMessage]

class SkillsRequest(BaseModel):
    skills: List[str]

class ProfileRequest(BaseModel):
    dialog_text: str

class VacancyMatchRequest(BaseModel):
    user_profile: Dict[str, Any]
    vacancy_info: str

class CareerAdviceRequest(BaseModel):
    user_goals: str
    current_skills: List[str]
    challenges: str = ""

# API Endpoints

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Career Advisor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "service": "Career Advisor API",
        "timestamp": datetime.now().isoformat(),
        "agent_initialized": career_interface is not None
    }

@app.post("/api/analyze-conversation")
async def analyze_conversation(request: ConversationRequest):
    """
    Анализирует диалог и возвращает рекомендации
    
    Args:
        request: Запрос с сообщениями диалога
        
    Returns:
        Рекомендации на основе анализа диалога
    """
    if not career_interface:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    
    try:
        start_time = datetime.now()
        logger.info(f"Начало анализа диалога: {len(request.messages)} сообщений")
        
        # Преобразуем в нужный формат
        messages = [{"role": msg.role, "message": msg.message} for msg in request.messages]
        
        # Анализируем диалог
        recommendations = await career_interface.process_conversation_data(messages)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Анализ завершен за {duration:.2f} секунд")
        
        return {
            "success": True,
            "recommendations": recommendations,
            "processing_time": duration,
            "message": "Диалог успешно проанализирован"
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа диалога: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")


@app.post("/api/get-user-profile")
async def get_user_profile(request: ProfileRequest):
    """
    Извлекает профиль пользователя из диалога
    
    Args:
        request: Запрос с текстом диалога
        
    Returns:
        Профиль пользователя с целями, навыками и пробелами
    """
    if not career_interface:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    
    try:
        logger.info("Извлечение профиля пользователя")
        
        profile = await career_interface.get_user_profile(request.dialog_text)
        
        return {
            "success": True,
            "profile": profile,
            "message": "Профиль успешно извлечен"
        }
        
    except Exception as e:
        logger.error(f"Ошибка извлечения профиля: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка извлечения профиля: {str(e)}")

@app.post("/api/find-resources")
async def find_resources(request: SkillsRequest):
    """
    Ищет ресурсы для указанных навыков
    
    Args:
        request: Запрос со списком навыков
        
    Returns:
        Ресурсы по категориям: курсы, статьи, вакансии, проекты, соревнования
    """
    if not career_interface:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    
    try:
        start_time = datetime.now()
        logger.info(f"Поиск ресурсов для навыков: {request.skills}")
        
        resources = await career_interface.find_resources_for_skills(request.skills)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Подсчитываем общее количество ресурсов
        total_resources = sum(len(resources[category]) for category in resources)
        
        return {
            "success": True,
            "resources": resources,
            "total_resources": total_resources,
            "processing_time": duration,
            "message": f"Найдено {total_resources} ресурсов для {len(request.skills)} навыков"
        }
        
    except Exception as e:
        logger.error(f"Ошибка поиска ресурсов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка поиска ресурсов: {str(e)}")

@app.post("/api/match-vacancy")
async def match_vacancy(request: VacancyMatchRequest):
    """
    Анализирует соответствие пользователя вакансии
    
    Args:
        request: Запрос с профилем пользователя и информацией о вакансии
        
    Returns:
        Результат анализа соответствия: оценка, решение, обоснование
    """
    if not career_interface:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    
    try:
        logger.info("Анализ соответствия пользователя вакансии")
        
        match_result = await career_interface.match_user_to_vacancy(
            request.user_profile, 
            request.vacancy_info
        )
        
        return {
            "success": True,
            "match": match_result,
            "message": "Анализ соответствия завершен"
        }
        
    except Exception as e:
        logger.error(f"Ошибка анализа соответствия: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа соответствия: {str(e)}")

@app.post("/api/career-advice")
async def get_career_advice(request: CareerAdviceRequest):
    """
    Получает карьерные советы на основе целей и навыков
    
    Args:
        request: Запрос с целями, навыками и проблемами пользователя
        
    Returns:
        Персональные карьерные советы
    """
    if not career_interface:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    
    try:
        logger.info("Генерация карьерных советов")
        
        advice = await career_interface.get_career_advice(
            request.user_goals,
            request.current_skills,
            request.challenges
        )
        
        return {
            "success": True,
            "advice": advice,
            "message": "Карьерные советы сгенерированы"
        }
        
    except Exception as e:
        logger.error(f"Ошибка генерации советов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации советов: {str(e)}")

# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    
    # Проверяем наличие API ключа
    if not os.getenv("SCIBOX_API_KEY"):
        print(" Ошибка: SCIBOX_API_KEY не найден!")
        print("Установите переменную окружения:")
        print("export SCIBOX_API_KEY='ваш-ключ-от-scibox'")
        exit(1)
    
    print(" Запуск Career Advisor API сервера...")
    print(" Документация API: http://localhost:8000/docs")
    print(" Health check: http://localhost:8000/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
