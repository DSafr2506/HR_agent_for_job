"""
Кастомные исключения
"""
from typing import Optional


class CareerAdvisorException(Exception):
    """Базовое исключение для Career Advisor"""
    pass


class VectorStoreException(CareerAdvisorException):
    """Исключение векторного хранилища"""
    pass


class LLMServiceException(CareerAdvisorException):
    """Исключение LLM сервиса"""
    pass


class RepositoryException(CareerAdvisorException):
    """Исключение репозитория"""
    pass


class ValidationException(CareerAdvisorException):
    """Исключение валидации"""
    pass

