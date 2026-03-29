"""
AI Money Mentor Pro — v2 API (does not replace legacy /api/chat).
"""

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from arthmitra.backend.agents.orchestrator import run as orchestrator_run
from arthmitra.backend.core.deps import get_current_user_id
from arthmitra.backend.core.security import decode_token

router = APIRouter(prefix="/api/v2/mentor", tags=["mentor-v2"])

# In-process memory fallback (replace with Redis in production)
_USER_MEMORY: dict[str, dict[str, Any]] = {}


class MentorChatRequest(BaseModel):
    user_id: str | None = None  # ignored when Bearer token present
    message: str
    history: list = []
    # UX / intelligence layer
    language: str = "hinglish"  # english | hindi | hinglish | marathi | gujarati
    expert_mode: bool = False
    auto_detect_language: bool = True
    display_name: str | None = None
    # CA / professional English mode (default: on when language is english)
    professional_ca: bool | None = None
    # general_finance | tax | investment | couple_family | debt_loan (or UI label aliases)
    planner_section: str | None = None


class WealthSimRequest(BaseModel):
    """SIP future value — monthly compounding, illustrative only."""

    monthly_sip_rupees: float = 10_000
    years: int = 10
    annual_return: float = 0.12


@router.get("/health")
def mentor_health():
    return {
        "status": "ok",
        "version": "2.1",
        "services": [
            "orchestrator",
            "rag",
            "groq",
            "finance_engine",
            "what_if",
            "intelligence_layer",
            "language_detect",
            "watchdog_stub",
        ],
    }


@router.get("/watchdog/alerts")
def watchdog_alerts(user_uuid: uuid.UUID = Depends(get_current_user_id)):
    """
    Stub for Autonomous Financial Watchdog (demo alerts).
    Replace with DB + scheduler in production.
    """
    user_id = str(user_uuid)
    return {
        "success": True,
        "user_id": user_id,
        "alerts": [
            {
                "id": "demo-1",
                "severity": "warning",
                "title": "Tax-saving window",
                "description": "Feb–Mar: check 80C gap vs ₹1.5L limit and plan NPS 80CCD(1B) if suitable.",
                "action_prompt": "Help me check my 80C gap and last-minute tax save options for this FY.",
            },
            {
                "id": "demo-2",
                "severity": "info",
                "title": "SIP reminder",
                "description": "If SIP date is near, ensure bank balance so mandate doesn’t bounce.",
                "action_prompt": "My SIP is due soon — what should I verify in my bank and portfolio?",
            },
        ],
    }


@router.post("/simulate/wealth")
async def simulate_wealth(body: WealthSimRequest, _: uuid.UUID = Depends(get_current_user_id)):
    """Future value of monthly SIP (not advice; math illustration)."""
    try:
        m = max(0.0, float(body.monthly_sip_rupees))
        y = max(1, min(50, int(body.years)))
        ar = max(0.0, min(0.5, float(body.annual_return)))
        r_m = ar / 12.0
        n = y * 12
        if r_m <= 0:
            fv = m * n
        else:
            fv = m * (((1 + r_m) ** n - 1) / r_m)
        return {
            "success": True,
            "future_value_rupees": round(fv, 2),
            "monthly_sip_rupees": m,
            "years": y,
            "annual_return_assumed": ar,
            "disclaimer": "Illustrative only; markets are uncertain.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/chat")
async def mentor_chat(req: MentorChatRequest, user_uuid: uuid.UUID = Depends(get_current_user_id)):
    try:
        uid_str = str(user_uuid)
        mem = _USER_MEMORY.get(uid_str, {})
        profile_summary = json.dumps(mem.get("notes", {}))[:2000]

        lang = (req.language or "hinglish").lower().strip()
        professional_ca = (
            req.professional_ca if req.professional_ca is not None else (lang == "english")
        )

        result = await orchestrator_run(
            req.message,
            list(req.history or []),
            profile_summary,
            language=req.language,
            expert_mode=req.expert_mode,
            auto_detect_language=req.auto_detect_language,
            display_name=req.display_name,
            professional_ca=professional_ca,
            planner_section=req.planner_section,
        )

        # Light memory: last topic
        _USER_MEMORY.setdefault(uid_str, {})
        _USER_MEMORY[uid_str]["last_message"] = req.message[:500]
        _USER_MEMORY[uid_str]["last_domain"] = result.get("domain")
        _USER_MEMORY[uid_str]["language"] = req.language

        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e), "data": None}


@router.websocket("/ws")
async def mentor_ws(websocket: WebSocket):
    """
    Simple WebSocket: pass JWT as query ?token=... Client sends JSON {"message","history",...}.
    """
    token = websocket.query_params.get("token") or ""
    claims = decode_token(token) if token else None
    if not claims or not claims.get("sub"):
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        raw = await websocket.receive_text()
        payload = json.loads(raw)
        user_id = str(claims["sub"])
        message = payload.get("message", "")
        history = payload.get("history") or []
        language = payload.get("language", "hinglish")
        expert_mode = bool(payload.get("expert_mode", False))
        auto_detect = payload.get("auto_detect_language", True)
        display_name = payload.get("display_name")
        mem = _USER_MEMORY.get(user_id, {})
        profile_summary = json.dumps(mem.get("notes", {}))[:2000]
        professional_ca = (
            payload.get("professional_ca")
            if payload.get("professional_ca") is not None
            else (str(language or "").lower().strip() == "english")
        )
        planner_section = payload.get("planner_section")
        result = await orchestrator_run(
            message,
            history,
            profile_summary,
            language=language,
            expert_mode=expert_mode,
            auto_detect_language=auto_detect,
            display_name=display_name,
            professional_ca=bool(professional_ca),
            planner_section=planner_section,
        )
        await websocket.send_json({"success": True, "data": result})
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await websocket.send_json({"success": False, "error": str(e)})
        except Exception:
            pass
