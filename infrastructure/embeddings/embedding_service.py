"""
Сервис для создания эмбеддингов
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
from config.settings import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Сервис для создания эмбеддингов текста"""
    
    def __init__(self, model_name: str = None):
        """
        Инициализация сервиса эмбеддингов
        
        Args:
            model_name: Название модели для эмбеддингов
        """
        settings = get_settings()
        self.model_name = model_name or settings.embedding_model
        
        logger.info(f"Загрузка модели эмбеддингов: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Модель эмбеддингов загружена")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Создать эмбеддинги для списка текстов
        
        Args:
            texts: Список текстов для кодирования
            
        Returns:
            Список векторов эмбеддингов
        """
        if not texts:
            return []
        
        embeddings = self.model.encode(texts, convert_to_numpy=False)
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings
    
    def encode_single(self, text: str) -> List[float]:
        """
        Создать эмбеддинг для одного текста
        
        Args:
            text: Текст для кодирования
            
        Returns:
            Вектор эмбеддинга
        """
        return self.encode([text])[0]


# Глобальный экземпляр сервиса (Singleton)
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """Получить экземпляр сервиса эмбеддингов (Singleton)"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

