"""Heuristic auto-detection: Hindi / Hinglish cues from user text."""

import re

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
_GUJARATI = re.compile(r"[\u0A80-\u0AFF]")
_MARATHI_SCRIPT = re.compile(r"[\u0900-\u097F]")  # shared Devanagari; disambiguation via keywords

_HINGLISH_HINTS = (
    "mera", "meri", "mere", "hai", "hain", "kya", "kaise", "kitna", "kitni", "rupee", "rupaye",
    "paisa", "batao", "chahiye", "karna", "karu", "salary", "naukri", "bachat", "invest",
    "aapka", "aapki", "hum", "main", "mujhe", "kyun", "kab", "yeh", "ye", "matlab",
)
_MARATHI_HINTS = ("maza", "mazi", "ahe", "kasa", "kashi", "rupee", "paise", "saving")
_GUJARATI_HINTS = ("chhe", "kem", "maru", "mari", "rupiya", "bachaat")


def auto_detect_language_code(text: str) -> str | None:
    """
    Returns one of: hinglish, hindi, marathi, gujarati — or None if no strong signal.
    """
    if not text or not str(text).strip():
        return None
    t = str(text).strip()
    low = t.lower()

    if _GUJARATI.search(t) or any(h in low for h in _GUJARATI_HINTS):
        return "gujarati"
    if any(h in low for h in _MARATHI_HINTS) and _DEVANAGARI.search(t):
        return "marathi"
    if _DEVANAGARI.search(t):
        return "hindi"
    if any(h in low for h in _HINGLISH_HINTS):
        return "hinglish"
    return None
