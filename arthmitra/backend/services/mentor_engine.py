"""
AI Money Mentor Pro — structured multi-mode response via Groq.
Intelligence layer + language + beginner/expert. RAG snippets + domain detection.
"""

import json
import re
from typing import Any

from arthmitra.backend.agents.domain_detector import detect_domain
from arthmitra.backend.agents.language_detect import auto_detect_language_code
from arthmitra.backend.services.rag_service import retrieve
from arthmitra.backend.services.claude_service import service as llm_service
from arthmitra.backend.services.mentor_prompts import (
    CA_FP_LAYER,
    ELITE_ADVISOR_APPENDIX,
    INTELLIGENCE_LAYER,
    PREMIUM_ADDON,
    LANGUAGE_RULES,
    expert_mode_instruction,
    planner_section_rules,
)


MENTOR_JSON_SCHEMA_HINT = """
Respond with ONLY valid JSON (no markdown) matching this shape:
{
  "domain": "finance" | "general",
  "confidence": "high" | "medium" | "low",
  "response_language_used": "english|hindi|hinglish|marathi|gujarati",
  "clarifying_question": "string or null — prefer null if you gave useful approximate guidance; else ONE question only",
  "answer": "string — Quick Summary (positive, goal + feasibility)",
  "key_numbers": "string — bullet-style lines: required corpus, current status, gap (mark approximate)",
  "analysis": "string — what's working vs what needs work",
  "explanation": "string — optional extra why if needed",
  "example": "string or null — ₹ illustration only if grounded or clearly approximate",
  "recommendation": "string — optional top-line takeaway",
  "risk_notes": "string — disclaimers, uncertainty",
  "modes": { "safe": "string", "balanced": "string", "growth": "string" },
  "action_steps": ["string — practical ordered steps"],
  "alternative_options": ["string — 2-3 ways to close the gap if goal is tight"],
  "assumptions": "string — return % range, inflation %, time horizon used",
  "pro_tip": "string — one smart mentor insight",
  "insights": ["string — optional extra bullets"],
  "why_this_answer": "string"
}
For finance replies, fill key_numbers, analysis, alternative_options, assumptions, and pro_tip whenever relevant.
If a fact is uncertain, set confidence to low and say so in risk_notes.
For India: use ₹; never claim guaranteed returns.

CA / professional English mode (when active in system prompt): "clarifying_question" may contain at most 1–2 very short
follow-ups when critical data for quantitative advice is missing; otherwise null. Never use filler phrases before questions.

When professional_ca + elite appendix is active: prefer "insights" with 3–5 items; "action_steps" must be exactly 3 phase lines.
"""


def _fallback_response(
    user_message: str,
    domain: str,
    rag_snippets: list[dict],
    *,
    language: str = "hinglish",
    professional_ca: bool = False,
) -> dict[str, Any]:
    ctx = " ".join(s.get("title", "") for s in rag_snippets[:2])
    base = {
        "domain": domain,
        "confidence": "medium",
        "response_language_used": language,
        "clarifying_question": "Monthly take-home (₹) aur age bata doge to plan aur sharp ho jayega — optional, agar abhi nahi to bhi chalega.",
        "answer": "✅ Quick Summary — Main aapko safe default plan de sakta hoon; numbers ke saath plan aur accurate hoga, par direction abhi bhi clear hai.",
        "key_numbers": "📊 Key Numbers (approximate) — illustration: agar ₹50k/month save + 10 saal @ ~11% nominal, future value rough ballpark SIP calculator se nikal sakte ho; exact goal ke liye amount + horizon chahiye.",
        "analysis": "📈 Analysis — Strength: aap planning shuru kar rahe ho. Gap: bina income/age ke corpus target fix karna mushkil; phir bhi priority order (emergency → term → SIP) follow karo.",
        "explanation": "Kyun: safety pehle, phir growth — yeh India mein sabse sustainable sequence hai.",
        "example": None,
        "recommendation": "Pehle 6 months expenses emergency fund, phir term life (if dependents), phir goal-based SIP.",
        "risk_notes": "Yeh education hai, guaranteed return nahi. Tax/sections final CA se confirm karo.",
        "modes": {
            "safe": "Pehle 6 mahine expenses liquid mein, phir SIP.",
            "balanced": "Debt + equity mix goal horizon se decide karo.",
            "growth": "Long horizon + risk capacity ho to equity tilt — par emergency pehle.",
        },
        "action_steps": [
            "Emergency fund target set karo (≈ 6× monthly expenses).",
            "Ek clear financial goal likho: amount + timeline.",
            "Uske hisaab se monthly SIP ballpark nikalwao (assumptions ke saath).",
        ],
        "alternative_options": [
            "SIP amount thoda badha ke timeline shorten karo.",
            "Goal date 1–2 saal extend karke monthly burden kam karo.",
            "Discretionary spend cut karke invest karo.",
        ],
        "assumptions": "⚠️ Assumptions — long-term return ~10–12% p.a. illustrative only; inflation planning ~5–6%; horizon user goal se match karna best.",
        "pro_tip": "💡 Pro Tip — Auto-debit SIP + annual step-up chhota sa hack hai jo time ke saath bada farq laata hai.",
        "insights": [
            "Common mistake: bina emergency fund ke aggressive SIP.",
            "Term insurance skip karna risky hai agar dependents hain.",
        ],
        "why_this_answer": "Fallback — API unavailable ya vague input; safe India-first defaults + optional clarification.",
    }
    if language == "english":
        base.update(
            {
                "clarifying_question": "If you share monthly take-home (₹) and age, I can sharpen the numbers — optional.",
                "answer": "✅ Quick Summary — I can still give a solid direction now; with your income and age the corpus math gets much tighter.",
                "key_numbers": "📊 Key Numbers (approximate) — Without your exact goal, use illustrative assumptions: e.g. ₹X/month SIP for Y years at ~11% gives a ballpark future value; label all figures approximate.",
                "analysis": "📈 Analysis — Working for you: you’re asking early. To improve: add one concrete goal (amount + timeline) when you can.",
                "explanation": "Why: emergency buffer and protection first, then investing, is the most reliable India-first sequence."
                + (f" Hint: {ctx}" if ctx else ""),
                "assumptions": "⚠️ Assumptions — return ~10–12% p.a. illustrative; inflation ~5–6% for goals; horizon from your goal when known.",
                "pro_tip": "💡 Pro Tip — A small annual SIP step-up beats chasing timing the market.",
            }
        )
    if professional_ca:
        base.update(
            {
                "response_language_used": "english",
                "clarifying_question": "Monthly take-home (₹)?\nAge?",
                "answer": (
                    "• Prioritise: high-cost debt reduction → 3–6 months emergency fund → health + term cover (if dependents) "
                    "→ goal-based SIP.\n"
                    "• Until income/age are known, keep assumptions explicit and numbers illustrative only."
                ),
                "key_numbers": (
                    "• Illustrative only: e.g. ₹10,000/month SIP for 10 years at ~12% p.a. ≈ ₹23 lakh (not guaranteed).\n"
                    "• Scale monthly amount and horizon to your goal once you share targets."
                ),
                "analysis": (
                    "• Positive: you are seeking structured guidance early.\n"
                    "• Gap: without cash-flow numbers, corpus targets remain approximate."
                ),
                "explanation": None,
                "example": None,
                "recommendation": (
                    "Under the new tax regime, focus on wealth creation and risk cover — not 80C-led products for 'tax saving'."
                ),
                "risk_notes": "Educational guidance only; confirm tax positions with a practising CA for your facts.",
                "modes": {
                    "safe": "Higher liquid / debt tilt until emergency fund is full; minimise high-interest debt first.",
                    "balanced": "After core buffers, split long-term goals between equity MF and quality debt per horizon.",
                    "growth": "Long horizon with capacity for volatility: higher equity share only after insurance and EF are in place.",
                },
                "action_steps": [
                    "(0–2 years) Build emergency fund (3–6 months’ expenses), clear high-interest debt, put basic health/term cover in place.",
                    "(2–5 years) Automate a SIP within actual surplus; increase income skills or side income; review asset mix yearly.",
                    "(5+ years) Tilt toward goal-linked equity for long horizons; rebalance; revisit FIRE corpus using expenses × 25 heuristic ± inflation.",
                ],
                "alternative_options": [
                    "Extend goal timeline to reduce required monthly investment.",
                    "Increase monthly surplus by trimming discretionary spend.",
                    "Prepay costliest loan first if interest rate exceeds expected investment return (illustrative comparison).",
                ],
                "assumptions": "Inflation ~5–7% for long goals; equity ~10–12% p.a., debt ~6–8% p.a. (illustrative only, not guaranteed).",
                "pro_tip": "Automate SIP and review once a year rather than timing the market.",
                "insights": [
                    "SIP size must stay within post-expense surplus — never treat full income as investable.",
                    "FIRE corpus ≈ 25× annual expenses is a starting heuristic; inflate expenses to your FI age for a stricter target.",
                    "Avoid starting large equity SIPs before emergency fund and core insurance (if dependents).",
                    "In the new tax regime, focus on net worth and risk cover rather than 80C-led products.",
                    "If an earlier estimate ignored inflation, revised corpus should be higher — state the correction explicitly.",
                ],
                "why_this_answer": "Fallback — model unavailable; CA-style priority stack and English-only output.",
            }
        )
    return base


