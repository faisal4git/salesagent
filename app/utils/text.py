# utils/text.py

NEGATION_TERMS = [
    "not allowed",
    "cannot",
    "company policy",
    "policy",
    "mudiyaathu",
    "illai",
    "allowed illa"
]

REPORTING_VERBS = [
    "client asked",
    "client said",
    "he said",
    "she said",
    "they said",
    "client told"
]

def normalize_text(text: str) -> str:
    """
    Normalize transcript text for consistent analysis
    """
    text = text.lower().strip()
    text = text.replace("\n", " ")
    return text


def has_negation(text: str) -> bool:
    """
    Detect negation / refusal language
    """
    return any(term in text for term in NEGATION_TERMS)


def is_reported_speech(text: str) -> bool:
    """
    Detect quoted or reported speech
    (used to reduce false positives)
    """
    return any(verb in text for verb in REPORTING_VERBS)
