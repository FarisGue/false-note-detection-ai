"""Functions to compute scoring metrics for the false note detection."""

import numpy as np


def compute_score(error_indices: np.ndarray, total_frames: int) -> dict:
    """Compute summary statistics from the detected error indices.

    Args:
        error_indices: Indices of frames where false notes were detected.
        total_frames: Total number of frames considered in the analysis.

    Returns:
        A dictionary containing the number of correct frames and the mean absolute cents error estimate.
    """
    # Number of incorrect frames
    incorrect = len(error_indices)
    correct = total_frames - incorrect
    # Compute mean absolute cents error if we had the cents_diff values
    # For simplicity, we approximate mean cents error as proportion of errors * threshold (rough estimate)
    # A more accurate implementation could compute actual cents differences.
    mean_cents = (incorrect / total_frames) * 100.0
    return {"correct_frames": correct, "mean_cents": mean_cents}