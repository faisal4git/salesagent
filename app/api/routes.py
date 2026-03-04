from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

from starlette.concurrency import run_in_threadpool

from app.services.chunker import build_chunks
from app.services.callback_engine import detect_callback_intent
from app.services.stt import GoogleWebSpeechSTT

from app.models.schemas import CallbackAnalysisResponse


router = APIRouter()


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
# STT singleton
# -----------------------------
stt = GoogleWebSpeechSTT(language="ta-IN", chunk_seconds=10)


# -----------------------------
# PRODUCTION: analyze audio call
# -----------------------------
@router.post("/analyze-call", response_model=CallbackAnalysisResponse)
async def analyze_call(audio: UploadFile = File(...)):
    """
    Upload audio file -> STT -> chunking -> callback detection
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

    chunks = build_chunks(segments)

    callback_result = detect_callback_intent(chunks)

    return {
        "callback_detected": callback_result["callback_detected"],
        "callback_confidence": callback_result["callback_confidence"],
        "callback_segments": callback_result["callback_segments"],
        "callback_summary": callback_result["callback_summary"],
        "transcript_preview": transcript[:800],
        "stt_meta": meta,
        "chunks_preview": chunks[:6]
    }


# -----------------------------
# TEST endpoint (optional)
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
# Debug STT endpoint
# -----------------------------
@router.post("/debug-transcribe")
async def debug_transcribe(audio: UploadFile = File(...)):

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
        "stt_meta": meta
    }