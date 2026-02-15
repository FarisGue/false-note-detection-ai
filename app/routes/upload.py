"""Endpoints for uploading audio and reference files for analysis."""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from ..services.pitch_extractor import extract_pitch
from ..services.midi_processor import parse_midi
from ..services.error_detector import detect_errors
from ..services.scoring import compute_score
from ..services.aligner import align_and_warp
from ..models.analysis_result import AnalysisResult
from ..services.recommender import generate_recommendations

import numpy as np
import tempfile
import os
import logging
import os
from ..config import (
    TARGET_SAMPLING_RATE,
    DEFAULT_THRESHOLD_CENTS,
    DEFAULT_IGNORE_SILENCE,
    ALLOWED_AUDIO_EXTENSIONS,
    ALLOWED_MIDI_EXTENSIONS,
    MAX_FILE_SIZE_MB
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=AnalysisResult)
async def upload_files(
    audio: UploadFile = File(..., description="Audio file of the performance (e.g. WAV, MP3)"),
    reference: UploadFile = File(..., description="Reference file (MIDI) representing the correct notes"),
    threshold_cents: float = Query(
        DEFAULT_THRESHOLD_CENTS, 
        ge=0.0, 
        le=200.0, 
        description="Threshold in cents for error detection (0-200)"
    ),
    ignore_silence: bool = Query(
        DEFAULT_IGNORE_SILENCE, 
        description="Ignore frames where either audio or reference is silent"
    ),
    generate_recommendations_flag: bool = Query(
        False,
        description="Generate practice recommendations using a language model"
    ),
):
    """Receive an audio file and a reference MIDI file, perform false note analysis and return the result."""
    audio_path = None
    ref_path = None
    try:
        # ---------------------------------------------------------------------------
        # Validate file types
        #
        # Historically, this API relied solely on file extensions to determine
        # whether an uploaded file was a valid audio or MIDI asset. This rigid
        # approach caused confusion when users converted an audio file to a
        # different container or uploaded a data‑URI (e.g. a MIME string
        # starting with ``data:audio/mp3``). In those cases the extension might
        # be missing or unrecognised, resulting in a spurious "Unsupported audio
        # format" error or silent mis‑processing.
        #
        # To make the API more robust we now also inspect the MIME type reported
        # by the ``UploadFile``. If the file extension is not in the allowlist
        # but the ``content_type`` indicates an audio payload (e.g. "audio/mp3",
        # "audio/mpeg"), we still accept the file. The same logic applies to
        # MIDI files ("audio/midi", etc.).
        audio_ext = os.path.splitext(audio.filename or "")[1].lower()
        ref_ext = os.path.splitext(reference.filename or "")[1].lower()

        audio_mime = (audio.content_type or "").lower()
        ref_mime = (reference.content_type or "").lower()

        # Check audio: accept if extension allowed or mime indicates audio
        if audio_ext not in ALLOWED_AUDIO_EXTENSIONS:
            # Fallback: allow if content_type starts with 'audio/'
            if not audio_mime.startswith("audio/"):
                raise ValueError(
                    f"Unsupported audio format: {audio_ext or audio_mime}. "
                    f"Supported extensions: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
                )

        # Check MIDI: accept if extension allowed or mime indicates midi
        if ref_ext not in ALLOWED_MIDI_EXTENSIONS:
            midi_mime_types = {"audio/mid", "audio/midi", "audio/x-midi", "application/x-midi"}
            if ref_mime not in midi_mime_types:
                raise ValueError(
                    f"Unsupported MIDI format: {ref_ext or ref_mime}. "
                    f"Supported extensions: {', '.join(ALLOWED_MIDI_EXTENSIONS)}"
                )
        
        # Check file sizes
        audio_size_mb = len(await audio.read()) / (1024 * 1024)
        await audio.seek(0)  # Reset file pointer
        if audio_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"Audio file too large: {audio_size_mb:.2f}MB. Maximum: {MAX_FILE_SIZE_MB}MB")
        
        ref_size_mb = len(await reference.read()) / (1024 * 1024)
        await reference.seek(0)  # Reset file pointer
        if ref_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"MIDI file too large: {ref_size_mb:.2f}MB. Maximum: {MAX_FILE_SIZE_MB}MB")
        
        # Save uploaded files to temporary locations
        # When reading the uploaded audio we handle two cases:
        # 1. Binary audio (standard uploads) – write bytes directly to temp file.
        # 2. data: URI (base64 encoded) – decode the payload and write decoded bytes.
        #
        # This allows clients to send a base64 encoded audio string (for example
        # copied from a web canvas or generated in JavaScript) and still have it
        # processed correctly by the API. Without this logic the server would
        # interpret the string as raw bytes and attempt to decode it as an audio
        # file, which inevitably fails and yields false pitch values.
        with tempfile.NamedTemporaryFile(delete=False, suffix=audio_ext) as audio_tmp:
            audio_data = await audio.read()
            # Try to detect and decode a base64 data URI
            decoded_written = False
            try:
                # Look for the ';base64,' marker in the first ~200 bytes to
                # minimise scanning overhead. This marker separates the MIME
                # declaration from the base64 payload in data URIs like
                # "data:audio/mp3;base64,<payload>".
                marker = b';base64,'
                idx = audio_data.find(marker)
                if 0 <= idx <= 200:
                    # Split on the marker
                    header = audio_data[:idx].decode('utf-8', errors='ignore')
                    b64_part = audio_data[idx + len(marker):].decode('utf-8', errors='ignore')
                    import base64
                    decoded_bytes = base64.b64decode(b64_part)
                    audio_tmp.write(decoded_bytes)
                    decoded_written = True
            except Exception:
                # Fall back to normal write on any error
                decoded_written = False
            if not decoded_written:
                audio_tmp.write(audio_data)
            audio_path = audio_tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=ref_ext) as ref_tmp:
            ref_data = await reference.read()
            decoded_written = False
            try:
                marker = b';base64,'
                idx = ref_data.find(marker)
                if 0 <= idx <= 200:
                    header = ref_data[:idx].decode('utf-8', errors='ignore')
                    b64_part = ref_data[idx + len(marker):].decode('utf-8', errors='ignore')
                    import base64
                    decoded_bytes = base64.b64decode(b64_part)
                    ref_tmp.write(decoded_bytes)
                    decoded_written = True
            except Exception:
                decoded_written = False
            if not decoded_written:
                ref_tmp.write(ref_data)
            ref_path = ref_tmp.name

        # Extract pitch from audio and reference with common sampling rate
        try:
            f_audio = extract_pitch(audio_path, target_sr=TARGET_SAMPLING_RATE)
        except ValueError as ve:
            raise ValueError(f"Audio processing error: {str(ve)}")
        except Exception as e:
            logger.error(f"Unexpected error extracting pitch: {e}")
            raise ValueError(f"Failed to process audio file: {str(e)}")
        
        try:
            f_ref = parse_midi(ref_path, target_sr=TARGET_SAMPLING_RATE)
        except ValueError as ve:
            raise ValueError(f"MIDI processing error: {str(ve)}")
        except Exception as e:
            logger.error(f"Unexpected error parsing MIDI: {e}")
            raise ValueError(f"Failed to process MIDI file: {str(e)}")

        # Validate that we have data
        if len(f_audio) == 0:
            raise ValueError("Audio file did not produce pitch data. Check if the file contains audio.")
        if len(f_ref) == 0:
            raise ValueError("MIDI file did not produce pitch data. Check if the file contains notes.")

        # Align sequences using DTW to handle tempo differences
        logger.info(f"Aligning sequences: audio={len(f_audio)} frames, ref={len(f_ref)} frames")
        try:
            f_audio_aligned, f_ref_aligned = align_and_warp(f_audio, f_ref)
            logger.info(f"Aligned sequences: {len(f_audio_aligned)} frames")
        except ValueError as ve:
            raise ValueError(f"Alignment error: {str(ve)}")
        except Exception as e:
            logger.error(f"Unexpected error during alignment: {e}")
            raise ValueError(f"Failed to align sequences: {str(e)}")

        # Detect false notes with configurable threshold
        error_indices = detect_errors(
            f_audio_aligned, 
            f_ref_aligned, 
            threshold_cents=threshold_cents,
            ignore_silence=ignore_silence
        )
        logger.info(f"Detected {len(error_indices)} error frames with threshold {threshold_cents} cents")
        
        # Compute score with actual cents differences
        score = compute_score(f_audio_aligned, f_ref_aligned, error_indices, total_frames=len(f_audio_aligned))
        
        # Calculate additional metrics
        total_frames = len(f_audio_aligned)
        incorrect_frames = len(error_indices)
        correct_frames = score["correct_frames"]
        accuracy = (correct_frames / total_frames * 100) if total_frames > 0 else 0.0
        duration = total_frames / TARGET_SAMPLING_RATE
        
        # Calculate max cents deviation
        mask = (f_audio_aligned > 0.0) & (f_ref_aligned > 0.0)
        if np.any(mask):
            cents_diff = 1200.0 * np.log2(f_audio_aligned[mask] / f_ref_aligned[mask])
            max_cents = float(np.max(np.abs(cents_diff)))
        else:
            max_cents = 0.0

        # Limit error indices to prevent huge responses
        from ..config import MAX_ERROR_INDICES_RETURNED
        error_indices_list = error_indices.tolist()
        if len(error_indices_list) > MAX_ERROR_INDICES_RETURNED:
            logger.warning(
                f"Too many error indices ({len(error_indices_list)}), "
                f"limiting to first {MAX_ERROR_INDICES_RETURNED}"
            )
            error_indices_list = error_indices_list[:MAX_ERROR_INDICES_RETURNED]
        
        # Create sampled pitch data for visualization (to keep response size manageable)
        # Sample every Nth frame - aim for ~500-1000 data points max
        sample_rate = max(1, int(total_frames / 500))
        sampled_indices = np.arange(0, total_frames, sample_rate)
        sampled_audio = f_audio_aligned[sampled_indices].tolist()
        sampled_ref = f_ref_aligned[sampled_indices].tolist()
        sampled_times = (sampled_indices / TARGET_SAMPLING_RATE).tolist()
        sampled_error_mask = np.isin(sampled_indices, error_indices).tolist()
        
        pitch_data = {
            "times": sampled_times,
            "audio_frequencies": sampled_audio,
            "reference_frequencies": sampled_ref,
            "is_error": sampled_error_mask,
            "sample_rate": sample_rate
        }
        
        # Initialise result model
        result = AnalysisResult(
            total_frames=total_frames,
            correct_frames=correct_frames,
            incorrect_frames=incorrect_frames,
            mean_cents=score["mean_cents"],
            max_cents=max_cents,
            accuracy_percent=accuracy,
            error_indices=error_indices_list,
            duration_seconds=duration,
            threshold_cents=threshold_cents,
            pitch_data=pitch_data,
        )

        # Optionally generate practice recommendations
        if generate_recommendations_flag:
            from ..config import ENABLE_RECOMMENDATIONS, TARGET_SAMPLING_RATE
            if ENABLE_RECOMMENDATIONS or os.getenv("ENABLE_RECOMMENDATIONS"):
                try:
                    rec = generate_recommendations(
                        accuracy_percent=accuracy,
                        incorrect_frames=incorrect_frames,
                        total_frames=total_frames,
                        mean_cents=score["mean_cents"],
                        max_cents=max_cents,
                        error_indices=error_indices_list,
                        duration_seconds=duration,
                        threshold_cents=threshold_cents,
                        sample_rate=TARGET_SAMPLING_RATE,
                    )
                    result.recommendations = rec
                except Exception as e:
                    # If recommendation generation fails, log and proceed without it
                    logger.error(f"Recommendation generation failed: {e}")
                    result.recommendations = None
            else:
                # Recommendations disabled globally; leave field as None
                result.recommendations = None

        logger.info(
            f"Analysis complete: accuracy={accuracy:.2f}%, mean_cents={score['mean_cents']:.2f}"
        )
        return result

    except ValueError as ve:
        # User input errors
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        # Other errors
        raise HTTPException(status_code=500, detail=f"Internal error: {str(exc)}")

    finally:
        # Clean up temporary files
        if audio_path:
            try:
                os.remove(audio_path)
            except Exception:
                pass
        if ref_path:
            try:
                os.remove(ref_path)
            except Exception:
                pass