"""
Реализация репозитория ресурсов с векторным хранилищем
"""
import logging
import json
from typing import List, Optional
from datetime import datetime
from domain.entities import Resource, ResourceType
from domain.repositories import IResourceRepository
from infrastructure.vector_store.base import IVectorStore
from infrastructure.vector_store.base import IVectorStore

logger = logging.getLogger(__name__)


class VectorResourceRepository(IResourceRepository):
    """Репозиторий ресурсов с векторным хранилищем"""
    
    COLLECTION_NAME = "resources"
    
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
    
    def _resource_to_text(self, resource: Resource) -> str:
        """Преобразовать ресурс в текст для эмбеддинга"""
        parts = [resource.title]
        if resource.description:
            parts.append(resource.description)
        if resource.skill:
            parts.append(f"Навык: {resource.skill}")
        return " | ".join(parts)
    
    async def save(self, resource: Resource) -> str:
        """Сохранить ресурс и вернуть ID"""
        await self._create_collection_if_not_exists()
        
        # Генерируем ID если его нет
        resource_id = resource.id or f"resource_{datetime.now().timestamp()}_{hash(resource.url)}"
        resource.id = resource_id
        
        # Преобразуем ресурс в текст
        text = self._resource_to_text(resource)
        
        # Сохраняем в векторное хранилище
        metadata = {
            "id": resource_id,
            "title": resource.title,
            "url": resource.url,
            "description": resource.description,
            "resource_type": resource.resource_type.value,
            "skill": resource.skill,
            "metadata": json.dumps(resource.metadata),
            "created_at": resource.created_at.isoformat()
        }
        
        await self.vector_store.add_documents(
            collection_name=self.COLLECTION_NAME,
            documents=[text],
            metadatas=[metadata],
            ids=[resource_id]
        )
        
        logger.info(f"Ресурс сохранен: {resource_id}")
        return resource_id
    
    async def save_batch(self, resources: List[Resource]) -> List[str]:
        """Сохранить несколько ресурсов"""
        await self._create_collection_if_not_exists()
        
        documents = []
        metadatas = []
        ids = []
        
        for resource in resources:
            resource_id = resource.id or f"resource_{datetime.now().timestamp()}_{hash(resource.url)}"
            resource.id = resource_id
            
            documents.append(self._resource_to_text(resource))
            metadatas.append({
                "id": resource_id,
                "title": resource.title,
                "url": resource.url,
                "description": resource.description,
                "resource_type": resource.resource_type.value,
                "skill": resource.skill,
                "metadata": json.dumps(resource.metadata),
                "created_at": resource.created_at.isoformat()
            })
            ids.append(resource_id)
        
        await self.vector_store.add_documents(
            collection_name=self.COLLECTION_NAME,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Сохранено {len(resources)} ресурсов")
        return ids
    
    async def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """Получить ресурс по ID"""
        results = await self.vector_store.get_by_ids(
            collection_name=self.COLLECTION_NAME,
            ids=[resource_id]
        )
        
        if not results:
            return None
        
        return self._metadata_to_resource(results[0]['metadata'])
    
    async def search_by_skill(
        self,
        skill: str,
        resource_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Resource]:
        """Поиск ресурсов по навыку (векторный поиск)"""
        filter_dict = {"skill": skill}
        if resource_type:
            filter_dict["resource_type"] = resource_type
        
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=skill,
            n_results=limit,
            filter=filter_dict if filter_dict else None
        )
        
        resources = []
        for result in results:
            try:
                resource = self._metadata_to_resource(result['metadata'])
                resources.append(resource)
            except Exception as e:
                logger.error(f"Ошибка преобразования ресурса: {e}")
        
        return resources
    
    async def search_similar(
        self,
        query: str,
        resource_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Resource]:
        """Поиск похожих ресурсов по векторному поиску"""
        filter_dict = {}
        if resource_type:
            filter_dict["resource_type"] = resource_type
        
        results = await self.vector_store.search(
            collection_name=self.COLLECTION_NAME,
            query=query,
            n_results=limit,
            filter=filter_dict if filter_dict else None
        )
        
        resources = []
        for result in results:
            try:
                resource = self._metadata_to_resource(result['metadata'])
                resources.append(resource)
            except Exception as e:
                logger.error(f"Ошибка преобразования ресурса: {e}")
        
        return resources
    
    async def delete(self, resource_id: str) -> bool:
        """Удалить ресурс"""
        return await self.vector_store.delete(
            collection_name=self.COLLECTION_NAME,
            ids=[resource_id]
        )
    
    def _metadata_to_resource(self, metadata: dict) -> Resource:
        """Преобразовать метаданные в ресурс"""
        return Resource(
            id=metadata.get("id"),
            title=metadata.get("title", ""),
            url=metadata.get("url", ""),
            description=metadata.get("description", ""),
            resource_type=ResourceType(metadata.get("resource_type", ResourceType.COURSE.value)),
            skill=metadata.get("skill", ""),
            metadata=json.loads(metadata.get("metadata", "{}")),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
        )

