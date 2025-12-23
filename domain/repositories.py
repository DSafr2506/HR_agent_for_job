"""
Интерфейсы репозиториев (Repository Pattern)
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import UserProfile, Resource, Conversation, Vacancy


class IUserProfileRepository(ABC):
    """Интерфейс репозитория профилей пользователей"""
    
    @abstractmethod
    async def save(self, profile: UserProfile) -> str:
        """Сохранить профиль и вернуть ID"""
        pass
    
    @abstractmethod
    async def get_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """Получить профиль по ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Получить профиль по user_id"""
        pass
    
    @abstractmethod
    async def search_similar(self, query: str, limit: int = 5) -> List[UserProfile]:
        """Поиск похожих профилей по векторному поиску"""
        pass
    
    @abstractmethod
    async def update(self, profile: UserProfile) -> bool:
        """Обновить профиль"""
        pass
    
    @abstractmethod
    async def delete(self, profile_id: str) -> bool:
        """Удалить профиль"""
        pass


class IResourceRepository(ABC):
    """Интерфейс репозитория ресурсов"""
    
    @abstractmethod
    async def save(self, resource: Resource) -> str:
        """Сохранить ресурс и вернуть ID"""
        pass
    
    @abstractmethod
    async def save_batch(self, resources: List[Resource]) -> List[str]:
        """Сохранить несколько ресурсов"""
        pass
    
    @abstractmethod
    async def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """Получить ресурс по ID"""
        pass
    
    @abstractmethod
    async def search_by_skill(self, skill: str, resource_type: Optional[str] = None, limit: int = 10) -> List[Resource]:
        """Поиск ресурсов по навыку (векторный поиск)"""
        pass
    
    @abstractmethod
    async def search_similar(self, query: str, resource_type: Optional[str] = None, limit: int = 10) -> List[Resource]:
        """Поиск похожих ресурсов по векторному поиску"""
        pass
    
    @abstractmethod
    async def delete(self, resource_id: str) -> bool:
        """Удалить ресурс"""
        pass


class IConversationRepository(ABC):
    """Интерфейс репозитория диалогов"""
    
    @abstractmethod
    async def save(self, conversation: Conversation) -> str:
        """Сохранить диалог и вернуть ID"""
        pass
    
    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Получить диалог по ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """Получить диалоги пользователя"""
        pass
    
    @abstractmethod
    async def search_similar(self, query: str, limit: int = 5) -> List[Conversation]:
        """Поиск похожих диалогов по векторному поиску"""
        pass
    
    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        """Удалить диалог"""
        pass


class IVacancyRepository(ABC):
    """Интерфейс репозитория вакансий"""
    
    @abstractmethod
    async def save(self, vacancy: Vacancy) -> str:
        """Сохранить вакансию и вернуть ID"""
        pass
    
    @abstractmethod
    async def get_by_id(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получить вакансию по ID"""
        pass
    
    @abstractmethod
    async def search_similar(self, query: str, limit: int = 10) -> List[Vacancy]:
        """Поиск похожих вакансий по векторному поиску"""
        pass
    
    @abstractmethod
    async def match_to_profile(self, profile: UserProfile, limit: int = 10) -> List[Vacancy]:
        """Поиск вакансий, соответствующих профилю пользователя"""
        pass
    
    @abstractmethod
    async def delete(self, vacancy_id: str) -> bool:
        """Удалить вакансию"""
        pass

