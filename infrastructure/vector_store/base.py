"""
Базовый интерфейс для векторного хранилища
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IVectorStore(ABC):
    """Интерфейс векторного хранилища"""
    
    @abstractmethod
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Добавить документы в коллекцию"""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Поиск похожих документов"""
        pass
    
    @abstractmethod
    async def get_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Получить документы по ID"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """Удалить документы по ID"""
        pass
    
    @abstractmethod
    async def create_collection(self, collection_name: str) -> bool:
        """Создать коллекцию"""
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> bool:
        """Удалить коллекцию"""
        pass

