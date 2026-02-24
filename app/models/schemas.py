# app/models/schemas.py

from pydantic import BaseModel
from typing import List, Optional


# ============================================================
# Callback datetime info
# ============================================================

class CallbackDateTime(BaseModel):

    datetime_iso: str
    date: str
    time: str
    unix: int


# ============================================================
# Individual callback segment
# ============================================================

class CallbackSegment(BaseModel):

    start: Optional[float] = None
    end: Optional[float] = None

    text: str

    matched_phrase: str

    callback_datetime: Optional[CallbackDateTime] = None


# ============================================================
# Callback summary
# ============================================================

class CallbackSummary(BaseModel):

    total_callback_mentions: int

    has_datetime: bool


# ============================================================
# Final API response model
# ============================================================

class CallbackAnalysisResponse(BaseModel):

    callback_detected: bool

    callback_confidence: float

    callback_segments: List[CallbackSegment]

    callback_summary: CallbackSummary

    transcript_preview: Optional[str] = None

    stt_meta: Optional[dict] = None

    chunks_preview: Optional[List[dict]] = None