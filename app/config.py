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

# DTW alignment settings
MAX_DTW_LENGTH: int = int(os.getenv("MAX_DTW_LENGTH", "60000"))  # Maximum frames for DTW (~10 min at 100 fps)

# File upload settings
MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_AUDIO_DURATION_SECONDS: float = float(os.getenv("MAX_AUDIO_DURATION_SECONDS", "600"))  # 10 minutes
MIN_AUDIO_DURATION_SECONDS: float = float(os.getenv("MIN_AUDIO_DURATION_SECONDS", "0.1"))  # 100ms
# Allow a wider range of audio extensions. In addition to common formats like
# WAV, MP3, FLAC and OGG we include `.m4a`, `.aac`, `.mpga` and `.mpeg` to
# accommodate audio streams that may not use the expected extension. These
# values are only used as a first pass; if ``UploadFile.content_type`` reports
# an audio MIME type the upload will still be accepted even when the
# extension is not explicitly listed (see routes/upload.py for details).
ALLOWED_AUDIO_EXTENSIONS: List[str] = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.mpga', '.mpeg']
ALLOWED_MIDI_EXTENSIONS: List[str] = ['.mid', '.midi']
MAX_ERROR_INDICES_RETURNED: int = int(os.getenv("MAX_ERROR_INDICES_RETURNED", "10000"))  # Limit response size

# API settings
API_TITLE: str = "False Note Detection API"
API_VERSION: str = "1.0.0"
API_DESCRIPTION: str = "API for detecting false notes in music performances."

# Logging settings
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

# -----------------------------------------------------------------------------
# OpenRouter / Recommendations configuration
#
# The backend can optionally generate practice recommendations by sending the
# analysis results to a large language model hosted on OpenRouter. To enable
# this feature you must supply an API key and endpoint in your environment
# variables. If `OPENROUTE_API_KEY` is missing or empty the recommendation
# service will be disabled and no external requests will be made.
#
# OPENROUTE_API_KEY: Secret token used to authenticate with OpenRouter. Keep
# this value private; do not log or expose it in responses. If unset or empty
# recommendations are skipped.
# OPENROUTE_API_URL: Base URL for the OpenRouter chat completions endpoint.
# Defaults to the OpenRouter v1 chat completions API. You can override this
# value to point to a different proxy or test server.
# DEEPSEEK_MODEL: Name of the model to use for generating recommendations.
# The default 'deepseek/deepseek-chat' is a light, free model suitable for
# quick feedback, but you can substitute any compatible model available via
# OpenRouter.
# ENABLE_RECOMMENDATIONS: Optional flag to globally enable or disable
# recommendation generation. Set to 'true' or '1' to force on, 'false' or '0'
# to force off. If unspecified, recommendations are enabled only when a
# valid API key is present.

OPENROUTE_API_KEY: str = os.getenv("OPENROUTE_API_KEY", "")
OPENROUTE_API_URL: str = os.getenv(
    "OPENROUTE_API_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)
DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek/deepseek-chat")
ENABLE_RECOMMENDATIONS: bool = (
    bool(os.getenv("ENABLE_RECOMMENDATIONS"))
    and os.getenv("ENABLE_RECOMMENDATIONS").lower() in {"1", "true", "yes"}
)

