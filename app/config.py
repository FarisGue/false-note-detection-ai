"""Configuration settings for the False Note Detection API."""

import os
from typing import List

# Audio processing settings
TARGET_SAMPLING_RATE: float = float(os.getenv("TARGET_SR", "100.0"))  # frames per second
AUDIO_FMIN: str = os.getenv("AUDIO_FMIN", "C2")  # Minimum frequency for pitch detection
AUDIO_FMAX: str = os.getenv("AUDIO_FMAX", "C7")  # Maximum frequency for pitch detection

# Error detection settings
DEFAULT_THRESHOLD_CENTS: float = float(os.getenv("DEFAULT_THRESHOLD_CENTS", "40.0"))
MIN_THRESHOLD_CENTS: float = 0.0
MAX_THRESHOLD_CENTS: float = 200.0
DEFAULT_IGNORE_SILENCE: bool = os.getenv("DEFAULT_IGNORE_SILENCE", "true").lower() == "true"

# MIDI processing settings
DEFAULT_MIDI_INSTRUMENT_INDEX: int = int(os.getenv("DEFAULT_MIDI_INSTRUMENT_INDEX", "0"))
MERGE_MIDI_INSTRUMENTS: bool = os.getenv("MERGE_MIDI_INSTRUMENTS", "false").lower() == "true"

# File upload settings
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
ALLOWED_AUDIO_EXTENSIONS: List[str] = ['.wav', '.mp3', '.flac', '.ogg', '.m4a']
ALLOWED_MIDI_EXTENSIONS: List[str] = ['.mid', '.midi']

# API settings
API_TITLE: str = "False Note Detection API"
API_VERSION: str = "1.0.0"
API_DESCRIPTION: str = "API for detecting false notes in music performances."

# Logging settings
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

