"""Service to generate practice recommendations via OpenRouter.

This module contains a helper function that uses the OpenRouter API to
generate natural language feedback based on the results of a false note
analysis. It builds a brief summary of the analysis (accuracy, number of
errors, mean pitch deviation and a few example error timestamps) and sends
that summary to a large language model hosted on OpenRouter. The model
returns a set of practice recommendations which are returned as a plain
string. If no API key is configured or the request fails, the function
returns ``None`` and logs the error.

You should avoid exposing the API key or detailed error information in
responses. Only return user‑facing messages when the call succeeds.
"""

from __future__ import annotations

import json
import logging
from typing import Optional, List

import requests

from ..config import (
    OPENROUTE_API_KEY,
    OPENROUTE_API_URL,
    DEEPSEEK_MODEL,
)


logger = logging.getLogger(__name__)


def _format_time(seconds: float) -> str:
    """Format a float number of seconds into a mm:ss format for readability."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:d}:{secs:04.1f}"


def generate_recommendations(
    *,
    accuracy_percent: float,
    incorrect_frames: int,
    total_frames: int,
    mean_cents: float,
    max_cents: float,
    error_indices: List[int],
    duration_seconds: float,
    threshold_cents: float,
    sample_rate: float = 100.0,
    max_error_times: int = 5,
) -> Optional[str]:
    """Generate practice recommendations based on analysis metrics.

    This function constructs a summary prompt describing the results of the
    false note analysis and sends it to the OpenRouter chat completions API.
    It returns the model's response as a string or ``None`` if the request
    could not be completed.

    Parameters
    ----------
    accuracy_percent: float
        The accuracy percentage of the performance (0-100).
    incorrect_frames: int
        The number of frames where the pitch deviated beyond the threshold.
    total_frames: int
        The total number of frames analysed.
    mean_cents: float
        The mean absolute pitch deviation in cents.
    max_cents: float
        The maximum absolute pitch deviation in cents.
    error_indices: List[int]
        Frame indices where errors were detected.
    duration_seconds: float
        Total duration of the analysed performance in seconds.
    threshold_cents: float
        The threshold used for error detection in cents.
    sample_rate: float, optional
        The frame rate (frames per second) of the pitch analysis. Default 100.0.
    max_error_times: int, optional
        Maximum number of error timestamps to include in the summary. Default 5.

    Returns
    -------
    Optional[str]
        A string containing the model's recommendations, or ``None`` if the
        request failed or no API key is configured.
    """
    # Skip if API key is not provided
    if not OPENROUTE_API_KEY:
        logger.info("Recommendations disabled: no OpenRouter API key configured.")
        return None

    # Build a concise summary of the analysis
    error_rate = (incorrect_frames / total_frames * 100.0) if total_frames > 0 else 0.0
    summary_lines = [
        f"Performance accuracy: {accuracy_percent:.2f}% (error rate: {error_rate:.2f}%).",
        f"Number of incorrect frames: {incorrect_frames} out of {total_frames} frames.",
        f"Mean pitch deviation: {mean_cents:.2f} cents (max {max_cents:.2f} cents).",
        f"Threshold used for error detection: {threshold_cents:.2f} cents.",
        f"Total duration: {duration_seconds:.2f} seconds."
    ]

    # Include a few example error timestamps
    if error_indices:
        # Convert first few error indices to timestamps
        times = [idx / sample_rate for idx in error_indices[:max_error_times]]
        formatted = ", ".join(_format_time(t) for t in times)
        summary_lines.append(
            f"Notable pitch deviations occurred at approximately: {formatted}."
        )
    summary = "\n".join(summary_lines)

    # Compose messages for the chat API
    system_prompt = (
        "You are a warm, encouraging, and experienced music teacher with years of experience "
        "helping students improve their musical performance. You have a genuine passion for music "
        "education and always provide constructive, personalized feedback. Your teaching style is "
        "supportive and empathetic - you understand that learning music takes time and practice. "
        "You speak in a friendly, conversational tone, as if you're having a one-on-one lesson "
        "with your student. You use encouraging language and always find something positive to "
        "acknowledge before offering suggestions for improvement. You provide specific, actionable "
        "advice that feels personal and tailored to each student's needs."
    )
    user_prompt = (
        "Bonjour ! J'ai enregistré ma performance et voici les résultats de l'analyse :\n\n"
        f"{summary}\n\n"
        "Pouvez-vous me donner vos conseils de professeur de musique ? J'aimerais savoir comment "
        "m'améliorer. Parlez-moi comme vous le feriez à un élève lors d'un cours particulier - "
        "soyez encourageant, spécifique et donnez-moi 3-5 suggestions pratiques pour progresser."
    )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # Increased token limit for more detailed, personalized responses
        # Higher temperature for more natural, human-like language
        "max_tokens": 800,
        "temperature": 0.8,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTE_API_KEY}",
        "Content-Type": "application/json",
        # Optional: identify our app for OpenRouter leaderboards if desired. Not
        # required for basic usage. Uncomment and set if you want to track usage.
        # "HTTP-Referer": "https://your-app-url.example",  # optional
        # "X-Title": "False Note Detection AI",  # optional
    }

    try:
        response = requests.post(
            OPENROUTE_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        # OpenRouter follows OpenAI's response format: choices[0].message.content
        choices = data.get("choices")
        if choices and isinstance(choices, list):
            message = choices[0].get("message") or {}
            content = message.get("content")
            if content:
                # Trim leading/trailing whitespace
                return content.strip()
        logger.warning("OpenRouter response missing expected fields: %s", data)
        return None
    except Exception as exc:
        # Log error but do not propagate to caller to avoid failing the entire
        # analysis. We return None to indicate recommendations could not be
        # generated.
        logger.error(f"Failed to generate recommendations: {exc}")
        return None