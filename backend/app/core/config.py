from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kinetic E-Commerce AI Support"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "local-development-only-change-before-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = "sqlite:///./kinetic_support.db"
    
    # LLM settings (optional - works completely offline/mocked if empty)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    LLM_PROVIDER: str = "auto"  # 'auto', 'gemini', 'groq', or 'mock'

    # Business Rules
    MAX_AUTO_REFUND_AMOUNT: float = 5000.0  # Refunds > ₹5,000 must be escalated
    DEFAULT_RETURN_WINDOW_DAYS: int = 14

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
