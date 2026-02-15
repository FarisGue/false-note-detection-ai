"""Miscellaneous analysis endpoints (health checks, diagnostics)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok"}