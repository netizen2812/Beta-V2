"""
journey_engine.py — Curated Journey State Machine

Pydantic models and state machine for the Faith-Tech Curated Journey Engine.
All journeys are pre-recorded (no live TTS during playback). Each journey
ends with a CTA to Ask Imam for personalized dialogue.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

# ─── Path Resolution ──────────────────────────────────────────────────────────
JOURNEY_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "journeys.json"


# ─── Enums ────────────────────────────────────────────────────────────────────

class StageType(str, Enum):
    """Defines what kind of interaction each stage offers."""
    LISTEN    = "listen"     # Pre-recorded Maulana audio playback
    RECITE    = "recite"     # User recites a Surah (optional STT evaluation)
    REFLECT   = "reflect"    # Meditative Maulana audio + text prompt
    MILESTONE = "milestone"  # Progress checkpoint / streak marker
    DIALOGUE  = "dialogue"   # Opens Ask Imam (always final stage)


class Difficulty(str, Enum):
    BEGINNER     = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED     = "Advanced"


class JourneyCategory(str, Enum):
    PEACE        = "Peace"
    PRAYER       = "Prayer"
    GROWTH       = "Growth"
    LEARNING     = "Learning"
    SPIRITUALITY = "Spirituality"


# ─── Data Models ─────────────────────────────────────────────────────────────

class SurahRef(BaseModel):
    number: int
    name: str
    arabic: str
    verses: int


class JourneyPalette(BaseModel):
    """CSS gradient palette for this journey's visual identity."""
    from_color: str = Field(alias="from")
    via: str
    to: str
    accent: str
    glow: str

    model_config = {"populate_by_name": True}


class StageConfig(BaseModel):
    """Complete configuration for a single journey stage."""
    id: str
    index: int
    type: StageType
    title: str
    description: str
    asset_key: Optional[str] = None          # Key into premade audio asset manifest
    duration_sec: int = 60
    surah: Optional[SurahRef] = None
    locked: bool = True                       # Unlocked by completing previous stage
    leads_to_imam: bool = False               # If True, final stage CTAs to Ask Imam


class JourneyConfig(BaseModel):
    """Full configuration for a curated spiritual journey."""
    id: str
    title: str
    title_arabic: str
    tagline: str
    theme: str
    category: JourneyCategory
    icon: str
    difficulty: Difficulty
    duration_min: int
    palette: JourneyPalette
    stages: list[StageConfig]

    @property
    def total_stages(self) -> int:
        return len(self.stages)


# ─── Runtime State ────────────────────────────────────────────────────────────

class StageCompletion(BaseModel):
    """Records when and how a stage was completed."""
    stage_id: str
    completed_at: datetime
    score: Optional[float] = None            # Optional tajweed score for recite stages
    duration_actual_sec: Optional[int] = None


class JourneyState(BaseModel):
    """Runtime state for a user's progress through a specific journey."""
    user_id: str
    journey_id: str
    current_stage_index: int = 0
    stage_completions: dict[str, StageCompletion] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    is_complete: bool = False

    def is_stage_unlocked(self, stage_index: int) -> bool:
        """A stage is unlocked only if all prior stages are complete."""
        return stage_index <= self.current_stage_index

    def completed_stage_ids(self) -> set[str]:
        return set(self.stage_completions.keys())


# ─── Engine ───────────────────────────────────────────────────────────────────

class JourneyEngine:
    """
    Stateless state machine for the Curated Journey Engine.

    State persistence is delegated to the caller (FastAPI route stores
    state in MongoDB via the Node backend, or in-memory for now).
    """

    def __init__(self):
        self._journeys: dict[str, JourneyConfig] = {}
        self._load_journeys()

    def _load_journeys(self):
        """Load all journey configs from the JSON data file."""
        if not JOURNEY_DATA_PATH.exists():
            raise FileNotFoundError(f"Journey data not found at {JOURNEY_DATA_PATH}")
        with open(JOURNEY_DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for journey_data in raw:
            cfg = JourneyConfig.model_validate(journey_data)
            self._journeys[cfg.id] = cfg

    def all_journeys(self) -> list[JourneyConfig]:
        """Return all journey configs ordered by difficulty."""
        order = {Difficulty.BEGINNER: 0, Difficulty.INTERMEDIATE: 1, Difficulty.ADVANCED: 2}
        return sorted(self._journeys.values(), key=lambda j: order[j.difficulty])

    def get_journey(self, journey_id: str) -> JourneyConfig:
        if journey_id not in self._journeys:
            raise KeyError(f"Journey not found: {journey_id}")
        return self._journeys[journey_id]

    def new_state(self, user_id: str, journey_id: str) -> JourneyState:
        """Create a fresh state for a user starting a journey."""
        self.get_journey(journey_id)  # Validates journey exists
        return JourneyState(user_id=user_id, journey_id=journey_id)

    def advance_stage(
        self,
        state: JourneyState,
        stage_id: str,
        score: Optional[float] = None,
        duration_actual_sec: Optional[int] = None,
    ) -> JourneyState:
        """
        Mark a stage as complete and advance the journey state.
        Raises ValueError if the stage is not the current unlocked stage.
        """
        journey = self.get_journey(state.journey_id)
        stage = next((s for s in journey.stages if s.id == stage_id), None)
        if stage is None:
            raise ValueError(f"Stage {stage_id} not found in journey {state.journey_id}")

        if stage.index != state.current_stage_index:
            raise ValueError(
                f"Stage {stage_id} (index {stage.index}) is not the current stage "
                f"(index {state.current_stage_index}). Skipping stages is not allowed."
            )

        # Record completion
        completion = StageCompletion(
            stage_id=stage_id,
            completed_at=datetime.now(timezone.utc),
            score=score,
            duration_actual_sec=duration_actual_sec,
        )
        state.stage_completions[stage_id] = completion

        # Advance pointer
        next_index = state.current_stage_index + 1
        if next_index >= journey.total_stages:
            state.is_complete = True
            state.completed_at = datetime.now(timezone.utc)
            state.current_stage_index = journey.total_stages - 1
        else:
            state.current_stage_index = next_index

        return state

    def get_enriched_journey(
        self, journey: JourneyConfig, state: Optional[JourneyState]
    ) -> dict:
        """
        Return journey config enriched with per-stage unlock status
        based on the user's current state.
        """
        completed_ids = state.completed_stage_ids() if state else set()
        stages_out = []
        for stage in journey.stages:
            unlocked = (stage.index == 0) or (
                state is not None and stage.index <= state.current_stage_index
            ) or stage.id in completed_ids
            stages_out.append({
                **stage.model_dump(),
                "is_unlocked": unlocked,
                "is_complete": stage.id in completed_ids,
            })
        return {
            **journey.model_dump(),
            "stages": stages_out,
            "user_progress": state.model_dump() if state else None,
        }


# ─── Singleton ────────────────────────────────────────────────────────────────
journey_engine = JourneyEngine()
