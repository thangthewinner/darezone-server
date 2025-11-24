from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def api_root():
    """API v1 root endpoint"""
    return {
        "version": "1.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "challenges": "/api/v1/challenges",
            "habits": "/api/v1/habits",
            "checkins": "/api/v1/checkins",
            "friends": "/api/v1/friends",
            "notifications": "/api/v1/notifications",
        },
        "docs": "/docs",
        "health": "/health",
    }
