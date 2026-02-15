"""Pydantic model representing the result of a false note analysis."""

from pydantic import BaseModel, Field
from typing import List, Optional


class AnalysisResult(BaseModel):
    """Response model for an analysis request."""

    total_frames: int = Field(..., description="Total number of frames analyzed")
    correct_frames: int = Field(..., description="Number of frames with correct pitch")
    incorrect_frames: int = Field(..., description="Number of frames with incorrect pitch")
    mean_cents: float = Field(..., description="Mean absolute pitch deviation in cents")
    max_cents: float = Field(..., description="Maximum absolute pitch deviation in cents")
    accuracy_percent: float = Field(..., description="Accuracy percentage (0-100)")
    error_indices: List[int] = Field(..., description="Frame indices where errors were detected")
    duration_seconds: float = Field(..., description="Duration of the analysis in seconds")
    threshold_cents: float = Field(..., description="Threshold used for error detection in cents")