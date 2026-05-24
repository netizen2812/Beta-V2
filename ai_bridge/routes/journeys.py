"""
routes/journeys.py — Curated Journey API Routes

Exposes the Journey Engine over HTTP. State is stored in-memory per process
(suitable for single-VM deployment). For multi-instance scaling, replace
_user_states with a MongoDB or Redis store.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.journey_engine import journey_engine, JourneyState

log = logging.getLogger("journeys")
router = APIRouter(prefix="/api/journeys", tags=["journeys"])

# ─── In-memory state store (user_id + journey_id → JourneyState) ─────────────
# Key: f"{user_id}:{journey_id}"
_user_states: dict[str, JourneyState] = {}


def _state_key(user_id: str, journey_id: str) -> str:
    return f"{user_id}:{journey_id}"


# ─── Request / Response schemas ───────────────────────────────────────────────

class AdvanceStageRequest(BaseModel):
    user_id: str
    stage_id: str
    score: Optional[float] = None
    duration_actual_sec: Optional[int] = None


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
def list_journeys(category: Optional[str] = Query(None)):
    """Return all journeys, optionally filtered by category."""
    journeys = journey_engine.all_journeys()
    if category and category.lower() != "all":
        journeys = [j for j in journeys if j.category.value.lower() == category.lower()]
    return {
        "status": "ok",
        "count": len(journeys),
        "journeys": [j.model_dump() for j in journeys],
    }


@router.get("/{journey_id}")
def get_journey(journey_id: str, user_id: Optional[str] = Query(None)):
    """Return full journey config, enriched with user's stage unlock state if provided."""
    try:
        journey = journey_engine.get_journey(journey_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Journey not found: {journey_id}")

    state = None
    if user_id:
        state = _user_states.get(_state_key(user_id, journey_id))

    return {
        "status": "ok",
        "journey": journey_engine.get_enriched_journey(journey, state),
    }


@router.get("/{journey_id}/state")
def get_journey_state(journey_id: str, user_id: str = Query(...)):
    """Return the current state of a user's journey progress."""
    state = _user_states.get(_state_key(user_id, journey_id))
    if not state:
        # Return default fresh state (not yet persisted)
        try:
            journey_engine.get_journey(journey_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Journey not found: {journey_id}")
        return {
            "status": "ok",
            "state": None,
            "message": "Journey not yet started",
        }
    return {"status": "ok", "state": state.model_dump()}


@router.post("/{journey_id}/start")
def start_journey(journey_id: str, user_id: str = Query(...)):
    """Start or restart a journey for a user."""
    try:
        journey_engine.get_journey(journey_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Journey not found: {journey_id}")

    key = _state_key(user_id, journey_id)
    if key not in _user_states:
        state = journey_engine.new_state(user_id, journey_id)
        _user_states[key] = state
    else:
        state = _user_states[key]

    return {"status": "ok", "state": state.model_dump()}


@router.post("/{journey_id}/advance")
def advance_stage(journey_id: str, body: AdvanceStageRequest):
    """Mark the current stage as complete and advance to the next."""
    key = _state_key(body.user_id, journey_id)
    state = _user_states.get(key)

    if not state:
        # Auto-start if not yet started
        try:
            state = journey_engine.new_state(body.user_id, journey_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Journey not found: {journey_id}")
        _user_states[key] = state

    try:
        state = journey_engine.advance_stage(
            state=state,
            stage_id=body.stage_id,
            score=body.score,
            duration_actual_sec=body.duration_actual_sec,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    _user_states[key] = state

    journey = journey_engine.get_journey(journey_id)
    enriched = journey_engine.get_enriched_journey(journey, state)

    return {
        "status": "ok",
        "state": state.model_dump(),
        "journey": enriched,
        "is_complete": state.is_complete,
        "leads_to_imam": enriched["stages"][state.current_stage_index].get("leads_to_imam", False)
            if not state.is_complete else True,
    }
