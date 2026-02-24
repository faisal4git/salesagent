
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import os
import tempfile
import shutil

from starlette.concurrency import run_in_threadpool

# keep your existing imports for chunker & callback engine      
from app.services.chunker import build_chunks
from app.services.callback_engine import detect_callback_intent

# NEW: import the SpeechRecognition-based STT class
from app.services.stt import GoogleWebSpeechSTT

router = APIRouter()
# optional codes below ! 
from app.models.schemas import CallbackAnalysisResponse

@router.post("/analyze-call", response_model=CallbackAnalysisResponse)

# -----------------------------
# Text-only testing schema
# -----------------------------
class Chunk(BaseModel):
    text: str
    start_time: float | None = None
    end_time: float | None = None

class ChunkPayload(BaseModel):
    chunks: List[Chunk]

# -----------------------------
# STT singleton (reuse model/recognizer across requests)
# -----------------------------
# tune language and chunk_seconds to your preference
stt = GoogleWebSpeechSTT(language="ta-IN", chunk_seconds=10)


# -----------------------------
# 1) PRODUCTION: analyze audio call
# -----------------------------
@router.post("/analyze-call")
async def analyze_call(audio: UploadFile = File(...)):
    """
    Upload audio file -> Google Web Speech STT (chunked) -> chunks -> callback intent engine
    """

    try:
        stt_out = await run_in_threadpool(stt.transcribe_upload, audio)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"STT runtime error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")

    segments = stt_out.get("segments", [])
    transcript = stt_out.get("transcript", "")
    meta = stt_out.get("meta", {})

    # Build chunks (you already have this)
    chunks = build_chunks(segments)

    # NEW: Detect callback intent
    callback_result = detect_callback_intent(chunks)

    return {
        "callback_detected": callback_result["callback_detected"],
        "callback_confidence": callback_result["callback_confidence"],
        "callback_segments": callback_result["callback_segments"],
        "transcript_preview": transcript[:800],
        "stt_meta": meta,
        "chunks_preview": chunks[:6]
    }


# -----------------------------
# 2) TESTING: analyze manual text chunks
# -----------------------------
@router.post("/analyze-chunks")
def analyze_chunks_api(payload: ChunkPayload):

    chunks = []
    for c in payload.chunks:
        chunks.append({
            "text": c.text,
            "start": c.start_time,
            "end": c.end_time
        })

    return detect_callback_intent(chunks)


# -----------------------------
# 3) Debug-only: return STT segments
# -----------------------------
@router.post("/debug-transcribe")
async def debug_transcribe(audio: UploadFile = File(...)):
    """
    Returns the first N segments from STT for quick debugging.
    """
    try:
        stt_out = await run_in_threadpool(stt.transcribe_upload, audio)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"STT runtime error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")

    segments = stt_out.get("segments", [])
    meta = stt_out.get("meta", {})
    transcript = stt_out.get("transcript", "")

    return {
        "segments": segments[:10],
        "transcript_preview": transcript[:800],
        "stt_meta": meta,
    }

