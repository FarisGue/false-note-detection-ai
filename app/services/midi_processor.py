"""Utility functions to convert MIDI files into pitch timelines."""

import numpy as np
import pretty_midi


def parse_midi(midi_path: str) -> np.ndarray:
    """Parse a MIDI file and produce a frequency timeline.

    Args:
        midi_path: Path to the MIDI file.

    Returns:
        A 1D numpy array of frequencies representing the reference pitch at each frame.
    """
    midi = pretty_midi.PrettyMIDI(midi_path)
    if not midi.instruments:
        return np.array([])
    # Use the first instrument as reference
    instrument = midi.instruments[0]
    # Determine the total duration of the MIDI
    total_duration = midi.get_end_time()
    # Define a sampling rate for the timeline (e.g. 100 frames per second)
    sr = 100
    num_frames = int(total_duration * sr) + 1
    timeline = np.zeros(num_frames)
    for note in instrument.notes:
        start_idx = int(note.start * sr)
        end_idx = int(note.end * sr)
        # Fill the interval with the note frequency
        timeline[start_idx:end_idx] = pretty_midi.note_number_to_hz(note.pitch)
    return timeline