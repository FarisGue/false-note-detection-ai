"""Functions for detecting out-of-tune notes based on pitch deviation."""

import numpy as np


def detect_errors(
    f_audio: np.ndarray,
    f_ref: np.ndarray,
    threshold_cents: float = 40.0,
    ignore_silence: bool = True,
    smooth_window: int = 3,
    min_error_frames: int = 3,
) -> np.ndarray:
    """Identify frames where the pitch deviates beyond a threshold in cents.

    This function compares the detected pitch from a performance to the
    reference pitch at each aligned frame.  Cents differences are
    median–smoothed to suppress outliers, then a threshold is applied to
    determine erroneous frames.  Very short bursts of large deviations
    (e.g. single–frame glitches) are suppressed via the ``min_error_frames``
    parameter which requires a minimum run length before flagging a segment as
    incorrect.  An adaptive threshold can be invoked by passing a non‑positive
    value for ``threshold_cents``.

    Args:
        f_audio: Array of detected pitch frequencies (Hz) from the performance.
        f_ref: Array of reference frequencies (Hz).
        threshold_cents: Threshold in cents beyond which a frame is considered incorrect.  If
            <= 0, a dynamic threshold based on the median absolute deviation is used.
        ignore_silence: If True, ignore frames where either audio or reference is silent (0 Hz).
        smooth_window: Window size for median filtering of cents differences (reduces noise).
        min_error_frames: Minimum number of consecutive error frames required to consider a
            deviation as a false note.  Shorter runs are ignored as likely glitches.

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
    
    # Dynamically adjust the threshold if requested.  A non‑positive threshold
    # (<= 0) signals automatic tuning based on the distribution of the cents
    # differences.  The median absolute deviation is used as a robust measure
    # of typical intonation variance.  A small constant (10¢) is added to avoid
    # flagging every small fluctuation.  The resulting threshold is clipped
    # between 10 and 200 cents to avoid unrealistic extremes.
    dynamic_threshold = threshold_cents
    if threshold_cents is None or threshold_cents <= 0:
        # Compute absolute deviations on valid frames
        abs_cents = np.abs(cents_diff[mask])
        if abs_cents.size > 0:
            median_dev = float(np.median(abs_cents))
            dynamic_threshold = median_dev + 10.0
            dynamic_threshold = max(10.0, min(dynamic_threshold, 200.0))
        else:
            dynamic_threshold = 40.0  # Fallback
    
    # Identify error indices where deviation exceeds the (possibly dynamic) threshold
    # Only consider frames where we have valid pitch data
    if ignore_silence:
        raw_error_mask = mask & (np.abs(cents_diff) > dynamic_threshold)
    else:
        # Also flag silence mismatches (one is silent, other is not)
        silence_mismatch = (f_audio == 0.0) != (f_ref == 0.0)
        pitch_error = mask & (np.abs(cents_diff) > dynamic_threshold)
        raw_error_mask = pitch_error | silence_mismatch

    # Convert to indices and filter out runs shorter than ``min_error_frames``
    raw_error_indices = np.where(raw_error_mask)[0]
    if len(raw_error_indices) == 0:
        return np.array([], dtype=int)

    if min_error_frames <= 1:
        # No run–length filtering requested
        return raw_error_indices

    # Group consecutive error indices into runs
    runs = []
    start = raw_error_indices[0]
    prev = start
    count = 1
    for idx in raw_error_indices[1:]:
        if idx == prev + 1:
            # Same run
            count += 1
        else:
            runs.append((start, prev, count))
            start = idx
            count = 1
        prev = idx
    runs.append((start, prev, count))

    # Collect indices for runs that meet the minimum length
    filtered_indices = []
    for run_start, run_end, run_len in runs:
        if run_len >= min_error_frames:
            filtered_indices.extend(range(run_start, run_end + 1))

    return np.array(filtered_indices, dtype=int)