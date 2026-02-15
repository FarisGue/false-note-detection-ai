"""Utility functions to convert MIDI files into pitch timelines."""

import numpy as np
import pretty_midi
import logging

logger = logging.getLogger(__name__)


def parse_midi(
    midi_path: str, 
    target_sr: float = 100.0,
    instrument_index: int = 0,
    merge_instruments: bool = False
) -> np.ndarray:
    """Parse a MIDI file and produce a frequency timeline.

    Args:
        midi_path: Path to the MIDI file.
        target_sr: Target sampling rate in frames per second for the output timeline.
        instrument_index: Index of the instrument to use (0-based). If -1, uses all instruments.
        merge_instruments: If True and instrument_index is -1, merge all instruments into one timeline.

    Returns:
        A 1D numpy array of frequencies representing the reference pitch at each frame.
        For multiple instruments, returns the highest frequency at each frame.
        
    Raises:
        ValueError: If MIDI file cannot be parsed or is invalid.
    """
    try:
        midi = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        raise ValueError(f"Failed to parse MIDI file: {str(e)}")
    if not midi.instruments:
        logger.warning(f"No instruments found in MIDI file: {midi_path}")
        return np.array([])
    
    logger.info(f"MIDI file contains {len(midi.instruments)} instrument(s)")
    
    # Determine the total duration of the MIDI
    total_duration = midi.get_end_time()
    
    # Create timeline at target sampling rate
    num_frames = int(total_duration * target_sr) + 1
    timeline = np.zeros(num_frames)
    
    # Select instruments to process
    if instrument_index == -1 or merge_instruments:
        # Use all instruments
        instruments_to_process = midi.instruments
        logger.info(f"Processing {len(instruments_to_process)} instruments")
    else:
        # Use specific instrument
        if instrument_index >= len(midi.instruments):
            logger.warning(f"Instrument index {instrument_index} out of range. Using first instrument.")
            instrument_index = 0
        instruments_to_process = [midi.instruments[instrument_index]]
        logger.info(f"Processing instrument {instrument_index}: {instruments_to_process[0].name if hasattr(instruments_to_process[0], 'name') else 'Unknown'}")
    
    # Fill timeline with note frequencies
    for instrument in instruments_to_process:
        if not instrument.notes:
            logger.warning(f"Instrument has no notes")
            continue
            
        for note in instrument.notes:
            start_idx = int(note.start * target_sr)
            end_idx = min(int(note.end * target_sr), num_frames)
            if start_idx < num_frames:
                note_freq = pretty_midi.note_number_to_hz(note.pitch)
                # If merging, take the highest frequency at each frame
                if merge_instruments and len(instruments_to_process) > 1:
                    timeline[start_idx:end_idx] = np.maximum(
                        timeline[start_idx:end_idx],
                        note_freq
                    )
                else:
                    # For single instrument or first pass, fill with note frequency
                    # If multiple notes overlap, keep the last one (can be improved)
                    timeline[start_idx:end_idx] = note_freq
    
    # Count non-zero frames
    non_zero_frames = np.count_nonzero(timeline)
    logger.info(f"MIDI timeline: {non_zero_frames}/{num_frames} frames contain notes ({non_zero_frames/num_frames*100:.1f}%)")
    
    return timeline