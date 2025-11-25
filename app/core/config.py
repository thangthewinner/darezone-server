from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    APP_NAME: str = "DareZone API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # CORS - can be comma-separated string or list
    ALLOWED_ORIGINS: Union[
        str, List[str]
    ] = "http://localhost:19006,http://localhost:8081"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Business Logic
    MAX_HABITS_PER_CHALLENGE: int = 4
    DEFAULT_HITCH_COUNT: int = 2
    POINTS_PER_CHECKIN: int = 10
    POINTS_STREAK_MULTIPLIER: int = 2

    # Push Notifications
    EXPO_ACCESS_TOKEN: str = ""  # Optional: Expo push notification token

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Singleton instance
settings = Settings()
