"""
Slide Builder API - FastAPI Backend

Provides REST API endpoints for the Slide Builder v2 frontend,
wrapping the existing slide_mcp package functionality.
"""

import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes import presentations, templates, styles, health

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import slide_mcp
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: Initialize connections
    logger.info("Starting Slide Builder API v%s", settings.version)
    if settings.debug:
        logger.warning("Running in DEBUG mode - not for production use")
    yield
    # Shutdown: Cleanup
    logger.info("Shutting down Slide Builder API...")


app = FastAPI(
    title="Slide Builder API",
    description="AI-powered presentation generation API",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(
    presentations.router,
    prefix="/api/v1/presentations",
    tags=["presentations"],
)
app.include_router(
    templates.router,
    prefix="/api/v1/templates",
    tags=["templates"],
)
app.include_router(
    styles.router,
    prefix="/api/v1/styles",
    tags=["styles"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
