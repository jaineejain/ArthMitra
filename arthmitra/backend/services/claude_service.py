import json
import re
from typing import Any

import httpx

from arthmitra.backend.config import GROQ_API_KEY, GROQ_MODEL
from arthmitra.backend.services.master_advisor_prompt import build_master_core_prompt


ELITE_MODELING_RULES = (
    "ELITE MODELLING (all features): "
    "Do NOT claim you are SEBI-registered. Never suggest SIP/investments above sustainable surplus or income. "
    "Show brief derivations for corpus/SIP. Assumptions: inflation ~5–7%; equity ~10–12%; debt ~6–8% (illustrative). "
    "FIRE baseline: annual expenses × 25 (or ~×33 conservative); adjust for inflation to FI date when relevant. "
    "If critical numbers missing, ask one focused question before asserting user-specific outcomes. "
    "Structure long answers: Reality Check → Numbers → Gap → phased actions → insights. Avoid repeating prior text verbatim."
)


CRITICAL_AI_RULES = (
    "CRITICAL RULES for the AI: "
    "1) NEVER perform financial calculations yourself. "
    "2) When math is needed, output ONLY this JSON (no other text before or after): "
    '{"needs_calc": true, "calc_type": "mhs|fire|tax|xirr|couple|loan", "params": {relevant values}} '
    "3) Ask exactly ONE question at a time during onboarding. "
    "4) Give ONE specific action with a specific rupee number — never say 'consider' or 'you might want to'. "
    "5) If user says income is below ₹5,000 ask exactly: "
    '"Did you mean ₹5,000 or ₹50,000? I want to confirm the figure." '
    "6) After the user shares their name, address them by first name in a professional way (e.g. “Thank you, Jainee.”). "
    "7) Never restart planner flow unless user asks to reset; continue from conversation context. "
    "8) After each major result, proactively provide 2-3 insights: biggest mistake, one exact rupee action, urgency if critical. "
    "9) Keep guidance professional and concise; ask only one question at a time during data collection. "
    "10) LANGUAGE: Use clear professional English by default; if the user writes in Hinglish, respond in warm, clear Hinglish "
    "(avoid crude slang like “bas karo” unless mirroring user tone sparingly). "
    "11) When enough data or CALCULATION_RESULT_JSON exists, end with the MHS + AKS **FINANCIAL SNAPSHOT** block from the master prompt; "
    "if data is thin, give a partial snapshot + one clarifying question."
)


FEATURE_ADDITIONS = {
    "onboarding": (
        "Collect these 8 values one question at a time: "
        "name, age, monthly_income, monthly_expenses, monthly_emi, emergency_fund, monthly_sip, term_cover. "
        'After all 8, output: {"needs_calc":true,"calc_type":"mhs","params":{all 8 values}} '
        "Never ask more than one thing per message."
    ),
    "fire": (
        "FIRE / financial independence planner. Collect: current_age, target_retirement_age, monthly_income, "
        "monthly_expenses, total_investments, monthly_sip. "
        "Once all 6 collected output the needs_calc JSON. "
        "Tone: professional English throughout — acknowledge answers politely (e.g. “Thank you for sharing that.”), "
        "never use informal Hindi or slang. "
        "After results from the engine: tie numbers to ELITE structure — Reality Check; Corrected Numbers with "
        "FIRE logic (annual expenses × 25 baseline, inflation note if long horizon); Gap Analysis; "
        "3-phase Action Plan (0–2, 2–5, 5+ years); 3–5 Smart Insights. "
        "Ensure suggested SIP fits surplus; never exceed income."
    ),
    "tax": (
        "Collect: annual_gross, hra_received, basic_salary, rent_paid, city_type (metro/non-metro), "
        "used_80c, health_premium, nps_tier1. "
        "Once collected output needs_calc JSON. "
        "After results: explain regime winner with exact rupee saving, "
        "list top 3 missed deductions."
    ),
    "life_event": (
        "Life Event Advisor. Detect event type from user message: bonus|job_loss|marriage|baby|job_change|inheritance. "
        "In addition, detect personal loan / debt prepayment intent from messages like: 'I have a personal loan', 'take a loan', 'prepay my loan', 'reduce EMI'. "
        "Personal loan flow (strict order, one question per message when collecting): "
        "1) Ask for current outstanding principal (in ₹). "
        "2) Ask for annual interest rate (in % p.a.). "
        "3) Ask for remaining tenure (months remaining). "
        "4) When all 3 are available, output needs_calc JSON with calc_type='loan' and params: "
        "{ 'outstanding_principal': <rupees>, 'annual_interest_rate': <percent>, 'months_remaining': <months>, "
        "'prepayment_penalty_percent': <assume 2 if not provided> }. "
        "After engine computation (no needs_calc JSON), show: EMI per month, total remaining outflow, and total interest remaining. "
        "Use the penalty percent only as an illustrative assumption until the user confirms actual prepayment penalty later. "
        "Then ask: monthly take-home income (post-TDS, in ₹). "
        "Next ask: health insurance policy type (term/health policy vs none) and sum insured (₹). "
        "Be calm and professional; do not suggest new SIP/investments until emergency fund and insurance protection are addressed."
    ),
    "mf_xray": (
        "You will receive a portfolio JSON. Analyze each fund: XIRR vs benchmark, expense ratio (flag if >1%), "
        "overlap between funds. Generate a rebalancing plan with 3-5 specific actions. "
        "Flag any regular plan vs direct plan differences."
    ),
    "couple": (
        "Both partners' data will be provided. Optimize: which partner claims HRA (higher slab wins), "
        "SIP split for LTCG efficiency (more to lower income partner), NPS for both, combined insurance. "
        "Calculate combined_old_tax vs combined_optimized_tax and show annual saving."
    ),
    "mhs": (
        "Collect these values (one question at a time) for Money Health Score: "
        "age, monthly_income, monthly_expenses, monthly_emi, emergency_fund, monthly_sip, term_cover. "
        "Once all are collected output the needs_calc JSON "
        'with {"needs_calc":true,"calc_type":"mhs","params":{collected values}}. '
        "After results, explain which single dimension is weakest and give 3 concrete actions with exact rupee amounts."
    ),
}


