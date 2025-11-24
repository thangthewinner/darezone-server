from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime


class TokenVerifyResponse(BaseModel):
    """Token verification response"""

    valid: bool
    user_id: str
    email: EmailStr


class CurrentUserResponse(BaseModel):
    """Current user full profile response"""

    id: str
    email: EmailStr
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    account_type: str = "b2c"
    stats: Dict[str, int]
    created_at: datetime

    class Config:
        from_attributes = True
