"""Health check endpoints."""

from fastapi import APIRouter
from ..config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": settings.version}


@router.get("/api/health")
async def api_health_check():
    """API health check endpoint."""
    return {"status": "healthy", "version": settings.version}
