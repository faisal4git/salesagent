# app/services/chunker.py
"""
Chunker:
- normalizes Tamil/English mixed text into a canonical form
- builds chunks from STT segments
- filters out too-short / filler-only chunks
"""

import re
from typing import List, Dict

RE_NON_WORD = re.compile(r"[^\w\u0B80-\u0BFF\s]")  # keep Tamil unicode block + word chars


def normalize_text(text: str) -> str:
    """
    Normalize Tamil/English mixed text for rule/ML matching:
    - lowercase
    - basic transliteration-like substitutions that your rules expect
    - remove punctuation
    """
    if not text:
        return ""

    t = text.lower().strip()

    # quick mapping of common spoken variants to canonical forms
    replacements = {
        "கம்பெனி": "company",
        "கம்பனி": "company",
        "company": "company",
        "தனியா": "own",
        "தனியா கம்பெனி": "own company",
        "தனியா கம்பெனி வச்சிருக்கேன்": "i have my own company",
        "கொடுக்க வேண்டாம்": "dont give",
        "கொடுக்காதீங்க": "dont give",
        "விலை கம்மியா": "price low",
        "விலை கம்மி": "price low",
        "என்கிட்ட": "to me",
        "என்கிட்ட வந்துருங்க": "come to me",
        "whatsapp": "whatsapp",
        "number": "number"
    }

    for k, v in replacements.items():
        t = t.replace(k, v)

    # remove punctuation but keep Tamil letters
    t = RE_NON_WORD.sub(" ", t)
    t = " ".join(t.split())
    return t


def build_chunks(segments: List[Dict]) -> List[Dict]:
    """
    Convert STT segments to chunk dicts expected by risk engine:
      { "text": str, "start": float, "end": float, "normalized": str }

    Filters:
     - minimum text length (>= 8 chars)
     - not only punctuation
    """
    chunks = []
    for seg in segments:
        raw = (seg.get("text") or "").strip()
        if not raw:
            continue

        norm = normalize_text(raw)
        if len(norm) < 8:
            # skip extremely short / noisy segments
            continue

        chunks.append({
            "text": raw,
            "normalized": norm,
            "start": seg.get("start"),
            "end": seg.get("end")
        })

    return chunks
