"""Application configuration using pydantic-settings"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = "E-commerce Intelligence Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    demo_mode: bool = True  # Enable demo mode for academic/testing purposes
    
    # Data Source Configuration
    data_source: str = "mock_api"  # "mock_api" or "database"
    mock_api_url: str = "https://amazon-seller-db.vercel.app"  # Deployed Vercel API
    internal_api_key: str = "super-secret-internal-key-change-in-production"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./ecommerce_intelligence.db"
    
    # Security
    secret_key: str  # No default - must be set in .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    # LLM Configuration
    llm_provider: str = "openai"  # "openai" or "gemini"
    openai_api_key: str | None = None  # Optional - required only if using OpenAI
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimension: int = 512
    gemini_api_key: str | None = None  # Optional - required only if using Gemini
    gemini_model: str = "gemini-pro"
    
    # Redis Cache Configuration
    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate LLM provider is one of the supported options"""
        if v not in {"openai", "gemini"}:
            raise ValueError("llm_provider must be 'openai' or 'gemini'")
        return v


# Global settings instance
settings = Settings()
