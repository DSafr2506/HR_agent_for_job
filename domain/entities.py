"""
Доменные сущности (Domain Entities)
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class ResourceType(str, Enum):
    """Типы ресурсов"""
    COURSE = "course"
    ARTICLE = "article"
    VACANCY = "vacancy"
    PROJECT = "project"
    COMPETITION = "competition"


@dataclass
class UserProfile:
    """Профиль пользователя"""
    user_id: str
    goals: str
    skills: List[str]
    experience: str
    challenges: str
    missing_skills: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "user_id": self.user_id,
            "goals": self.goals,
            "skills": self.skills,
            "experience": self.experience,
            "challenges": self.challenges,
            "missing_skills": self.missing_skills,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Создание из словаря"""
        return cls(
            user_id=data["user_id"],
            goals=data.get("goals", ""),
            skills=data.get("skills", []),
            experience=data.get("experience", ""),
            challenges=data.get("challenges", ""),
            missing_skills=data.get("missing_skills", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class Resource:
    """Ресурс для обучения/развития"""
    id: Optional[str] = None
    title: str = ""
    url: str = ""
    description: str = ""
    resource_type: ResourceType = ResourceType.COURSE
    skill: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "resource_type": self.resource_type.value,
            "skill": self.skill,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resource":
        """Создание из словаря"""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            url=data.get("url", ""),
            description=data.get("description", ""),
            resource_type=ResourceType(data.get("resource_type", ResourceType.COURSE.value)),
            skill=data.get("skill", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )


@dataclass
class Conversation:
    """Диалог между пользователем и консультантом"""
    id: Optional[str] = None
    user_id: str = ""
    messages: List[Dict[str, str]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Создание из словаря"""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", ""),
            messages=data.get("messages", []),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass
class Vacancy:
    """Вакансия"""
    id: Optional[str] = None
    title: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    company: str = ""
    url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "company": self.company,
            "url": self.url,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vacancy":
        """Создание из словаря"""
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            description=data.get("description", ""),
            requirements=data.get("requirements", []),
            company=data.get("company", ""),
            url=data.get("url", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
        )

