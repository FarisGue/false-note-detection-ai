"""Functions for detecting out-of-tune notes based on pitch deviation."""

import numpy as np


def detect_errors(
    f_audio: np.ndarray, 
    f_ref: np.ndarray, 
    threshold_cents: float = 40.0,
    ignore_silence: bool = True,
    smooth_window: int = 3
) -> np.ndarray:
    """Identify frames where the pitch deviates beyond a threshold in cents.

    Uses median filtering on cents differences to reduce false positives from
    pitch tracking glitches, a common technique in audio analysis.

    Args:
        f_audio: Array of detected pitch frequencies (Hz) from the performance.
        f_ref: Array of reference frequencies (Hz).
        threshold_cents: Threshold in cents beyond which a frame is considered incorrect.
        ignore_silence: If True, ignore frames where either audio or reference is silent (0 Hz).
        smooth_window: Window size for median filtering of cents differences (reduces noise).

    Returns:
        Indices of frames where the absolute pitch deviation exceeds the threshold.
    """
    # Initialize array of differences in cents
    cents_diff = np.zeros_like(f_audio)
    
    # Compute only where both sequences have positive (non-zero) values
    # This handles silence: if either is 0, we don't compare
    mask = (f_audio > 0.0) & (f_ref > 0.0)
    
    if not np.any(mask):
        # No valid frames to compare
        return np.array([], dtype=int)
    
    # Avoid division by zero; compute cents difference
    # Formula: cents = 1200 * log2(f1 / f2)
    cents_diff[mask] = 1200.0 * np.log2(f_audio[mask] / f_ref[mask])
    
    # Apply median filtering to cents differences to reduce noise and glitches
    # This is a common technique to improve robustness of error detection
    if smooth_window > 1 and len(cents_diff) > smooth_window:
        from scipy import signal
        # Only smooth where we have valid data
        cents_smoothed = signal.medfilt(cents_diff, kernel_size=smooth_window)
        # Update only the masked regions
        cents_diff[mask] = cents_smoothed[mask]
    
    # Identify error indices where deviation exceeds threshold
    # Only consider frames where we have valid pitch data
    if ignore_silence:
        error_mask = mask & (np.abs(cents_diff) > threshold_cents)
    else:
        # Also flag silence mismatches (one is silent, other is not)
        silence_mismatch = (f_audio == 0.0) != (f_ref == 0.0)
        pitch_error = mask & (np.abs(cents_diff) > threshold_cents)
        error_mask = pitch_error | silence_mismatch
    
    error_indices = np.where(error_mask)[0]
    return error_indices