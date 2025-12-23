"""
Фабрика для создания векторных хранилищ (Factory Pattern)
"""
from typing import Optional
import logging
from config.settings import get_settings
from .base import IVectorStore
from .chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


class VectorStoreFactory:
    """Фабрика для создания векторных хранилищ"""
    
    @staticmethod
    def create_vector_store(
        store_type: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_function=None
    ) -> IVectorStore:
        """
        Создать векторное хранилище
        
        Args:
            store_type: Тип хранилища (chroma, faiss)
            persist_directory: Директория для сохранения
            embedding_function: Функция для создания эмбеддингов
            
        Returns:
            Экземпляр векторного хранилища
        """
        settings = get_settings()
        
        store_type = store_type or settings.vector_store_type
        persist_directory = persist_directory or settings.vector_store_path
        
        if store_type.lower() == "chroma":
            logger.info(f"Создание ChromaDB хранилища в {persist_directory}")
            return ChromaVectorStore(
                persist_directory=persist_directory,
                embedding_function=embedding_function
            )
        elif store_type.lower() == "faiss":
            # TODO: Реализовать FAISS хранилище
            raise NotImplementedError("FAISS хранилище пока не реализовано")
        else:
            raise ValueError(f"Неизвестный тип хранилища: {store_type}")

