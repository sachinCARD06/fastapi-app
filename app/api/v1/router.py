from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, hospitals, users

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(hospitals.router, prefix="/hospitals", tags=["hospitals"])
