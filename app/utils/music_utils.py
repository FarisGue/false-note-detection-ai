"""Utilities for music notation and visualization."""

import numpy as np


def hz_to_note_name(frequency: float) -> str:
    """Convert frequency in Hz to note name (e.g., 'A4', 'C#5').
    
    Args:
        frequency: Frequency in Hz.
        
    Returns:
        Note name as string (e.g., 'A4', 'C#5', 'Bb3').
    """
    if frequency <= 0:
        return ""
    
    # A4 = 440 Hz is the reference
    A4 = 440.0
    
    # Calculate semitones from A4
    semitones = 12 * np.log2(frequency / A4)
    
    # Round to nearest semitone
    note_number = int(round(semitones))
    
    # Note names in order starting from A
    note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    
    # Calculate octave (A4 is note 0, so A4 = octave 4)
    octave = 4 + (note_number // 12)
    note_index = note_number % 12
    
    # Handle negative note numbers
    if note_index < 0:
        note_index += 12
        octave -= 1
    
    note_name = note_names[note_index]
    
    # Use flat notation for some notes (optional, can be customized)
    flat_notes = {'A#': 'Bb', 'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab'}
    if note_name in flat_notes:
        note_name = flat_notes[note_name]
    
    return f"{note_name}{octave}"


def hz_to_midi_note(frequency: float) -> int:
    """Convert frequency in Hz to MIDI note number.
    
    Args:
        frequency: Frequency in Hz.
        
    Returns:
        MIDI note number (0-127), or -1 if frequency is invalid.
    """
    if frequency <= 0:
        return -1
    
    # MIDI note 69 = A4 = 440 Hz
    midi_note = 69 + 12 * np.log2(frequency / 440.0)
    return int(round(midi_note))


def midi_note_to_hz(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz.
    
    Args:
        midi_note: MIDI note number (0-127).
        
    Returns:
        Frequency in Hz.
    """
    # MIDI note 69 = A4 = 440 Hz
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


def create_note_timeline(frequencies: np.ndarray, frame_rate: float = 100.0) -> list:
    """Create a timeline of notes from frequency array.
    
    Args:
        frequencies: Array of frequencies in Hz.
        frame_rate: Frames per second.
        
    Returns:
        List of tuples (start_time, end_time, note_name, frequency).
    """
    notes = []
    current_note = None
    current_start = None
    current_freq = None
    
    for i, freq in enumerate(frequencies):
        time = i / frame_rate
        
        if freq > 0:
            note_name = hz_to_note_name(freq)
            
            if current_note == note_name and current_freq is not None:
                # Same note continues
                current_freq = freq
            else:
                # New note or note change
                if current_note is not None:
                    # Save previous note
                    notes.append((current_start, time, current_note, current_freq))
                
                # Start new note
                current_note = note_name
                current_start = time
                current_freq = freq
        else:
            # Silence
            if current_note is not None:
                # End current note
                notes.append((current_start, time, current_note, current_freq))
                current_note = None
                current_start = None
                current_freq = None
    
    # Add final note if exists
    if current_note is not None:
        final_time = len(frequencies) / frame_rate
        notes.append((current_start, final_time, current_note, current_freq))
    
    return notes

