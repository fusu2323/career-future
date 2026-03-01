"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # GLM API
    GLM_API_KEY: str

    # Neo4j Configuration
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "fusu2023yzcm"
    NEO4J_DATABASE: str = "career_planning"

    # Chroma Configuration
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    @property
    def chroma_url(self) -> str:
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"

    class Config:
        env_file = ".env"
        extra = "ignore"


# Global settings instance
settings = Settings()
