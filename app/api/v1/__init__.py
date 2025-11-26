from fastapi import APIRouter
from .router import router as base_router
from .auth import router as auth_router
from .users import router as users_router
from .challenges import router as challenges_router
from .checkins import router as checkins_router
from .friends import router as friends_router
from .notifications import router as notifications_router
from .media import router as media_router

router = APIRouter()
router.include_router(base_router)
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(challenges_router, prefix="/challenges", tags=["Challenges"])
router.include_router(checkins_router, prefix="/checkins", tags=["Check-ins"])
router.include_router(friends_router, prefix="/friends", tags=["Friends"])
router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
router.include_router(media_router, prefix="/media", tags=["Media"])
