"""Functions to extract pitch from audio files."""

import numpy as np
import librosa


def extract_pitch(audio_path: str) -> np.ndarray:
    """Extract the fundamental frequency (f0) over time from an audio file.

    Args:
        audio_path: Path to the audio file.

    Returns:
        A 1D numpy array containing the estimated frequency in Hz for each frame. Unvoiced frames are set to 0.0.
    """
    # Load the audio at native sampling rate
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    # Use PYIN for pitch estimation (returns frequency or NaN for unvoiced)
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        sr=sr,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
    )
    # Replace NaN with 0.0 for unvoiced frames
    f0_clean = np.nan_to_num(f0, nan=0.0)
    return f0_clean