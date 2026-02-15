"""Alignment utilities using Dynamic Time Warping (DTW)."""

from fastdtw import fastdtw
import numpy as np
from typing import Tuple


def align_sequences(seq1: np.ndarray, seq2: np.ndarray):
    """Align two sequences using FastDTW and return the distance and alignment path.

    Args:
        seq1: First sequence (e.g. estimated pitch timeline).
        seq2: Second sequence (e.g. reference pitch timeline).

    Returns:
        A tuple of (distance, path) where path is a list of index pairs.
    """
    distance, path = fastdtw(seq1, seq2)
    return distance, path


def align_and_warp(seq1: np.ndarray, seq2: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Align two sequences using DTW and return warped sequences of equal length.

    Args:
        seq1: First sequence (e.g. estimated pitch timeline from audio).
        seq2: Second sequence (e.g. reference pitch timeline from MIDI).

    Returns:
        A tuple of (aligned_seq1, aligned_seq2) with the same length.
    """
    # Compute DTW alignment
    distance, path = fastdtw(seq1, seq2)
    
    # Convert path to numpy array for easier manipulation
    path_array = np.array(path)
    
    # Create aligned sequences by mapping indices according to the path
    # Use the length of the path as the aligned sequence length
    aligned_length = len(path)
    aligned_seq1 = np.zeros(aligned_length)
    aligned_seq2 = np.zeros(aligned_length)
    
    for i, (idx1, idx2) in enumerate(path):
        if idx1 < len(seq1):
            aligned_seq1[i] = seq1[idx1]
        if idx2 < len(seq2):
            aligned_seq2[i] = seq2[idx2]
    
    return aligned_seq1, aligned_seq2