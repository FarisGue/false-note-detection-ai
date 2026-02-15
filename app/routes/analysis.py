"""Miscellaneous analysis endpoints (health checks, diagnostics, AI recommendations)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from ..services.ai_recommender import generate_recommendations
from ..models.recommendation_result import RecommendationResult

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple health check endpoint to verify the API is running."""
    return {"status": "ok"}


class AnalysisResultInput(BaseModel):
    """Input model for recommendation generation."""
    analysis_result: Dict[str, Any]


@router.post("/recommendations", response_model=RecommendationResult)
async def get_recommendations(input_data: AnalysisResultInput):
    """
    Generate AI recommendations for improving musical performance based on analysis results.
    
    This endpoint takes the JSON result from the analysis and sends it to OpenRoute DeepSeek API
    to generate personalized recommendations for the musician.
    
    Args:
        input_data: Contains the analysis_result dictionary from the upload endpoint
    
    Returns:
        RecommendationResult: Contains the AI-generated recommendations or error message
    """
    try:
        recommendations = generate_recommendations(input_data.analysis_result)
        
        if recommendations:
            return RecommendationResult(
                recommendations=recommendations,
                success=True,
                error_message=None
            )
        else:
            return RecommendationResult(
                recommendations=None,
                success=False,
                error_message="Failed to generate recommendations. Please check API configuration."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )