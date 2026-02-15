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
    """
    # Load the audio at native sampling rate
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    
    # Use PYIN for pitch estimation (returns frequency or NaN for unvoiced)
    # hop_length controls the frame rate: smaller = more frames per second
    # We want approximately target_sr frames per second
    hop_length = int(sr / target_sr)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        sr=sr,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        hop_length=hop_length,
    )
    # Replace NaN with 0.0 for unvoiced frames
    f0_clean = np.nan_to_num(f0, nan=0.0)
    
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
    
    return f0_clean