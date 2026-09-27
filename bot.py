"""
Vera AI Assistant Bot — Unified Module & FastAPI Server
Complies with:
  1. §7.1 of challenge-brief.md: compose(category, merchant, trigger, customer) -> dict
  2. challenge-testing-brief.md: FastAPI web server exposing /v1/healthz, /v1/metadata, /v1/context, /v1/tick, /v1/reply
"""

from typing import Dict, Any, Optional, List
from fastapi import FastAPI
from pydantic import BaseModel, Field
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from composer import VeraComposer
from state import StateManager

_composer = VeraComposer()
_state_mgr = StateManager()


def compose(category: Dict[str, Any], merchant: Dict[str, Any],
            trigger: Dict[str, Any], customer: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Direct composition entry point compliant with §7.1."""
    return _composer.compose(category, merchant, trigger, customer)


# -----------------------------------------------------------------------------
# FastAPI HTTP Server
# -----------------------------------------------------------------------------

app = FastAPI(title="Vera AI Assistant Bot", version="1.0.0")


class ContextPushModel(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: Optional[str] = None


class TickModel(BaseModel):
    now: Optional[str] = None
    available_triggers: List[str] = Field(default_factory=list)


class ReplyModel(BaseModel):
    conversation_id: str
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    from_role: str = "merchant"
    message: str
    received_at: Optional[str] = None
    turn_number: int = 1


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Vera AI Assistant Bot",
        "docs": "/docs",
        "health": "/v1/healthz",
    }


@app.get("/v1/healthz")
async def healthz():
    return {
        "status": "ok",
        "uptime_seconds": _state_mgr.get_uptime_seconds(),
        "contexts_loaded": _state_mgr.get_context_counts(),
    }


@app.get("/v1/metadata")
async def metadata():
    return {
        "team_name": "Team Vera Elite",
        "team_members": ["AI Lead"],
        "model": "claude-3-5-sonnet / gemini-1.5-flash",
        "approach": "4-Context deterministic LLM composer with multi-turn intent transition & auto-reply filter",
        "contact_email": "vera-team@magicpin.in",
        "version": "1.0.0",
        "submitted_at": "2026-04-26T08:00:00Z",
    }


@app.post("/v1/context")
async def push_context(body: ContextPushModel):
    return _state_mgr.push_context(body.scope, body.context_id, body.version, body.payload)


@app.post("/v1/tick")
async def tick(body: TickModel):
    actions = []

    for trg_id in body.available_triggers:
        if len(actions) >= 20:
            break

        trg = _state_mgr.get_context("trigger", trg_id)
        if not trg:
            continue

        merchant_id = trg.get("merchant_id") or trg.get("payload", {}).get("merchant_id")
        if not merchant_id:
            continue

        merchant = _state_mgr.get_context("merchant", merchant_id)
        if not merchant:
            continue

        cat_slug = merchant.get("category_slug") or trg.get("payload", {}).get("category", "dentists")
        category = _state_mgr.get_context("category", cat_slug)
        if not category:
            category = {"slug": cat_slug, "voice": {"tone": "peer_clinical"}, "peer_stats": {"avg_ctr": 0.030}}

        customer_id = trg.get("customer_id")
        customer = _state_mgr.get_context("customer", customer_id) if customer_id else None

        composed = compose(category, merchant, trg, customer)
        conv_id = f"conv_{merchant_id}_{trg_id}"

        actions.append({
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
            "customer_id": customer_id,
            "send_as": composed["send_as"],
            "trigger_id": trg_id,
            "template_name": "vera_generic_v1",
            "template_params": [merchant.get("identity", {}).get("name", ""), composed["body"][:30]],
            "body": composed["body"],
            "cta": composed["cta"],
            "suppression_key": composed["suppression_key"],
            "rationale": composed["rationale"],
        })

        _state_mgr.update_last_sent(conv_id, composed["body"])

    return {"actions": actions}


@app.post("/v1/reply")
async def reply(body: ReplyModel):
    conv_state = _state_mgr.record_incoming_reply(
        conv_id=body.conversation_id,
        merchant_id=body.merchant_id,
        customer_id=body.customer_id,
        from_role=body.from_role,
        message=body.message,
        turn_number=body.turn_number,
    )

    merchant_ctx = _state_mgr.get_context("merchant", body.merchant_id) if body.merchant_id else None
    cat_slug = merchant_ctx.get("category_slug") if merchant_ctx else "dentists"
    cat_ctx = _state_mgr.get_context("category", cat_slug) if cat_slug else None

    return _composer.respond_to_reply(conv_state, body.message, merchant_ctx, cat_ctx)


if __name__ == "__main__":
    import uvicorn

    # Render provides PORT dynamically. Keep 8080 as the local-development fallback.
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
