"""Application configuration with environment-based settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App
    APP_NAME: str = "OrionX : AI Educational Platform"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/app.db"

    # Vector store
    VECTOR_STORE_PATH: str = str(BASE_DIR / "data" / "chroma")

    # Embeddings
    EMBEDDING_PROVIDER: str = "sklearn"  # sklearn, sentence-transformers
    EMBEDDING_MODEL: str = "tfidf"  # or model name for sentence-transformers

    # LLM
    LLM_PROVIDER: str = "openai"  # openai, mock
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Retrieval
    RETRIEVAL_TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.1

    # Auth
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 20
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
