#!/usr/bin/env python3
"""
Обновленный API сервер для Career Advisor с векторным хранилищем
Использует новую архитектуру с паттернами проектирования
"""
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорт зависимостей
from infrastructure.di.container import get_container, DIContainer
from application.services.career_service import CareerService
from infrastructure.exceptions import CareerAdvisorException


# Модели данных для API
class ConversationMessage(BaseModel):
    """Сообщение диалога"""
    role: str = Field(..., description="Роль отправителя: 'user' или 'assistant'")
    message: str = Field(..., description="Текст сообщения")


class ConversationRequest(BaseModel):
    """Запрос на анализ диалога"""
    messages: List[ConversationMessage] = Field(..., description="Список сообщений диалога")
    user_id: str = Field(..., description="ID пользователя")


class SkillsRequest(BaseModel):
    """Запрос на поиск ресурсов по навыкам"""
    skills: List[str] = Field(..., description="Список навыков для поиска")


class ProfileRequest(BaseModel):
    """Запрос на извлечение профиля"""
    dialog_text: str = Field(..., description="Текст диалога")
    user_id: str = Field(..., description="ID пользователя")


class VacancyMatchRequest(BaseModel):
    """Запрос на анализ соответствия вакансии"""
    user_profile: Dict[str, Any] = Field(..., description="Профиль пользователя")
    vacancy_info: str = Field(..., description="Информация о вакансии")


class CareerAdviceRequest(BaseModel):
    """Запрос на получение карьерных советов"""
    user_goals: str = Field(..., description="Цели пользователя")
    current_skills: List[str] = Field(..., description="Текущие навыки")
    challenges: str = Field(default="", description="Проблемы/вызовы")


# Инициализация зависимостей
container: Optional[DIContainer] = None
career_service: Optional[CareerService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    global container, career_service
    
    # Инициализация при старте
    logger.info("Инициализация Career Advisor API...")
    try:
        container = get_container()
        career_service = container.get_career_service()
        logger.info("Career Advisor API успешно инициализирован")
    except Exception as e:
        logger.error(f"Ошибка инициализации: {e}")
        raise
    
    yield
    
    # Очистка при остановке
    logger.info("Завершение работы Career Advisor API...")


# Создание FastAPI приложения
app = FastAPI(
    title="Career Advisor API",
    description="API для карьерного агента с векторным хранилищем",
    version="2.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency для получения сервиса
def get_career_service() -> CareerService:
    """Получить сервис карьерного консультирования"""
    if career_service is None:
        raise HTTPException(status_code=500, detail="Career Advisor не инициализирован")
    return career_service


# API Endpoints

@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "Career Advisor API",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Векторное хранилище для всех данных",
            "Семантический поиск ресурсов",
            "Анализ соответствия вакансий",
            "Персональные карьерные рекомендации"
        ]
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "service": "Career Advisor API",
        "timestamp": datetime.now().isoformat(),
        "vector_store_initialized": container is not None and container.get_vector_store() is not None,
        "career_service_initialized": career_service is not None
    }


@app.post("/api/analyze-conversation")
async def analyze_conversation(
    request: ConversationRequest,
    service: CareerService = Depends(get_career_service)
):
    """
    Анализирует диалог и возвращает рекомендации
    
    Args:
        request: Запрос с сообщениями диалога
        
    Returns:
        Рекомендации на основе анализа диалога
    """
    try:
        start_time = datetime.now()
        logger.info(f"Начало анализа диалога: {len(request.messages)} сообщений для пользователя {request.user_id}")
        
        # Преобразуем в нужный формат
        messages = [{"role": msg.role, "message": msg.message} for msg in request.messages]
        
        # Анализируем диалог
        result = await service.analyze_conversation(messages, request.user_id)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Анализ завершен за {duration:.2f} секунд")
        
        return {
            "success": True,
            **result,
            "processing_time": duration,
            "message": "Диалог успешно проанализирован"
        }
        
    except CareerAdvisorException as e:
        logger.error(f"Ошибка анализа диалога: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка анализа диалога: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/api/get-user-profile")
async def get_user_profile(
    request: ProfileRequest,
    service: CareerService = Depends(get_career_service)
):
    """
    Извлекает профиль пользователя из диалога
    
    Args:
        request: Запрос с текстом диалога
        
    Returns:
        Профиль пользователя с целями, навыками и пробелами
    """
    try:
        logger.info(f"Извлечение профиля пользователя {request.user_id}")
        
        profile = await service.get_user_profile(request.dialog_text, request.user_id)
        
        return {
            "success": True,
            "profile": profile,
            "message": "Профиль успешно извлечен"
        }
        
    except CareerAdvisorException as e:
        logger.error(f"Ошибка извлечения профиля: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка извлечения профиля: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка извлечения профиля: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/api/find-resources")
async def find_resources(
    request: SkillsRequest,
    service: CareerService = Depends(get_career_service)
):
    """
    Ищет ресурсы для указанных навыков (использует векторный поиск)
    
    Args:
        request: Запрос со списком навыков
        
    Returns:
        Ресурсы по категориям: курсы, статьи, вакансии, проекты, соревнования
    """
    try:
        start_time = datetime.now()
        logger.info(f"Поиск ресурсов для навыков: {request.skills}")
        
        resources = await service.find_resources_for_skills(request.skills)
        
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
        
    except CareerAdvisorException as e:
        logger.error(f"Ошибка поиска ресурсов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка поиска ресурсов: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка поиска ресурсов: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/api/match-vacancy")
async def match_vacancy(
    request: VacancyMatchRequest,
    service: CareerService = Depends(get_career_service)
):
    """
    Анализирует соответствие пользователя вакансии
    
    Args:
        request: Запрос с профилем пользователя и информацией о вакансии
        
    Returns:
        Результат анализа соответствия: оценка, решение, обоснование
    """
    try:
        logger.info("Анализ соответствия пользователя вакансии")
        
        match_result = await service.match_vacancy(
            request.user_profile,
            request.vacancy_info
        )
        
        return {
            "success": True,
            "match": match_result,
            "message": "Анализ соответствия завершен"
        }
        
    except CareerAdvisorException as e:
        logger.error(f"Ошибка анализа соответствия: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка анализа соответствия: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка анализа соответствия: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/api/career-advice")
async def get_career_advice(
    request: CareerAdviceRequest,
    service: CareerService = Depends(get_career_service)
):
    """
    Получает карьерные советы на основе целей и навыков
    
    Args:
        request: Запрос с целями, навыками и проблемами пользователя
        
    Returns:
        Персональные карьерные советы
    """
    try:
        logger.info("Генерация карьерных советов")
        
        advice = await service.get_career_advice(
            request.user_goals,
            request.current_skills,
            request.challenges
        )
        
        return {
            "success": True,
            "advice": advice,
            "message": "Карьерные советы сгенерированы"
        }
        
    except CareerAdvisorException as e:
        logger.error(f"Ошибка генерации советов: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации советов: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка генерации советов: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


# Запуск сервера
if __name__ == "__main__":
    import uvicorn
    
    # Проверяем наличие API ключа
    if not os.getenv("SCIBOX_API_KEY"):
        print(" Ошибка: SCIBOX_API_KEY не найден!")
        print("Установите переменную окружения:")
        print("export SCIBOX_API_KEY='ваш-ключ-от-scibox'")
        exit(1)
    
    print(" Запуск Career Advisor API сервера (v2.0.0)...")
    print(" Документация API: http://localhost:8000/docs")
    print(" Health check: http://localhost:8000/health")
    print(" Векторное хранилище: ChromaDB")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