def _parse_json_obj(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None


async def generate_mentor_response(
    user_message: str,
    history: list[dict[str, Any]],
    profile_summary: str | None = None,
    *,
    language: str = "hinglish",
    expert_mode: bool = False,
    auto_detect_language: bool = True,
    display_name: str | None = None,
    professional_ca: bool = False,
    planner_section: str | None = None,
) -> dict[str, Any]:
    domain = detect_domain(user_message)
    resolved_lang = (language or "hinglish").lower().strip()
    if professional_ca:
        resolved_lang = "english"
        auto_detect_language = False
    elif auto_detect_language:
        detected = auto_detect_language_code(user_message)
        if detected:
            resolved_lang = detected

    lang_rule = LANGUAGE_RULES.get(
        resolved_lang,
        LANGUAGE_RULES["hinglish"],
    )

    intelligence = (
        f"{CA_FP_LAYER}\n\n{ELITE_ADVISOR_APPENDIX}" if professional_ca else INTELLIGENCE_LAYER
    )
    section_block = planner_section_rules(planner_section)

    snippets = retrieve(user_message, k=4)
    rag_text = "\n".join(
        f"[{s.get('id')}] {s.get('title')}: {s.get('text')}" for s in snippets
    )

    name_line = f"User preferred name: {display_name}.\n" if display_name else ""

    system = f"""You are AI Money Mentor Pro / ArthMitra — premium India-first financial intelligence.

{intelligence}

{PREMIUM_ADDON}

{section_block}

{(
        "MODE: CA / PROFESSIONAL — use precise India-relevant terminology (IT Act concepts, liquidity, asset allocation). "
        "Short bullet-led answers; no dumbing down below professional clarity."
        if professional_ca
        else expert_mode_instruction(expert_mode)
    )}

LANGUAGE RULE (locked for this response):
{lang_rule}
Selected language code: {resolved_lang}. Never switch language unless user changes setting in a future message.

{name_line}
{MENTOR_JSON_SCHEMA_HINT}

Domain hint: {domain}. If not finance, still output valid JSON; give sensible general guidance.
Profile context (may be empty): {profile_summary or "none"}
Knowledge snippets (may be incomplete; if conflict, say uncertain):
{rag_text or "(no snippets)"}
"""

    user_block = ""
    for m in history[-10:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        user_block += f"{role}: {content}\n"
    user_block += f"user: {user_message}\n"

    raw = await llm_service.groq_raw_completion(
        system=system,
        user_content=user_block,
        max_tokens=2400,
        temperature=0.2,
    )

    parsed = _parse_json_obj(raw) if raw else None
    if isinstance(parsed, dict) and (parsed.get("answer") or parsed.get("clarifying_question")):
        parsed.setdefault("domain", domain)
        parsed.setdefault("response_language_used", resolved_lang)
        parsed.setdefault("rag_citations", [s.get("id") for s in snippets])
        return parsed

    return _fallback_response(
        user_message,
        domain,
        snippets,
        language=resolved_lang,
        professional_ca=professional_ca,
    )

