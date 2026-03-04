from typing import List, Dict, Optional
import dateparser
from datetime import datetime
import re


# ============================================================
# Expanded multilingual callback patterns
# ============================================================

CALLBACK_PATTERNS = [

    # ---------------- English ----------------
    "call you later","call me later",
    "i will call later","i'll call later",
    "i will call back","i'll call back",
    "call back later",
    "get back to you",
    "talk later","speak later",
    "i will contact you later",
    "i will call tomorrow",

    # ---------------- Tamil ----------------
    "கால் பண்றேன்","கால் பண்ணுறேன்","கால் பண்ணுவேன்",
    "நான் கால் பண்றேன்","நான் உங்களுக்கு கால் பண்றேன்",
    "நாளை கால் பண்றேன்","நாளைக்கு கால் பண்றேன்",
    "அப்புறம் கால் பண்றேன்","பின்னர் கால் பண்றேன்",
    "ரிமைண்ட் பண்றேன்","ரிமைண்ட் பண்ணுறேன்",
    "பின்னர் பேசலாம்","அப்புறம் பேசலாம்",
    "பின்னர் தொடர்பு கொள்கிறேன்",

    # Tanglish (very common in STT)
    "call pandra",
    "call panren",
    "call pannren",
    "call pannuren",
    "naan call panren",
    "nangal call panren",
    "naan call pannuren",
    "later call panren",
    "remind panren",
    "remind pannuren"

    # ---------------- Hindi native ----------------
    "मैं बाद में कॉल करूंगा",
    "मैं बाद में कॉल करूंगी",
    "मैं बाद में फोन करूंगा",
    "कल कॉल करूंगा",
    "कल फोन करूंगा",
    "थोड़ी देर बाद कॉल करता हूँ",
    "बाद में बात करते हैं",

    # ---------------- Hindi mixed ----------------
    "kal call karta hoon",
    "kal phone karta hoon",
    "main baad mein call karunga",
    "main baad mein phone karunga",
    "baad mein call karta hoon",
    "thodi der baad call karta hoon",
    "baad mein baat karte hain",

    # ---------------- Kannada native ----------------
    "ನಾನು ನಂತರ ಕರೆ ಮಾಡ್ತೀನಿ",
    "ನಾನು ನಂತರ ಫೋನ್ ಮಾಡ್ತೀನಿ",
    "ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಕರೆ ಮಾಡ್ತೀನಿ",
    "ನಾಳೆ ಕರೆ ಮಾಡ್ತೀನಿ",
    "ನಾನು ನಂತರ ಮಾತಾಡ್ತೀನಿ",

    # ---------------- Kannada mixed ----------------
    "nanu later call madtini",
    "nanu nantara call madtini",
    "nanu swalpa nantara call madtini",
    "nan free aadmele call madtini",
    "nanu nantara phone madtini",
]


# ============================================================
# Multilingual normalization map
# ============================================================

MULTILINGUAL_MAP = {

    # ---- Date words ----
    "டே ஆப்டர் டுமாரோ":"day after tomorrow",
    "டேய் ஆப்டர் டுமாரோ":"day after tomorrow",
    "டுமாரோ":"tomorrow",
    "நாளை":"tomorrow",
    "நாளைக்கு":"tomorrow",

    "कल":"tomorrow",
    "परसों":"day after tomorrow",

    "ನಾಳೆ":"tomorrow",
    "ಮತ್ತೊಂದು ದಿನ":"day after tomorrow",

    # ---- Time indicators ----
    # Tamil
    "காலை":"morning",
    "மாலை":"evening",
    "ஈவினிங்":"evening",
    "நைட்":"night",

    # Hindi
    "सुबह":"morning",
    "शाम":"evening",
    "रात":"night",
    "दोपहर":"afternoon",

    # Kannada
    "ಬೆಳಗ್ಗೆ":"morning",
    "ಸಂಜೆ":"evening",
    "ರಾತ್ರಿ":"night",
    "ಮಧ್ಯಾಹ್ನ":"afternoon",
}


