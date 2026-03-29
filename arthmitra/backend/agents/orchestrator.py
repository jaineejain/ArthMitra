"""
Orchestrator: routes to domain + delegates to mentor_engine.
"""

from typing import Any

from arthmitra.backend.services.mentor_engine import generate_mentor_response


async def run(
    user_message: str,
    history: list[dict[str, Any]],
    profile_summary: str | None,
    *,
    language: str = "hinglish",
    expert_mode: bool = False,
    auto_detect_language: bool = True,
    display_name: str | None = None,
    professional_ca: bool = False,
    planner_section: str | None = None,
) -> dict[str, Any]:
    return await generate_mentor_response(
        user_message,
        history,
        profile_summary,
        language=language,
        expert_mode=expert_mode,
        auto_detect_language=auto_detect_language,
        display_name=display_name,
        professional_ca=professional_ca,
        planner_section=planner_section,
    )
