"""Endpoints for uploading audio and reference files for analysis."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.pitch_extractor import extract_pitch
from ..services.midi_processor import parse_midi
from ..services.error_detector import detect_errors
from ..services.scoring import compute_score
from ..models.analysis_result import AnalysisResult

import numpy as np
import tempfile
import os

router = APIRouter()


@router.post("/", response_model=AnalysisResult)
async def upload_files(
    audio: UploadFile = File(..., description="Audio file of the performance (e.g. WAV, MP3)"),
    reference: UploadFile = File(..., description="Reference file (MIDI) representing the correct notes"),
):
    """Receive an audio file and a reference MIDI file, perform false note analysis and return the result."""
    try:
        # Save uploaded files to temporary locations
        with tempfile.NamedTemporaryFile(delete=False) as audio_tmp:
            audio_data = await audio.read()
            audio_tmp.write(audio_data)
            audio_path = audio_tmp.name

        with tempfile.NamedTemporaryFile(delete=False) as ref_tmp:
            ref_data = await reference.read()
            ref_tmp.write(ref_data)
            ref_path = ref_tmp.name

        # Extract pitch from audio and reference
        f_audio = extract_pitch(audio_path)
        f_ref = parse_midi(ref_path)

        # Align sequences by truncating to the shortest length for this basic version
        min_len = min(len(f_audio), len(f_ref))
        if min_len == 0:
            raise ValueError("Audio or reference file did not produce pitch data.")
        f_audio = f_audio[:min_len]
        f_ref = f_ref[:min_len]

        # Detect false notes
        error_indices = detect_errors(f_audio, f_ref)
        # Compute score
        score = compute_score(error_indices, total_frames=min_len)

        result = AnalysisResult(
            total_frames=min_len,
            correct_frames=score["correct_frames"],
            mean_cents=score["mean_cents"],
            error_indices=error_indices.tolist(),
        )
        return result

    except Exception as exc:
        # Propagate errors as HTTP exceptions for the client
        raise HTTPException(status_code=400, detail=str(exc))

    finally:
        # Clean up temporary files
        try:
            os.remove(audio_path)
        except Exception:
            pass
        try:
            os.remove(ref_path)
        except Exception:
            pass