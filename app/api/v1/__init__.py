from fastapi import APIRouter
from .router import router as base_router
from .auth import router as auth_router

router = APIRouter()
router.include_router(base_router)
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])

# Future imports will be added here as we implement stories:
# from .users import router as users_router
# from .challenges import router as challenges_router
# router.include_router(users_router, prefix="/users", tags=["Users"])
# router.include_router(challenges_router, prefix="/challenges", tags=["Challenges"])
