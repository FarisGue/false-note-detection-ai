"""Functions to extract pitch from audio files."""

import numpy as np
import librosa


def extract_pitch(audio_path: str, target_sr: float = 100.0) -> np.ndarray:
    """Extract the fundamental frequency (f0) over time from an audio file.

    Args:
        audio_path: Path to the audio file.
        target_sr: Target sampling rate in frames per second for the output timeline.

    Returns:
        A 1D numpy array containing the estimated frequency in Hz for each frame at target_sr.
        Unvoiced frames are set to 0.0.
        
    Raises:
        ValueError: If audio file cannot be loaded or is invalid.
    """
    try:
        # Load the audio at native sampling rate
        y, sr = librosa.load(audio_path, sr=None, mono=True)
    except Exception as e:
        raise ValueError(f"Failed to load audio file: {str(e)}")
    
    # Validate audio data
    if len(y) == 0:
        raise ValueError("Audio file is empty")
    if sr < 1000:
        raise ValueError(f"Audio sampling rate too low: {sr} Hz. Minimum: 1000 Hz")
    
    # Calculate duration and validate
    duration = len(y) / sr
    if duration < 0.1:
        raise ValueError(f"Audio too short: {duration:.2f}s. Minimum: 0.1s")
    if duration > 600:  # 10 minutes max
        raise ValueError(f"Audio too long: {duration:.1f}s. Maximum: 600s (10 minutes)")
    
    # Use PYIN for pitch estimation (returns frequency or NaN for unvoiced)
    # hop_length controls the frame rate: smaller = more frames per second
    # We want approximately target_sr frames per second
    hop_length = max(1, int(sr / target_sr))  # Ensure hop_length >= 1
    
    try:
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            sr=sr,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            hop_length=hop_length,
        )
    except Exception as e:
        raise ValueError(f"Failed to extract pitch from audio: {str(e)}")
    
    # Replace NaN with 0.0 for unvoiced frames
    f0_clean = np.nan_to_num(f0, nan=0.0)
    
    # Post-processing: median filtering to remove glitches and smooth pitch track
    # This is a common technique in pitch tracking to reduce octave errors and noise
    from scipy import signal
    if len(f0_clean) > 3:
        # Apply median filter only to non-zero values to preserve silence
        non_zero_mask = f0_clean > 0.0
        if np.any(non_zero_mask):
            # Median filter with window size 3 (removes single-frame glitches)
            f0_filtered = signal.medfilt(f0_clean, kernel_size=3)
            # Only update non-zero values (preserve silence detection)
            f0_clean[non_zero_mask] = f0_filtered[non_zero_mask]
    
    # Remove octave errors: if pitch jumps by ~2x or 0.5x, it's likely an octave error
    # This is a common issue in pitch detection
    if len(f0_clean) > 1:
        non_zero_indices = np.where(f0_clean > 0.0)[0]
        if len(non_zero_indices) > 1:
            for i in range(1, len(non_zero_indices)):
                idx = non_zero_indices[i]
                prev_idx = non_zero_indices[i-1]
                ratio = f0_clean[idx] / f0_clean[prev_idx] if f0_clean[prev_idx] > 0 else 1.0
                
                # If ratio is close to 2.0 or 0.5, likely octave error
                if 1.8 < ratio < 2.2:
                    f0_clean[idx] = f0_clean[idx] / 2.0
                elif 0.45 < ratio < 0.55:
                    f0_clean[idx] = f0_clean[idx] * 2.0
    
    # Calculate actual frame rate from librosa output
    actual_frame_rate = sr / hop_length
    duration = len(y) / sr
    
    # Resample to exact target_sr if needed
    if abs(actual_frame_rate - target_sr) > 0.1:
        target_length = int(duration * target_sr) + 1
        if len(f0_clean) > 0:
            # Use linear interpolation to resample to target rate
            original_times = np.arange(len(f0_clean)) / actual_frame_rate
            target_times = np.arange(target_length) / target_sr
            f0_clean = np.interp(target_times, original_times, f0_clean)
        else:
            f0_clean = np.zeros(target_length)
    
    # Validate that we extracted some pitch data
    if np.all(f0_clean == 0.0):
        raise ValueError("No pitch detected in audio. Check if the file contains musical content.")
    
    return f0_clean