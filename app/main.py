"""Entry point for the FastAPI application."""

from fastapi import FastAPI

from .routes.upload import router as upload_router
from .routes.analysis import router as analysis_router

# Create the FastAPI app
app = FastAPI(title="False Note Detection API", description="API for detecting false notes in music performances.")

# Include routers
app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(analysis_router, prefix="/analysis", tags=["analysis"])


@app.get("/")
def read_root():
    """Root endpoint providing a simple status check."""
    return {"message": "Welcome to the False Note Detection API"}