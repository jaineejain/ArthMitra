"""
Master Financial Advisor — re-exports Arth protocol v3 for /api/chat.
"""

from arthmitra.backend.services.arth_protocol_prompt import build_master_core_prompt

__all__ = ["build_master_core_prompt"]
