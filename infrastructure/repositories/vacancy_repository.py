"""
Реализация репозитория вакансий с векторным хранилищем
"""
import logging
import json
from typing import List, Optional
from datetime import datetime
from domain.entities import Vacancy, UserProfile
from domain.repositories import IVacancyRepository
from infrastructure.vector_store.base import IVectorStore
from infrastructure.vector_store.base import IVectorStore

logger = logging.getLogger(__name__)


class VectorVacancyRepository(IVacancyRepository):
    """Репозиторий вакансий с векторным хранилищем"""
    
    COLLECTION_NAME = "vacancies"
    
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
    
    def _vacancy_to_text(self, vacancy: Vacancy) -> str:
        """Преобразовать вакансию в текст для эмбеддинга"""
        parts = [vacancy.title]
        if vacancy.description:
            parts.append(vacancy.description)
        if vacancy.requirements:
            parts.append(f"Требования: {', '.join(vacancy.requirements)}")
        if vacancy.company:
            parts.append(f"Компания: {vacancy.company}")
        return " | ".join(parts)
    
    async def save(self, vacancy: Vacancy) -> str:
        """Сохранить вакансию и вернуть ID"""
        await self._create_collection_if_not_exists()
        
        # Генерируем ID если его нет
        vacancy_id = vacancy.id or f"vacancy_{datetime.now().timestamp()}_{hash(vacancy.url)}"
        vacancy.id = vacancy_id
        
        # Преобразуем вакансию в текст
        text = self._vacancy_to_text(vacancy)
        
        # Сохраняем в векторное хранилище
        metadata = {
            "id": vacancy_id,
            "title": vacancy.title,
            "description": vacancy.description,
            "requirements": json.dumps(vacancy.requirements, ensure_ascii=False),
            "company": vacancy.company,
            "url": vacancy.url,
            "metadata": json.dumps(vacancy.metadata),
            "created_at": vacancy.created_at.isoformat()
        }
        
        await self.vector_store.add_documents(
            collection_name=self.COLLECTION_NAME,
            documents=[text],
            metadatas=[metadata],
            ids=[vacancy_id]
        )
        
        logger.info(f"Вакансия сохранена: {vacancy_id}")
        return vacancy_id
    
    async def get_by_id(self, vacancy_id: str) -> Optional[Vacancy]:
        """Получить вакансию по ID"""
        results = await self.vector_store.get_by_ids(
            collection_name=self.COLLECTION_NAME,
            ids=[vacancy_id]
        )
        
        if not results:
            return None
        
        return self._metadata_to_vacancy(results[0]['metadata'])
    
    async def search_similar(self, query: str, limit: int = 10) -> List[Vacancy]:
        """Поиск похожих вакансий по векторному поиску"""
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=query,
            n_results=limit
        )
        
        vacancies = []
        for result in results:
            try:
                vacancy = self._metadata_to_vacancy(result['metadata'])
                vacancies.append(vacancy)
            except Exception as e:
                logger.error(f"Ошибка преобразования вакансии: {e}")
        
        return vacancies
    
    async def match_to_profile(self, profile: UserProfile, limit: int = 10) -> List[Vacancy]:
        """Поиск вакансий, соответствующих профилю пользователя"""
        # Создаем запрос на основе профиля пользователя
        query_parts = [
            profile.goals,
            ", ".join(profile.skills),
            ", ".join(profile.missing_skills)
        ]
        query = " | ".join(query_parts)
        
        # Ищем похожие вакансии
        return await self.search_similar(query, limit)
    
    async def delete(self, vacancy_id: str) -> bool:
        """Удалить вакансию"""
        return await self.vector_store.delete(
            collection_name=self.COLLECTION_NAME,
            ids=[vacancy_id]
        )
    
    def _metadata_to_vacancy(self, metadata: dict) -> Vacancy:
        """Преобразовать метаданные в вакансию"""
        return Vacancy(
            id=metadata.get("id"),
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            requirements=json.loads(metadata.get("requirements", "[]")),
            company=metadata.get("company", ""),
            url=metadata.get("url", ""),
            metadata=json.loads(metadata.get("metadata", "{}")),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
        )

