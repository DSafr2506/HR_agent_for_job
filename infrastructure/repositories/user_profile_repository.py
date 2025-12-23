"""
Реализация репозитория профилей пользователей с векторным хранилищем
"""
import logging
import json
from typing import List, Optional
from datetime import datetime
from domain.entities import UserProfile
from domain.repositories import IUserProfileRepository
from infrastructure.vector_store.base import IVectorStore
from infrastructure.embeddings.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class VectorUserProfileRepository(IUserProfileRepository):
    """Репозиторий профилей пользователей с векторным хранилищем"""
    
    COLLECTION_NAME = "user_profiles"
    
    def __init__(self, vector_store: IVectorStore):
        """
        Инициализация репозитория
        
        Args:
            vector_store: Векторное хранилище
        """
        self.vector_store = vector_store
        self.embedding_service = get_embedding_service()
    
    async def _create_collection_if_not_exists(self):
        """Создать коллекцию если её нет"""
        try:
            await self.vector_store.create_collection(self.COLLECTION_NAME)
        except Exception as e:
            logger.warning(f"Коллекция {self.COLLECTION_NAME} уже существует или ошибка: {e}")
    
    def _profile_to_text(self, profile: UserProfile) -> str:
        """Преобразовать профиль в текст для эмбеддинга"""
        parts = [
            f"Цели: {profile.goals}",
            f"Навыки: {', '.join(profile.skills)}",
            f"Опыт: {profile.experience}",
            f"Проблемы: {profile.challenges}",
            f"Недостающие навыки: {', '.join(profile.missing_skills)}"
        ]
        return " | ".join(parts)
    
    async def save(self, profile: UserProfile) -> str:
        """Сохранить профиль и вернуть ID"""
        await self._create_collection_if_not_exists()
        
        # Генерируем ID если его нет
        profile_id = profile.user_id or f"profile_{datetime.now().timestamp()}"
        
        # Обновляем время изменения
        profile.updated_at = datetime.now()
        
        # Преобразуем профиль в текст и создаем эмбеддинг
        text = self._profile_to_text(profile)
        
        # Сохраняем в векторное хранилище
        metadata = {
            "user_id": profile.user_id,
            "goals": profile.goals,
            "skills": json.dumps(profile.skills),
            "experience": profile.experience,
            "challenges": profile.challenges,
            "missing_skills": json.dumps(profile.missing_skills),
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat()
        }
        
        await self.vector_store.add_documents(
            collection_name=self.COLLECTION_NAME,
            documents=[text],
            metadatas=[metadata],
            ids=[profile_id]
        )
        
        logger.info(f"Профиль сохранен: {profile_id}")
        return profile_id
    
    async def get_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """Получить профиль по ID"""
        results = await self.vector_store.get_by_ids(
            collection_name=self.COLLECTION_NAME,
            ids=[profile_id]
        )
        
        if not results:
            return None
        
        return self._metadata_to_profile(results[0]['metadata'])
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Получить профиль по user_id"""
        # Поиск по метаданным
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=user_id,
            n_results=1,
            filter={"user_id": user_id}
        )
        
        if not results:
            return None
        
        return self._metadata_to_profile(results[0]['metadata'])
    
    async def search_similar(self, query: str, limit: int = 5) -> List[UserProfile]:
        """Поиск похожих профилей по векторному поиску"""
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=query,
            n_results=limit
        )
        
        profiles = []
        for result in results:
            try:
                profile = self._metadata_to_profile(result['metadata'])
                profiles.append(profile)
            except Exception as e:
                logger.error(f"Ошибка преобразования профиля: {e}")
        
        return profiles
    
    async def update(self, profile: UserProfile) -> bool:
        """Обновить профиль"""
        profile_id = profile.user_id
        if not profile_id:
            return False
        
        # Удаляем старый профиль
        await self.delete(profile_id)
        
        # Сохраняем новый
        await self.save(profile)
        return True
    
    async def delete(self, profile_id: str) -> bool:
        """Удалить профиль"""
        return await self.vector_store.delete(
            collection_name=self.COLLECTION_NAME,
            ids=[profile_id]
        )
    
    def _metadata_to_profile(self, metadata: dict) -> UserProfile:
        """Преобразовать метаданные в профиль"""
        return UserProfile(
            user_id=metadata.get("user_id", ""),
            goals=metadata.get("goals", ""),
            skills=json.loads(metadata.get("skills", "[]")),
            experience=metadata.get("experience", ""),
            challenges=metadata.get("challenges", ""),
            missing_skills=json.loads(metadata.get("missing_skills", "[]")),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat()))
        )