def _try_extract_needs_calc(text: str) -> dict[str, Any] | None:
    """
    Claude is instructed to output JSON only when math is needed.
    We still parse defensively to be robust.
    """
    # Direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and parsed.get("needs_calc") is True:
            return parsed
    except Exception:
        pass

    # Extract first JSON object in the output (defensive).
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    candidate = match.group(0)
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict) and parsed.get("needs_calc") is True:
            return parsed
    except Exception:
        return None
    return None


class ClaudeService:
    def __init__(self) -> None:
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    async def _groq_chat(self, system: str, messages: list[dict], max_tokens: int = 4096) -> str:
        """
        Groq uses OpenAI-compatible chat completions API.
        """
        if not self.api_key:
            return ""

        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": 0.3,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            return str(message.get("content") or "").strip()

    async def groq_raw_completion(
        self,
        system: str,
        user_content: str,
        max_tokens: int = 2000,
        temperature: float = 0.25,
    ) -> str:
        """Single-turn Groq completion (system + one user blob). Used by Mentor Pro / agents."""
        if not self.api_key:
            return ""
        messages = [{"role": "user", "content": user_content}]
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, *messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices") or []
            if not choices:
                return ""
            message = choices[0].get("message") or {}
            return str(message.get("content") or "").strip()

    def _build_system(self, profile: dict, feature: str) -> str:
        feature_key = feature.lower().strip()
        addition = FEATURE_ADDITIONS.get(feature_key, "")
        profile_hint = ""
        if profile:
            # Include a compact profile hint for personalization.
            name = profile.get("name") or ""
            if name:
                profile_hint = f"\nUser first name: {name}.\n"
        return "\n\n".join(
            [
                build_master_core_prompt(),
                ELITE_MODELING_RULES,
                CRITICAL_AI_RULES,
                addition,
                profile_hint,
            ]
        ).strip()

    async def chat(self, messages: list, profile: dict, feature: str) -> dict[str, Any]:
        try:
            if not self.api_key:
                return {
                    "type": "text",
                    "content": (
                        "Quick note: Groq API key is not configured, so I can’t call the AI model right now. "
                        "For the hackathon demo, keep going—your inputs will still appear."
                    ),
                }

            system = self._build_system(profile, feature)

            # Groq chat format: list of {"role": "user"|"assistant", "content": "..."}
            groq_messages = []
            for m in messages:
                role = m.get("role")
                content = m.get("content")
                if not role or content is None:
                    continue
                if role not in {"user", "assistant"}:
                    role = "user"
                groq_messages.append({"role": role, "content": str(content)})

            text = await self._groq_chat(system=system, messages=groq_messages, max_tokens=4096)

            needs_calc = _try_extract_needs_calc(text or "")
            if needs_calc:
                return {
                    "type": "calc_needed",
                    "data": needs_calc.get("params") or {},
                    "calc_type": needs_calc.get("calc_type"),
                }

            return {"type": "text", "content": text.strip() if isinstance(text, str) else str(text)}
        except Exception as e:
            return {
                "type": "text",
                "content": (
                    "Oops—something went wrong while generating your reply. "
                    "Please try again in a moment. (Friendly error: "
                    + str(e)
                    + ")"
                ),
            }

    async def extract_profile(self, conversation_history: list) -> dict[str, Any]:
        """
        LLM-based extraction. We request JSON-only output.
        """
        try:
            if not self.api_key:
                return {}

            instruction = (
                "Extract the financial onboarding/profile values from this chat. "
                "Return ONLY valid JSON with keys if found. Do not wrap in markdown. "
                "Expected fields include: name, age, monthly_income, monthly_expenses, monthly_emi, "
                "emergency_fund, monthly_sip, term_cover, total_investments, invested_80c, has_nps, "
                "equity_pct, city (if present). Amounts should be numeric in rupees as written."
            )

            system = "You are a strict JSON extraction engine. Return JSON only."

            groq_messages = []
            groq_messages.append({"role": "user", "content": instruction})
            for m in conversation_history:
                role = m.get("role")
                content = m.get("content")
                if role and content is not None:
                    if role not in {"user", "assistant"}:
                        role = "user"
                    groq_messages.append({"role": role, "content": str(content)})

            text = await self._groq_chat(system=system, messages=groq_messages, max_tokens=900)
            if not text:
                return {}

            try:
                return json.loads(text)
            except Exception:
                # Defensive extraction if model wraps JSON in prose.
                match = re.search(r"\{[\s\S]*\}", text)
                if not match:
                    return {}
                return json.loads(match.group(0))
        except Exception:
            return {}


service = ClaudeService()

