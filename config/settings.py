"""
Настройки приложения с использованием переменных окружения
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API Keys
    scibox_api_key: str = Field(..., env="SCIBOX_API_KEY")
    scibox_api_url: str = Field(
        default="https://llm.t1v.scibox.tech/v1",
        env="SCIBOX_API_URL"
    )
    scibox_model: str = Field(
        default="Qwen2.5-72B-Instruct-AWQ",
        env="SCIBOX_MODEL"
    )
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")
    
    # Vector Store Settings
    vector_store_type: str = Field(default="chroma", env="VECTOR_STORE_TYPE")  # chroma, faiss
    vector_store_path: str = Field(
        default="./vector_store",
        env="VECTOR_STORE_PATH"
    )
    embedding_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")
    
    # Application Settings
    max_history_length: int = Field(default=10, env="MAX_HISTORY_LENGTH")
    request_timeout: int = Field(default=60, env="REQUEST_TIMEOUT")
    max_resources_per_category: int = Field(default=10, env="MAX_RESOURCES_PER_CATEGORY")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Глобальный экземпляр настроек
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Получить настройки приложения (Singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

