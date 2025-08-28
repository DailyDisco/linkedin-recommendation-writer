"""API v1 package."""

from fastapi import APIRouter

from app.api.v1 import github, recommendations

api_router = APIRouter()
api_router.include_router(github.router, prefix="/github", tags=["github"])
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["recommendations"]
)
