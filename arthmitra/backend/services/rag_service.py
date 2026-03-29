"""
Minimal RAG: retrieve top-k knowledge snippets from local JSON.
Replace with vector DB / embeddings in production.
"""

import json
import os
import re
from typing import Any


def _kb_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "data", "knowledge_base.json")


def _load_kb() -> list[dict[str, Any]]:
    path = _kb_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def retrieve(query: str, k: int = 3) -> list[dict[str, Any]]:
    """Score snippets by simple token overlap + tag match."""
    q = (query or "").lower()
    if not q.strip():
        return []

    kb = _load_kb()
    q_tokens = set(re.findall(r"[a-z0-9]+", q))
    scored: list[tuple[float, dict[str, Any]]] = []

    for item in kb:
        text = (item.get("text") or "") + " " + (item.get("title") or "")
        text_l = text.lower()
        tags = " ".join(item.get("tags") or [])
        t_tokens = set(re.findall(r"[a-z0-9]+", text_l + " " + tags.lower()))
        overlap = len(q_tokens & t_tokens)
        score = overlap + 0.5 * sum(1 for tag in (item.get("tags") or []) if tag in q)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: -x[0])
    return [x[1] for x in scored[:k]]
