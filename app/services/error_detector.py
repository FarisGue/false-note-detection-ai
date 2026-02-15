"""Functions for detecting out-of-tune notes based on pitch deviation."""

import numpy as np


def detect_errors(f_audio: np.ndarray, f_ref: np.ndarray, threshold_cents: float = 40.0) -> np.ndarray:
    """Identify frames where the pitch deviates beyond a threshold in cents.

    Args:
        f_audio: Array of detected pitch frequencies (Hz) from the performance.
        f_ref: Array of reference frequencies (Hz).
        threshold_cents: Threshold in cents beyond which a frame is considered incorrect.

    Returns:
        Indices of frames where the absolute pitch deviation exceeds the threshold.
    """
    # Initialize array of differences in cents
    cents_diff = np.zeros_like(f_audio)
    # Compute only where both sequences have positive (non-zero) values
    mask = (f_audio > 0.0) & (f_ref > 0.0)
    # Avoid division by zero; compute cents difference
    cents_diff[mask] = 1200.0 * np.log2(f_audio[mask] / f_ref[mask])
    # Identify error indices
    error_indices = np.where(np.abs(cents_diff) > threshold_cents)[0]
    return error_indices