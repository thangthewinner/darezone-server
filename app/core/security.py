"""
Security and authentication helpers
Will be implemented in Story 3: Authentication System
"""

from typing import Optional
from fastapi import Depends, Header
from app.core.exceptions import unauthorized_exception


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Get current user ID from JWT token
    TODO: Implement in Story 3
    """
    if not authorization:
        raise unauthorized_exception("Authorization header required")

    # Placeholder - will verify JWT in Story 3
    raise unauthorized_exception("Authentication not implemented yet")


async def verify_supabase_jwt(token: str) -> dict:
    """
    Verify Supabase JWT token
    TODO: Implement in Story 3
    """
    pass
