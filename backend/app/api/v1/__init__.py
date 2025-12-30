"""API v1 package."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.github import router as github_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(billing_router, tags=["Billing"])
api_router.include_router(github_router, prefix="/github", tags=["GitHub"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
