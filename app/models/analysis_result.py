"""Pydantic model representing the result of a false note analysis."""

from pydantic import BaseModel
from typing import List


class AnalysisResult(BaseModel):
    """Response model for an analysis request."""

    total_frames: int
    correct_frames: int
    mean_cents: float
    error_indices: List[int]