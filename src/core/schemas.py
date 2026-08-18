"""
Module Name: schemas.py
Repo Path: src/core/schemas.py
Canonical Schema Registry for Stage 1.
"""
from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

class MacroTier(str, Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

    @classmethod
    def _missing_(cls, value: Any):
        # Auto-normalize "TIER 1", "tier 1", "tier_1" -> MacroTier.TIER_1
        if isinstance(value, str):
            norm = value.upper().replace(" ", "_").strip()
            for member in cls:
                if member.value == norm:
                    return member
        return None

class EpistemicTag(str, Enum):
    VERIFIED_OFFICIAL = "[VERIFIED_OFFICIAL]"
    VERIFIED_SOCIAL_PRIMARY = "[VERIFIED_SOCIAL_PRIMARY]"
    UNVERIFIED_RUMOR = "[UNVERIFIED_RUMOR]"

class DateWindow(BaseModel):
    model_config = ConfigDict(frozen=True)
    week_number: int = Field(..., ge=1, le=4)
    start_date: date
    end_date: date
    label: str

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v

class WeeklyCalendarWindows(BaseModel):
    model_config = ConfigDict(frozen=True)
    week_1: DateWindow
    week_2: DateWindow
    week_3: DateWindow
    week_4: DateWindow

class AnchorEvent(BaseModel):
    event_name: str = Field(..., description="Title of catalyst event")
    event_date: date = Field(..., description="Date of the event in YYYY-MM-DD")
    tier: MacroTier = Field(..., description="TIER_1, TIER_2, or TIER_3")
    source_citation: str = Field(..., description="Primary public source citation domain")
    epistemic_tag: EpistemicTag = Field(default=EpistemicTag.VERIFIED_OFFICIAL)
    is_verified: bool = Field(default=True)

class DominantThemeClassification(BaseModel):
    tier: MacroTier = Field(..., description="Highest priority tier matching anchor window")
    dominant_theme: str = Field(..., description="Primary market-moving macro narrative")
    rationale: str = Field(..., description="Analytical justification")
    anchor_events: List[AnchorEvent] = Field(default_factory=list, description="Anchor events")

class Stage1TemporalOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    windows: WeeklyCalendarWindows
    regime: DominantThemeClassification
    degraded_mode: bool = False
    audit_trace: List[str] = Field(default_factory=list)
