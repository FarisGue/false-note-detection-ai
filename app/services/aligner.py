"""Alignment utilities using Dynamic Time Warping (DTW)."""

from fastdtw import fastdtw
import numpy as np
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Import MAX_DTW_LENGTH from config
from ..config import MAX_DTW_LENGTH


def align_sequences(seq1: np.ndarray, seq2: np.ndarray):
    """Align two sequences using FastDTW and return the distance and alignment path.

    Args:
        seq1: First sequence (e.g. estimated pitch timeline).
        seq2: Second sequence (e.g. reference pitch timeline).

    Returns:
        A tuple of (distance, path) where path is a list of index pairs.
        
    Raises:
        ValueError: If sequences are too long for DTW.
    """
    # Check sequence lengths
    if len(seq1) > MAX_DTW_LENGTH or len(seq2) > MAX_DTW_LENGTH:
        raise ValueError(
            f"Sequences too long for DTW alignment (max {MAX_DTW_LENGTH} frames). "
            f"Audio: {len(seq1)}, MIDI: {len(seq2)}. Consider using shorter files."
        )
    
    try:
        distance, path = fastdtw(seq1, seq2)
        return distance, path
    except MemoryError:
        raise ValueError("Not enough memory for DTW alignment. Try shorter audio files.")
    except Exception as e:
        raise ValueError(f"DTW alignment failed: {str(e)}")


def align_and_warp(seq1: np.ndarray, seq2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Align two sequences using DTW and return warped sequences of equal length.
    
    For very long sequences, uses a simple truncation fallback to prevent timeout.

    Args:
        seq1: First sequence (e.g. estimated pitch timeline from audio).
        seq2: Second sequence (e.g. reference pitch timeline from MIDI).

    Returns:
        A tuple of (aligned_seq1, aligned_seq2) with the same length.
    """
    # Validate inputs
    if len(seq1) == 0 or len(seq2) == 0:
        raise ValueError("Cannot align empty sequences")
    
    # For very similar lengths, use simple truncation (faster)
    length_ratio = max(len(seq1), len(seq2)) / min(len(seq1), len(seq2))
    if length_ratio < 1.1:  # Less than 10% difference
        logger.info("Sequences have similar lengths, using simple alignment")
        min_len = min(len(seq1), len(seq2))
        return seq1[:min_len], seq2[:min_len]
    
    # Check if sequences are too long
    if len(seq1) > MAX_DTW_LENGTH or len(seq2) > MAX_DTW_LENGTH:
        logger.warning(
            f"Sequences too long for DTW ({len(seq1)}, {len(seq2)}), "
            f"using simple truncation to {MAX_DTW_LENGTH} frames"
        )
        min_len = min(len(seq1), len(seq2), MAX_DTW_LENGTH)
        return seq1[:min_len], seq2[:min_len]
    
    try:
        # Compute DTW alignment
        logger.info(f"Computing DTW alignment for sequences of length {len(seq1)} and {len(seq2)}")
        distance, path = fastdtw(seq1, seq2)
        logger.info(f"DTW alignment complete, distance: {distance:.2f}, path length: {len(path)}")
    except MemoryError:
        logger.warning("DTW failed due to memory, using simple truncation")
        min_len = min(len(seq1), len(seq2))
        return seq1[:min_len], seq2[:min_len]
    except Exception as e:
        logger.warning(f"DTW alignment failed: {e}, using simple truncation")
        min_len = min(len(seq1), len(seq2))
        return seq1[:min_len], seq2[:min_len]
    
    # Create aligned sequences by mapping indices according to the path
    aligned_length = len(path)
    aligned_seq1 = np.zeros(aligned_length)
    aligned_seq2 = np.zeros(aligned_length)
    
    for i, (idx1, idx2) in enumerate(path):
        if idx1 < len(seq1):
            aligned_seq1[i] = seq1[idx1]
        if idx2 < len(seq2):
            aligned_seq2[i] = seq2[idx2]
    
    return aligned_seq1, aligned_seq2