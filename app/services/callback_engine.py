# app/services/callback_engine.py

from typing import List, Dict, Optional
import dateparser
from datetime import datetime


# ============================================================
# Multilingual callback patterns (EN, TA, HI, KN)
# ============================================================

CALLBACK_PATTERNS = [

    # ---------------- English ----------------
    "call you later",
    "call me later",
    "i will call later",
    "i'll call later",
    "i will call back",
    "i'll call back",
    "call back later",
    "i will get back to you",
    "i'll get back to you",
    "can we talk later",
    "let's talk later",
    "talk later",
    "speak later",
    "busy now",
    "call tomorrow",
    "call next",

    # ---------------- Tamil ----------------
    "naan apram call panren",
    "apram call panren",
    "later call panren",
    "naan later call panren",
    "apram pesuren",
    "apram pesuvom",
    "later pesuren",
    "later pesalaam",
    "konjam busy ah iruken",
    "ippo busy ah iruken",
    "free aana apram pesuren",
    "naan later pesuren",
    "naan apram pesuren",

    # ---------------- Hindi ----------------
    "main baad mein call karunga",
    "main baad mein call karungi",
    "baad mein call karta hoon",
    "baad mein baat karte hain",
    "kal call karta hoon",
    "kal baat karte hain",
    "main busy hoon",
    "abhi busy hoon",
    "baad mein call karoonga",
    "phir call karta hoon",

    # ---------------- Kannada ----------------
    "nanu later call madtini",
    "nanu later call maadthini",
    "nanu nantara call madtini",
    "nanu busy iddini",
    "nanu later mathadthini",
    "nanu nantara mathadthini",
    "later call madtini",
    "nan free aadmele call madtini"
]


# ============================================================
# Multilingual normalization for datetime extraction
# ============================================================

MULTILINGUAL_TIME_MAP = {

    # Tamil
    "நாளை": "tomorrow",
    "அடுத்த வாரம்": "next week",
    "அடுத்த திங்கள்": "next monday",
    "மாலை": "evening",
    "காலை": "morning",

    # Hindi
    "कल": "tomorrow",
    "बाद में": "later",
    "अगले हफ्ते": "next week",

    # Kannada
    "ನಾಳೆ": "tomorrow",
    "ನಂತರ": "later",
    "ಮುಂದಿನ ವಾರ": "next week"
}


# ============================================================
# Datetime extraction
# ============================================================

def preprocess_text_for_datetime(text: str) -> str:

    processed = text

    for k, v in MULTILINGUAL_TIME_MAP.items():
        processed = processed.replace(k, v)

    return processed


def extract_callback_datetime(text: str) -> Optional[Dict]:

    processed = preprocess_text_for_datetime(text)

    settings = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(),
        "RETURN_AS_TIMEZONE_AWARE": False
    }

    parsed = dateparser.parse(
        processed,
        languages=["en", "ta", "hi", "kn"],
        settings=settings
    )

    if parsed:

        return {
            "datetime_iso": parsed.isoformat(),
            "date": parsed.strftime("%Y-%m-%d"),
            "time": parsed.strftime("%H:%M:%S"),
            "unix": int(parsed.timestamp())
        }

    return None


# ============================================================
# Main detection function
# ============================================================

def detect_callback_intent(chunks: List[Dict]) -> Dict:

    callback_segments = []
    match_count = 0

    for chunk in chunks:

        original_text = chunk.get("text", "")
        normalized_text = chunk.get("normalized", original_text).lower()

        for pattern in CALLBACK_PATTERNS:

            if pattern in normalized_text:

                datetime_info = extract_callback_datetime(original_text)

                callback_segments.append({
                    "start": chunk.get("start"),
                    "end": chunk.get("end"),
                    "text": original_text,
                    "matched_phrase": pattern,
                    "callback_datetime": datetime_info
                })

                match_count += 1
                break

    callback_detected = match_count > 0

    # confidence scoring
    if match_count == 0:
        confidence = 0.0
    elif match_count == 1:
        confidence = 0.65
    elif match_count == 2:
        confidence = 0.85
    else:
        confidence = 0.95

    return {

        "callback_detected": callback_detected,

        "callback_confidence": round(confidence, 2),

        "callback_segments": callback_segments,

        "callback_summary": {
            "total_callback_mentions": match_count,
            "has_datetime": any(seg["callback_datetime"] for seg in callback_segments)
        }
    }