"""
Реализация репозитория диалогов с векторным хранилищем
"""
import logging
import json
from typing import List, Optional
from datetime import datetime
from domain.entities import Conversation
from domain.repositories import IConversationRepository
from infrastructure.vector_store.base import IVectorStore
from infrastructure.vector_store.base import IVectorStore

logger = logging.getLogger(__name__)


class VectorConversationRepository(IConversationRepository):
    """Репозиторий диалогов с векторным хранилищем"""
    
    COLLECTION_NAME = "conversations"
    
    def __init__(self, vector_store: IVectorStore):
        """
        Инициализация репозитория
        
        Args:
            vector_store: Векторное хранилище
        """
        self.vector_store = vector_store
    
    async def _create_collection_if_not_exists(self):
        """Создать коллекцию если её нет"""
        try:
            await self.vector_store.create_collection(self.COLLECTION_NAME)
        except Exception as e:
            logger.warning(f"Коллекция {self.COLLECTION_NAME} уже существует или ошибка: {e}")
    
    def _conversation_to_text(self, conversation: Conversation) -> str:
        """Преобразовать диалог в текст для эмбеддинга"""
        messages_text = []
        for msg in conversation.messages:
            role = msg.get("role", "unknown")
            content = msg.get("message", "") or msg.get("content", "")
            messages_text.append(f"{role}: {content}")
        return "\n".join(messages_text)
    
    async def save(self, conversation: Conversation) -> str:
        """Сохранить диалог и вернуть ID"""
        await self._create_collection_if_not_exists()
        
        # Генерируем ID если его нет
        conversation_id = conversation.id or f"conv_{datetime.now().timestamp()}_{conversation.user_id}"
        conversation.id = conversation_id
        
        # Обновляем время изменения
        conversation.updated_at = datetime.now()
        
        # Преобразуем диалог в текст
        text = self._conversation_to_text(conversation)
        
        # Сохраняем в векторное хранилище
        metadata = {
            "id": conversation_id,
            "user_id": conversation.user_id,
            "messages": json.dumps(conversation.messages, ensure_ascii=False),
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
        
        await self.vector_store.add_documents(
            collection_name=self.COLLECTION_NAME,
            documents=[text],
            metadatas=[metadata],
            ids=[conversation_id]
        )
        
        logger.info(f"Диалог сохранен: {conversation_id}")
        return conversation_id
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Получить диалог по ID"""
        results = await self.vector_store.get_by_ids(
            collection_name=self.COLLECTION_NAME,
            ids=[conversation_id]
        )
        
        if not results:
            return None
        
        return self._metadata_to_conversation(results[0]['metadata'])
    
    async def get_by_user_id(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """Получить диалоги пользователя"""
        # Поиск по метаданным
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=user_id,
            n_results=limit,
            filter={"user_id": user_id}
        )
        
        conversations = []
        for result in results:
            try:
                conversation = self._metadata_to_conversation(result['metadata'])
                conversations.append(conversation)
            except Exception as e:
                logger.error(f"Ошибка преобразования диалога: {e}")
        
        return conversations
    
    async def search_similar(self, query: str, limit: int = 5) -> List[Conversation]:
        """Поиск похожих диалогов по векторному поиску"""
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=query,
            n_results=limit
        )
        
        conversations = []
        for result in results:
            try:
                conversation = self._metadata_to_conversation(result['metadata'])
                conversations.append(conversation)
            except Exception as e:
                logger.error(f"Ошибка преобразования диалога: {e}")
        
        return conversations
    
    async def delete(self, conversation_id: str) -> bool:
        """Удалить диалог"""
        return await self.vector_store.delete(
            collection_name=self.COLLECTION_NAME,
            ids=[conversation_id]
        )
    
    def _metadata_to_conversation(self, metadata: dict) -> Conversation:
        """Преобразовать метаданные в диалог"""
        return Conversation(
            id=metadata.get("id"),
            user_id=metadata.get("user_id", ""),
            messages=json.loads(metadata.get("messages", "[]")),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat()))
        )

