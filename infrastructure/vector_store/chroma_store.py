"""
Реализация векторного хранилища на основе ChromaDB
"""
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from typing import List, Dict, Any, Optional, Callable
import uuid
import logging
from .base import IVectorStore

logger = logging.getLogger(__name__)


class ChromaVectorStore(IVectorStore):
    """Векторное хранилище на основе ChromaDB"""
    
    def __init__(
        self,
        persist_directory: str = "./vector_store",
        embedding_function: Optional[Callable] = None
    ):
        """
        Инициализация ChromaDB хранилища
        
        Args:
            persist_directory: Директория для сохранения данных
            embedding_function: Функция для создания эмбеддингов
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB не установлен. Установите: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.embedding_function = embedding_function
        
        # Инициализация клиента ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        logger.info(f"ChromaDB инициализирован в {persist_directory}")
    
    async def create_collection(self, collection_name: str) -> bool:
        """Создать коллекцию"""
        try:
            self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Коллекция {collection_name} создана/получена")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания коллекции {collection_name}: {e}")
            return False
    
    async def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Добавить документы в коллекцию"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Генерируем ID если не предоставлены
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]
            
            # Подготавливаем метаданные
            if metadatas is None:
                metadatas = [{}] * len(documents)
            
            # Добавляем документы
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Добавлено {len(documents)} документов в коллекцию {collection_name}")
            return ids
            
        except Exception as e:
            logger.error(f"Ошибка добавления документов в {collection_name}: {e}")
            raise
    
    async def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Поиск похожих документов"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            # Выполняем поиск
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter
            )
            
            # Форматируем результаты
            formatted_results = []
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else 0.0
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка поиска в {collection_name}: {e}")
            return []
    
    async def get_by_ids(
        self,
        collection_name: str,
        ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Получить документы по ID"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            results = collection.get(ids=ids)
            
            formatted_results = []
            if results['ids']:
                for i in range(len(results['ids'])):
                    formatted_results.append({
                        'id': results['ids'][i],
                        'document': results['documents'][i] if results['documents'] else '',
                        'metadata': results['metadatas'][i] if results['metadatas'] else {}
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Ошибка получения документов из {collection_name}: {e}")
            return []
    
    async def delete(
        self,
        collection_name: str,
        ids: List[str]
    ) -> bool:
        """Удалить документы по ID"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            
            collection.delete(ids=ids)
            logger.info(f"Удалено {len(ids)} документов из {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документов из {collection_name}: {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Удалить коллекцию"""
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Коллекция {collection_name} удалена")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления коллекции {collection_name}: {e}")
            return False

