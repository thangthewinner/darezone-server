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

    # Storage Settings
    STORAGE_BUCKET_PHOTOS: str = "darezone-photos"
    STORAGE_BUCKET_VIDEOS: str = "darezone-videos"
    STORAGE_BUCKET_AVATARS: str = "darezone-avatars"
    MAX_UPLOAD_SIZE_MB: int = 10  # Max size for photos in MB
    MAX_VIDEO_SIZE_MB: int = 50  # Max size for videos in MB
    MAX_AVATAR_SIZE_MB: int = 5  # Max size for avatars in MB

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Singleton instance
settings = Settings()
