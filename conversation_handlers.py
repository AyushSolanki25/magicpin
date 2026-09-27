"""
conversation_handlers.py — Multi-turn conversation reply handler for Vera
Complies with §7.4 of challenge-brief.md.

Exposes:
    respond(state: dict, merchant_message: str) -> dict
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composer import VeraComposer

_composer = VeraComposer()

def respond(state: dict, merchant_message: str) -> dict:
    """
    Given the conversation state so far + the merchant's latest message, produce the reply action.
    Returns dict: {"action": "send" | "wait" | "end", "body": str, "cta": str, "rationale": str}
    """
    merchant_ctx = state.get("merchant_context", {})
    category_ctx = state.get("category_context", {})
    return _composer.respond_to_reply(state, merchant_message, merchant_ctx, category_ctx)
