"""Entry point for the FastAPI application."""

import logging
from fastapi import FastAPI

from .routes.upload import router as upload_router
from .routes.analysis import router as analysis_router
from .config import (
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION,
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT
)

# Configure logging
log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

# Create the FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION
)

# Include routers
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(analysis_router, prefix="/analysis", tags=["analysis"])

logger.info("False Note Detection API initialized")


@app.get("/")
def read_root():
    """Root endpoint providing a simple status check."""
    return {
        "message": "Welcome to the False Note Detection API",
        "version": API_VERSION,
        "endpoints": {
            "upload": "/upload/",
            "analysis": "/analysis/health",
            "docs": "/docs"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Log startup event."""
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown event."""
    logger.info("Application shutdown")