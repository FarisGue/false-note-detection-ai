"""Alignment utilities using Dynamic Time Warping (DTW)."""

from fastdtw import fastdtw
import numpy as np


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