"""Lightweight domain detection (finance vs general)."""

import re

_FINANCE_PATTERNS = [
    r"\b(sip|mutual fund|mf|elss|ppf|epf|nps|80c|80d|hra|tds|itr|gst)\b",
    r"\b(tax|income tax|capital gains|ltcg|stcg)\b",
    r"\b(fire|retirement corpus|swp|xirr|portfolio|asset allocation)\b",
    r"\b(emergency fund|foir|emi|credit card debt|loan)\b",
    r"\b(₹|inr|rupee|lakh|crore)\b",
    r"\b(sebi|rbi|fd|rd|recurring deposit)\b",
    r"\b(insurance|term plan|health insurance)\b",
    r"\b(stock|nifty|sensex|equity|debt fund)\b",
]


def detect_domain(text: str) -> str:
    if not text or not str(text).strip():
        return "general"
    t = str(text).lower()
    for pat in _FINANCE_PATTERNS:
        if re.search(pat, t, re.IGNORECASE):
            return "finance"
    # Short numeric money-like
    if re.search(r"\d{4,}", t):
        return "finance"
    return "general"
