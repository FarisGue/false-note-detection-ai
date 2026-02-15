"""Functions to compute scoring metrics for the false note detection."""

import numpy as np


def compute_score(f_audio: np.ndarray, f_ref: np.ndarray, error_indices: np.ndarray, total_frames: int) -> dict:
    """Compute summary statistics from the detected error indices and actual pitch differences.

    Args:
        f_audio: Array of detected pitch frequencies (Hz) from the performance.
        f_ref: Array of reference frequencies (Hz).
        error_indices: Indices of frames where false notes were detected.
        total_frames: Total number of frames considered in the analysis.

    Returns:
        A dictionary containing the number of correct frames and the mean absolute cents error.
    """
    # Number of incorrect frames
    incorrect = len(error_indices)
    correct = total_frames - incorrect
    
    # Compute actual cents differences for all frames where both have non-zero values
    cents_diff = np.zeros_like(f_audio)
    mask = (f_audio > 0.0) & (f_ref > 0.0)
    
    # Calculate cents difference: 1200 * log2(f_audio / f_ref)
    cents_diff[mask] = 1200.0 * np.log2(f_audio[mask] / f_ref[mask])
    
    # Compute mean absolute cents error over all valid frames
    if np.any(mask):
        mean_cents = np.mean(np.abs(cents_diff[mask]))
    else:
        mean_cents = 0.0
    
    return {"correct_frames": correct, "mean_cents": mean_cents}