TIME_FIX_REGEX = re.compile(r'(\d{1,2})\s+(\d{2})')
TIME_REGEX = re.compile(r'\b(\d{1,2}):?(\d{2})?\s?(am|pm)?\b')


DAY_KEYWORDS = [
    "day after tomorrow",
    "tomorrow",
    "today",
    "next monday","next tuesday","next wednesday",
    "next thursday","next friday",
    "next saturday","next sunday"
]


# ============================================================
# Normalize callback phrases (improves detection accuracy)
# ============================================================

def normalize_callback_intent(text: str) -> str:

    text = text.lower()

    replacements = {
        "i will call": "call",
        "i'll call": "call",
        "call you": "call",
        "call back": "callback",
        "call again": "callback",

        # Tanglish normalization
        "pandra": "panren",
        "pannra": "panren",
        "pannuren": "panren",

        # Hindi mixed normalization
        "main baad mein": "baad mein",
        "kal phone": "kal call",

        # Kannada mixed normalization
        "phone madtini": "call madtini",
        "kare madtini": "call madtini"
    }

    for k,v in replacements.items():
        text = text.replace(k,v)

    return text


# ============================================================
# Preprocess
# ============================================================

def preprocess(text:str)->str:

    processed=text.lower()

    for k,v in MULTILINGUAL_MAP.items():
        processed=processed.replace(k.lower(),v)

    processed=TIME_FIX_REGEX.sub(r'\1:\2',processed)

    return processed


# ============================================================
# Improved datetime extraction
# ============================================================

def extract_callback_datetime(text:str)->Optional[Dict]:

    processed=preprocess(text)

    found_day=None
    found_time=None

    for day in DAY_KEYWORDS:
        if day in processed:
            found_day=day
            break

    time_match=TIME_REGEX.search(processed)

    if time_match:

        hour=int(time_match.group(1))
        minute=time_match.group(2) or "00"
        ampm=time_match.group(3)

        if ampm:
            if ampm.lower()=="pm" and hour<12:
                hour+=12
            if ampm.lower()=="am" and hour==12:
                hour=0
        else:

            if "evening" in processed or "night" in processed:
                if hour<12:
                    hour+=12

            elif "afternoon" in processed:
                if hour<12:
                    hour+=12

            elif "morning" in processed:
                if hour==12:
                    hour=0

        found_time=f"{hour}:{minute}"

    if not found_day and not found_time:
        return None

    if found_day and found_time:
        clean_string=f"{found_day} {found_time}"
    elif found_day:
        clean_string=found_day
    else:
        clean_string=found_time

    parsed=dateparser.parse(
        clean_string,
        settings={
            "PREFER_DATES_FROM":"future",
            "RELATIVE_BASE":datetime.now()
        }
    )

    if parsed:
        return {
            "datetime_iso":parsed.isoformat(),
            "date":parsed.strftime("%Y-%m-%d"),
            "time":parsed.strftime("%H:%M:%S"),
            "unix":int(parsed.timestamp())
        }

    return None


# ============================================================
# Main detection engine
# ============================================================

def detect_callback_intent(chunks:List[Dict])->Dict:

    callback_segments=[]
    match_count=0

    for chunk in chunks:

        original_text=chunk.get("text","")

        normalized_text=normalize_callback_intent(
            chunk.get("normalized",original_text)
        )

        for pattern in CALLBACK_PATTERNS:

            if pattern.lower() in normalized_text:

                datetime_info=extract_callback_datetime(original_text)

                callback_segments.append({
                    "start":chunk.get("start"),
                    "end":chunk.get("end"),
                    "text":original_text,
                    "matched_phrase":pattern,
                    "callback_datetime":datetime_info
                })

                match_count+=1
                break

    callback_detected=match_count>0

    confidence=(
        0.0 if match_count==0 else
        0.85 if match_count==1 else
        0.93 if match_count==2 else
        0.98
    )

    return {
        "callback_detected":callback_detected,
        "callback_confidence":confidence,
        "callback_segments":callback_segments,
        "callback_summary":{
            "total_callback_mentions":match_count,
            "has_datetime":any(seg["callback_datetime"] for seg in callback_segments)
        }
    }