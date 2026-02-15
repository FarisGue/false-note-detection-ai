"""Pydantic model for AI recommendation results."""

from pydantic import BaseModel, Field
from typing import Optional


class RecommendationResult(BaseModel):
    """Response model for AI recommendations."""
    
    recommendations: Optional[str] = Field(
        None,
        description="AI-generated recommendations for improving musical performance"
    )
    success: bool = Field(
        ...,
        description="Whether the recommendation generation was successful"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if recommendation generation failed"
    )

