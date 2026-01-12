"""
Pydantic schemas for anonymous user authentication
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
import re


class AnonymousLoginRequest(BaseModel):
    """Request schema for anonymous login"""

    device_id: str = Field(
        ...,
        min_length=36,
        max_length=36,
        description="Unique device identifier (UUID format)",
    )

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        """Validate device_id is a valid UUID format"""
        # UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )

        if not uuid_pattern.match(v):
            raise ValueError(
                "device_id must be a valid UUID v4 format (e.g., 550e8400-e29b-41d4-a716-446655440000)"
            )

        return v.lower()


class AnonymousLoginResponse(BaseModel):
    """Response schema for anonymous login"""

    access_token: str = Field(..., description="JWT access token for API authentication")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    user_id: str = Field(..., description="Unique user ID")
    is_anonymous: bool = Field(default=True, description="Flag indicating anonymous user")
    created_at: datetime = Field(..., description="Timestamp when user was created")
    is_new_user: bool = Field(
        ..., description="True if this is a newly created user, False if existing"
    )


class AnonymousUserInfo(BaseModel):
    """Anonymous user information"""

    id: str
    device_id: str
    user_id: str
    email: str
    created_at: datetime
    last_login_at: datetime
    upgraded_at: Optional[datetime] = None
    upgraded_to_user_id: Optional[str] = None


class UpgradeAccountRequest(BaseModel):
    """Request schema for upgrading anonymous account to real account (future feature)"""

    email: str = Field(..., description="Email for real account")
    password: str = Field(..., min_length=8, description="Password for real account")
    full_name: Optional[str] = Field(None, description="User's full name")
    display_name: Optional[str] = Field(None, description="Display name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format"""
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        if not email_pattern.match(v):
            raise ValueError("Invalid email format")
        return v.lower()


class UpgradeAccountResponse(BaseModel):
    """Response schema for account upgrade (future feature)"""

    success: bool
    message: str
    new_user_id: str
    access_token: str
    token_type: str = "bearer"
