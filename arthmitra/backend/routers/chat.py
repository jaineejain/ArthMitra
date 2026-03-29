import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from arthmitra.backend.core.deps import get_current_user_id
from arthmitra.backend.database.session import get_db
from arthmitra.backend.database.models import Chat, FinancialProfile, Message, User
from arthmitra.backend.services.claude_service import service as claude_service
from arthmitra.backend.services.finance_engine import (
    calculate_couple_optimization,
    calculate_fire,
    calculate_loan,
    calculate_mhs,
    calculate_tax,
)
from arthmitra.backend.services.tax_engine import format_tax_result
from arthmitra.backend.services.mhs_scorer import calculate_mhs_score


router = APIRouter()

ALLOWED_MODULES = frozenset({"fire", "tax", "life_event", "mf_xray", "couple", "mhs", "onboarding"})

OPENING_LINES = {
    "fire": (
        "Hello — welcome to your Financial Independence plan. "
        "To tailor the roadmap, could you share your current age and the age at which you would like to achieve financial independence?"
    ),
    "tax": (
        "Hello. I will help you review your tax position. "
        "To begin, what is your annual gross salary or CTC (in ₹)?"
    ),
    "life_event": (
        "Hello. I am here to help you think through a major financial decision. "
        "Which situation are you facing? (For example: a bonus, job change, marriage, or preparing for a child.)"
    ),
    "mf_xray": (
        "Hello. I can review your mutual fund portfolio. "
        "You may upload a CAMS / KFintech statement, or we can walk through a sample portfolio first."
    ),
    "couple": (
        "Welcome to joint financial planning. "
        "To start, what is your monthly take-home income (in ₹), before we add your partner’s details?"
    ),
    "mhs": (
        "Hello. We will work through your Money Health Score. "
        "What is your current monthly income (in ₹)?"
    ),
    "onboarding": (
        "Hello — I am ArthMitra, your personal finance guide. "
        "We will build a structured plan step by step. May I have your name to begin?"
    ),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _require_session(db: Session | None) -> Session:
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db


def get_or_create_chat(db: Session, user_id: uuid.UUID, module_name: str) -> Chat:
    if module_name not in ALLOWED_MODULES:
        raise HTTPException(status_code=400, detail="Invalid feature / module")
    chat = db.query(Chat).filter(Chat.user_id == user_id, Chat.module_name == module_name).first()
    if chat:
        return chat
    now = _utcnow()
    chat = Chat(user_id=user_id, module_name=module_name, created_at=now, updated_at=now)
    db.add(chat)
    db.flush()
    opening = OPENING_LINES.get(module_name)
    if opening:
        db.add(Message(chat_id=chat.id, sender="ai", content=opening, created_at=now))
    db.commit()
    db.refresh(chat)
    return chat


def load_history_for_model(db: Session, chat_id: uuid.UUID) -> list[dict[str, str]]:
    rows = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    return [{"role": "user" if r.sender == "user" else "assistant", "content": r.content} for r in rows]


class ChatRequest(BaseModel):
    message: str
    feature: str
    history: list = []  # deprecated — server uses DB; kept for backward compatibility


def _guard_low_quality_reply(feature: str, text: str) -> str:
    """
    Groq can occasionally return short acknowledgements ("Got it.").
    Keep planner flow usable by forcing one concrete next question.
    """
    t = (text or "").strip().lower().replace("!", "").replace(".", "")
    low_quality = {
        "got it",
        "ok",
        "okay",
        "noted",
        "sure",
        "done",
        "understood",
    }
    if t not in low_quality:
        return text

    followups = {
        "tax": "Thank you. Next, how much HRA did you receive this year (in ₹)?",
        "fire": "Thank you. Next, what are your total monthly expenses, including rent and living costs (in ₹)?",
        "mhs": "Thank you. Next, what are your monthly expenses (in ₹)?",
        "onboarding": "Thank you. What is your age?",
        "couple": "Thank you. What is your partner's monthly take-home income (in ₹)?",
        "life_event": "Thank you. What is the exact amount involved (in ₹)?",
    }
    return followups.get((feature or "").lower(), text)


def _rupees_to_paise(v: Any) -> int:
    try:
        return int(round(float(v) * 100.0))
    except Exception:
        return 0


def _paise_to_rupees(v: Any) -> float:
    try:
        return float(v) / 100.0
    except Exception:
        return 0.0


def _convert_money_to_rupees(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            kl = k.lower()
            if isinstance(v, (int, float)) and ("rate" not in kl and "percent" not in kl) and (
                "tax" in k
                or "amount" in k
                or "sip" in k
                or "emi" in k
                or "outflow" in k
                or "interest" in k
                or "principal" in k
                or "penalty" in k
                or "fire" in k
                or "corpus" in k
                or "covered" in k
                or "gap" in k
                or "deduction" in k
                or "savings" in k
                or "current" in k
                or "invested" in k
                or "rent" in k
            ):
                out[k] = _paise_to_rupees(v)
            else:
                out[k] = _convert_money_to_rupees(v)
        return out
    if isinstance(obj, list):
        return [_convert_money_to_rupees(x) for x in obj]
    return obj


def _convert_calc_params_to_math_units(calc_type: str, params: dict, existing_profile: dict) -> dict:
    """
    Convert Claude numeric outputs (assumed rupees) to paise for finance_engine inputs.
    """
    p = dict(existing_profile)

    if calc_type == "mhs":
        p["age"] = int(params.get("age") or params.get("current_age") or p.get("age") or 0)
        p["monthly_income"] = _rupees_to_paise(params.get("monthly_income"))
        p["monthly_expenses"] = _rupees_to_paise(params.get("monthly_expenses"))
        p["monthly_emi"] = _rupees_to_paise(params.get("monthly_emi") or 0)
        p["emergency_fund"] = _rupees_to_paise(params.get("emergency_fund"))
        p["monthly_sip"] = _rupees_to_paise(params.get("monthly_sip"))
        p["term_cover"] = _rupees_to_paise(params.get("term_cover"))
        return p

    if calc_type == "fire":
        p["age"] = int(params.get("current_age") or p.get("age") or 0)
        p["target_retirement_age"] = int(params.get("target_retirement_age") or 60)
        p["monthly_income"] = _rupees_to_paise(params.get("monthly_income"))
        p["monthly_expenses"] = _rupees_to_paise(params.get("monthly_expenses"))
        p["total_investments"] = _rupees_to_paise(params.get("total_investments"))
        p["monthly_sip"] = _rupees_to_paise(params.get("monthly_sip"))
        p["monthly_emi"] = _rupees_to_paise(params.get("monthly_emi") or p.get("monthly_emi") or 0)
        return p

    if calc_type == "tax":
        p["annual_gross"] = _rupees_to_paise(params.get("annual_gross"))
        p["hra_received"] = _rupees_to_paise(params.get("hra_received"))
        p["basic_salary"] = _rupees_to_paise(params.get("basic_salary"))
        p["rent_paid"] = _rupees_to_paise(params.get("rent_paid"))
        p["city_type"] = params.get("city_type") or "metro"
        p["used_80c"] = _rupees_to_paise(params.get("used_80c"))
        p["health_premium"] = _rupees_to_paise(params.get("health_premium"))
        p["nps_tier1"] = _rupees_to_paise(params.get("nps_tier1"))
        return p

    if calc_type == "couple":
        # Claude may send either partner1/partner2 objects, or flattened partner fields.
        return p

    if calc_type == "loan":
        # Loan amounts are assumed in rupees coming from Claude output.
        # Convert only the principal to paise; keep interest rate and percentages as percentages.
        p["outstanding_principal"] = _rupees_to_paise(
            params.get("outstanding_principal")
            or params.get("principal")
            or params.get("outstanding_balance")
            or params.get("balance")
        )
        p["annual_interest_rate"] = float(
            params.get("annual_interest_rate")
            or params.get("interest_rate")
            or params.get("annual_rate")
            or 0.0
        )
        p["months_remaining"] = int(
            params.get("months_remaining")
            or params.get("remaining_months")
            or params.get("tenure_months")
            or 0
        )
        p["prepayment_penalty_percent"] = float(
            params.get("prepayment_penalty_percent") or params.get("penalty_percent") or 2.0
        )
        return p

    return p


def _extract_user_profile(db: Session, user_id: str) -> dict:
    try:
        uid = uuid.UUID(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    fp = db.query(FinancialProfile).filter(FinancialProfile.user_id == uid).first()
    if not fp:
        fp = FinancialProfile(user_id=uid)
        db.add(fp)
        db.commit()
        db.refresh(fp)

    return {
        "name": user.name,
        "age": user.age,
        "city": user.city,
        "is_salaried": bool(user.is_salaried),
        "monthly_income": int(user.monthly_income or 0),
        "monthly_expenses": int(user.monthly_expenses or 0),
        "monthly_emi": int(user.monthly_emi or 0),
        "risk_profile": user.risk_profile,
        "tax_regime": user.tax_regime,
        "emergency_fund": int(fp.emergency_fund),
        "total_investments": int(fp.total_investments),
        "monthly_sip": int(fp.monthly_sip),
        "term_cover": int(fp.term_cover),
        "health_cover": int(fp.health_cover),
        "epf_balance": int(fp.epf_balance),
        "invested_80c": int(fp.invested_80c),
        "has_nps": bool(fp.has_nps),
        "cc_outstanding": int(fp.cc_outstanding),
        "equity_pct": float(fp.equity_pct) if fp.equity_pct is not None else 0.7,
        "mhs_score": fp.mhs_score,
        "mhs_dimensions": fp.mhs_dimensions,
        "health_premium": int(fp.health_cover),  # best-effort mapping for tax wizard
    }


def _profile_for_ai(profile: dict) -> dict:
    """
    Claude talks in rupees; finance_engine uses paise.
    """
    return {
        **profile,
        "monthly_income": _paise_to_rupees(profile.get("monthly_income", 0)),
        "monthly_expenses": _paise_to_rupees(profile.get("monthly_expenses", 0)),
        "monthly_emi": _paise_to_rupees(profile.get("monthly_emi", 0)),
        "emergency_fund": _paise_to_rupees(profile.get("emergency_fund", 0)),
        "total_investments": _paise_to_rupees(profile.get("total_investments", 0)),
        "monthly_sip": _paise_to_rupees(profile.get("monthly_sip", 0)),
        "term_cover": _paise_to_rupees(profile.get("term_cover", 0)),
        "health_cover": _paise_to_rupees(profile.get("health_cover", 0)),
        "invested_80c": _paise_to_rupees(profile.get("invested_80c", 0)),
        "cc_outstanding": _paise_to_rupees(profile.get("cc_outstanding", 0)),
        "health_premium": _paise_to_rupees(profile.get("health_premium", 0)),
    }


@router.get("/api/chat/history/{feature}")
def get_chat_history(
    feature: str,
    db: Session | None = Depends(get_db),
    user_uuid: uuid.UUID = Depends(get_current_user_id),
):
    db = _require_session(db)
    if feature not in ALLOWED_MODULES:
        raise HTTPException(status_code=400, detail="Invalid feature")
    chat_row = db.query(Chat).filter(Chat.user_id == user_uuid, Chat.module_name == feature).first()
    if not chat_row:
        opening = OPENING_LINES.get(feature, "Tell me what you want to plan today.")
        return {
            "messages": [
                {"id": None, "role": "assistant", "content": opening, "created_at": None},
            ]
        }
    rows = db.query(Message).filter(Message.chat_id == chat_row.id).order_by(Message.created_at.asc()).all()
    out = []
    for r in rows:
        out.append(
            {
                "id": str(r.id),
                "role": "user" if r.sender == "user" else "assistant",
                "content": r.content,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
        )
    return {"messages": out}


@router.delete("/api/chat/history/{feature}")
def delete_chat_history(
    feature: str,
    db: Session | None = Depends(get_db),
    user_uuid: uuid.UUID = Depends(get_current_user_id),
):
    db = _require_session(db)
    if feature not in ALLOWED_MODULES:
        raise HTTPException(status_code=400, detail="Invalid feature")
    chat_row = db.query(Chat).filter(Chat.user_id == user_uuid, Chat.module_name == feature).first()
    if not chat_row:
        return {"ok": True, "cleared": True}
    db.query(Message).filter(Message.chat_id == chat_row.id).delete(synchronize_session=False)
    now = _utcnow()
    opening = OPENING_LINES.get(feature)
    if opening:
        db.add(Message(chat_id=chat_row.id, sender="ai", content=opening, created_at=now))
    chat_row.updated_at = now
    db.commit()
    return {"ok": True, "cleared": True}


@router.post("/api/chat")
async def chat(
    req: ChatRequest,
    db: Session | None = Depends(get_db),
    user_uuid: uuid.UUID = Depends(get_current_user_id),
):
    db = _require_session(db)
    try:
        profile = _extract_user_profile(db, str(user_uuid))
        ai_profile = _profile_for_ai(profile)

        chat_row = get_or_create_chat(db, user_uuid, req.feature)
        prior = load_history_for_model(db, chat_row.id)
        messages = list(prior)
        messages.append({"role": "user", "content": req.message})

        claude_result = await claude_service.chat(messages=messages, profile=ai_profile, feature=req.feature)

        card_data = None
        card_type = None
        response_text = ""

        if claude_result.get("type") == "calc_needed":
            calc_type = claude_result.get("calc_type")
            params = claude_result.get("data") or {}

            if calc_type == "mhs":
                math_profile = _convert_calc_params_to_math_units("mhs", params, profile)
                mhs = calculate_mhs_score(math_profile)
                card_data = mhs
                card_type = "mhs"
            elif calc_type == "fire":
                math_profile = _convert_calc_params_to_math_units("fire", params, profile)
                fire = calculate_fire(math_profile)
                card_data = fire
                card_type = "fire"
            elif calc_type == "tax":
                # Map used_80c/invested_80c best-effort from profile
                math_profile = _convert_calc_params_to_math_units("tax", params, profile)
                raw = calculate_tax(math_profile)
                card_data = format_tax_result(raw)
                card_type = "tax"
            elif calc_type == "couple":
                # Claude should provide partner1/partner2. If not, best-effort fallback.
                partner1 = params.get("partner1") or params.get("p1") or params.get("partner_a") or {}
                partner2 = params.get("partner2") or params.get("p2") or params.get("partner_b") or {}

                # Ensure required keys exist.
                partner1 = dict(partner1)
                partner2 = dict(partner2)
                # Convert numeric money fields (rupees->paise) if present.
                for pt in (partner1, partner2):
                    for f in [
                        "annual_gross",
                        "hra_received",
                        "basic_salary",
                        "rent_paid",
                        "used_80c",
                        "health_premium",
                        "nps_tier1",
                        "monthly_income",
                        "monthly_expenses",
                        "monthly_emi",
                        "monthly_sip",
                        "emergency_fund",
                        "term_cover",
                        "total_investments",
                        "invested_80c",
                    ]:
                        if f in pt and pt[f] is not None:
                            pt[f] = _rupees_to_paise(pt[f])
                    # City type -> keep
                    if "city_type" not in pt:
                        pt["city_type"] = "metro"

                couple = calculate_couple_optimization(partner1, partner2)
                card_data = couple
                card_type = "couple"
            elif calc_type == "loan":
                math_profile = _convert_calc_params_to_math_units("loan", params, profile)
                loan_result = calculate_loan(math_profile)
                card_data = loan_result
                card_type = None
            else:
                card_data = None
                card_type = None

            # Narrate results in natural language.
            narrate_input = {
                "feature": req.feature,
                "calc_type": claude_result.get("calc_type"),
                "result": _convert_money_to_rupees(card_data) if card_data is not None else None,
            }
            user_narrate_msg = (
                "CALCULATION_RESULT_JSON (already computed): "
                + json.dumps(narrate_input, ensure_ascii=False)
                + "\n\nNow write the final answer for the user. "
                + "Do not output any needs_calc JSON. Return ONLY normal text. "
                + "End with the MHS + AKS FINANCIAL SNAPSHOT scorecard (exact format from your system prompt) when the "
                + "result JSON supports scoring; otherwise state what is still needed for a full snapshot."
            )

            narrate_messages = list(messages)
            narrate_messages.append({"role": "user", "content": user_narrate_msg})
            narrate = await claude_service.chat(messages=narrate_messages, profile=ai_profile, feature=req.feature)
            response_text = narrate.get("content") or "Done. "
        else:
            response_text = claude_result.get("content") or ""

        response_text = _guard_low_quality_reply(req.feature, response_text)

        if not response_text:
            response_text = "I’m here with an update—reply back with a number and I’ll proceed."

        now = _utcnow()
        db.add(Message(chat_id=chat_row.id, sender="user", content=req.message, created_at=now))
        db.add(Message(chat_id=chat_row.id, sender="ai", content=response_text, created_at=now))
        chat_row.updated_at = now
        db.commit()

        return {"response": response_text, "card_data": card_data, "card_type": card_type}
    except HTTPException as e:
        # Still return something to avoid breaking the frontend.
        return {"response": str(e.detail), "card_data": None, "card_type": None}
    except Exception as e:
        return {
            "response": "Hmm, I didn’t fully get that — can you rephrase it once?",
            "card_data": None,
            "card_type": None,
        }


@router.post("/api/chat/onboarding-complete")
async def onboarding_complete(
    user_payload: dict,
    db: Session | None = Depends(get_db),
    user_uuid: uuid.UUID = Depends(get_current_user_id),
):
    db = _require_session(db)
    try:
        conversation = user_payload.get("conversation") or []

        profile_extracted = await claude_service.extract_profile(conversation_history=conversation)

        uid = user_uuid
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid)
            db.add(user)

        # Save extracted onboarding fields.
        # Amounts expected in rupees => convert to paise.
        name = profile_extracted.get("name") or user.name or "ArthMitra User"
        age = profile_extracted.get("age") or user.age or 30

        user.name = name
        user.age = int(age) if age is not None else user.age

        fp = db.query(FinancialProfile).filter(FinancialProfile.user_id == uid).first()
        if not fp:
            fp = FinancialProfile(user_id=uid)
            db.add(fp)

        user.monthly_income = _rupees_to_paise(profile_extracted.get("monthly_income") or 0)
        user.monthly_expenses = _rupees_to_paise(profile_extracted.get("monthly_expenses") or 0)
        user.monthly_emi = _rupees_to_paise(profile_extracted.get("monthly_emi") or 0)
        fp.emergency_fund = _rupees_to_paise(profile_extracted.get("emergency_fund") or 0)
        fp.monthly_sip = _rupees_to_paise(profile_extracted.get("monthly_sip") or 0)
        fp.term_cover = _rupees_to_paise(profile_extracted.get("term_cover") or 0)

        fp.total_investments = fp.total_investments or 0
        fp.invested_80c = fp.invested_80c or 0
        fp.equity_pct = float(fp.equity_pct) if fp.equity_pct is not None else 0.7
        fp.has_nps = bool(profile_extracted.get("has_nps") or False)  # might not exist
        fp.updated_at = None

        # Calculate MHS and store.
        math_profile = {
            "age": int(user.age) if user.age is not None else 30,
            "is_salaried": bool(user.is_salaried),
            "monthly_income": int(user.monthly_income or 0),
            "monthly_expenses": int(user.monthly_expenses or 0),
            "monthly_emi": int(user.monthly_emi or 0),
            "emergency_fund": int(fp.emergency_fund or 0),
            "monthly_sip": int(fp.monthly_sip or 0),
            "term_cover": int(fp.term_cover or 0),
            "health_cover": int(fp.health_cover or 0),
            "cc_outstanding": int(fp.cc_outstanding or 0),
            "equity_pct": float(fp.equity_pct or 0.7),
            "invested_80c": int(fp.invested_80c or 0),
            "has_nps": bool(fp.has_nps or False),
            "total_investments": int(fp.total_investments or 0),
        }
        mhs = calculate_mhs(math_profile)
        fp.mhs_score = mhs.get("total")
        fp.mhs_dimensions = mhs.get("dimensions")

        # Also compute karma for better dashboard UX.
        from arthmitra.backend.services.finance_engine import calculate_karma_score

        karma = calculate_karma_score(math_profile)

        db.commit()
        return {"user_id": str(uid), "name": name, "mhs": mhs, "karma": karma}
    except Exception:
        return {"error": "onboarding failed"}

