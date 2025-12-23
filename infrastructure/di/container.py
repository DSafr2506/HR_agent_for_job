"""
Контейнер зависимостей (Dependency Injection Container)
"""
import logging
from typing import Optional
from config.settings import get_settings
from infrastructure.vector_store.factory import VectorStoreFactory
from infrastructure.vector_store.base import IVectorStore
from infrastructure.embeddings.embedding_service import get_embedding_service
from infrastructure.repositories.user_profile_repository import VectorUserProfileRepository
from infrastructure.repositories.resource_repository import VectorResourceRepository
from infrastructure.repositories.conversation_repository import VectorConversationRepository
from infrastructure.repositories.vacancy_repository import VectorVacancyRepository
from infrastructure.llm.llm_service import LLMService
from infrastructure.searcher.web_searcher import WebSearcher
from application.services.career_service import CareerService
from domain.repositories import (
    IUserProfileRepository,
    IResourceRepository,
    IConversationRepository,
    IVacancyRepository
)

logger = logging.getLogger(__name__)


class DIContainer:
    """Контейнер зависимостей (Singleton)"""
    
    _instance: Optional['DIContainer'] = None
    
    def __init__(self):
        """Инициализация контейнера"""
        if DIContainer._instance is not None:
            raise RuntimeError("DIContainer уже инициализирован. Используйте get_instance()")
        
        self.settings = get_settings()
        self._vector_store: Optional[IVectorStore] = None
        self._user_profile_repo: Optional[IUserProfileRepository] = None
        self._resource_repo: Optional[IResourceRepository] = None
        self._conversation_repo: Optional[IConversationRepository] = None
        self._vacancy_repo: Optional[IVacancyRepository] = None
        self._llm_service: Optional[LLMService] = None
        self._career_service: Optional[CareerService] = None
        
        DIContainer._instance = self
    
    @classmethod
    def get_instance(cls) -> 'DIContainer':
        """Получить экземпляр контейнера (Singleton)"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_vector_store(self) -> IVectorStore:
        """Получить векторное хранилище"""
        if self._vector_store is None:
            embedding_service = get_embedding_service()
            # Создаем функцию эмбеддинга для ChromaDB
            def embedding_function(texts):
                return embedding_service.encode(texts)
            
            self._vector_store = VectorStoreFactory.create_vector_store(
                embedding_function=embedding_function
            )
            logger.info("Векторное хранилище инициализировано")
        
        return self._vector_store
    
    def get_user_profile_repository(self) -> IUserProfileRepository:
        """Получить репозиторий профилей пользователей"""
        if self._user_profile_repo is None:
            vector_store = self.get_vector_store()
            self._user_profile_repo = VectorUserProfileRepository(vector_store)
            logger.info("Репозиторий профилей пользователей инициализирован")
        
        return self._user_profile_repo
    
    def get_resource_repository(self) -> IResourceRepository:
        """Получить репозиторий ресурсов"""
        if self._resource_repo is None:
            vector_store = self.get_vector_store()
            self._resource_repo = VectorResourceRepository(vector_store)
            logger.info("Репозиторий ресурсов инициализирован")
        
        return self._resource_repo
    
    def get_conversation_repository(self) -> IConversationRepository:
        """Получить репозиторий диалогов"""
        if self._conversation_repo is None:
            vector_store = self.get_vector_store()
            self._conversation_repo = VectorConversationRepository(vector_store)
            logger.info("Репозиторий диалогов инициализирован")
        
        return self._conversation_repo
    
    def get_vacancy_repository(self) -> IVacancyRepository:
        """Получить репозиторий вакансий"""
        if self._vacancy_repo is None:
            vector_store = self.get_vector_store()
            self._vacancy_repo = VectorVacancyRepository(vector_store)
            logger.info("Репозиторий вакансий инициализирован")
        
        return self._vacancy_repo
    
    def get_llm_service(self) -> LLMService:
        """Получить сервис LLM"""
        if self._llm_service is None:
            self._llm_service = LLMService(
                api_key=self.settings.scibox_api_key,
                base_url=self.settings.scibox_api_url,
                model=self.settings.scibox_model
            )
            logger.info("LLM сервис инициализирован")
        
        return self._llm_service
    
    def get_web_searcher(self) -> WebSearcher:
        """Получить сервис поиска ресурсов в интернете"""
        return WebSearcher(self.get_resource_repository())
    
    def get_career_service(self) -> CareerService:
        """Получить сервис карьерного консультирования"""
        if self._career_service is None:
            self._career_service = CareerService(
                user_profile_repo=self.get_user_profile_repository(),
                resource_repo=self.get_resource_repository(),
                conversation_repo=self.get_conversation_repository(),
                vacancy_repo=self.get_vacancy_repository(),
                llm_service=self.get_llm_service(),
                web_searcher=self.get_web_searcher()
            )
            logger.info("Сервис карьерного консультирования инициализирован")
        
        return self._career_service


def get_container() -> DIContainer:
    """Получить контейнер зависимостей"""
    return DIContainer.get_instance()

