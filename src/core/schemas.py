"""
Module Name: schemas.py
Repo Path: src/core/schemas.py

BCBS 239 Data Lineage & Compliance Standards:
- Canonical Schema Registry for Stages 1 through 5, and Unscheduled Shock Monitoring.
- Enforces strict Pydantic v2 immutability and type validation across all data pipeline states.
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


# =====================================================================
# ENUMS & COMMON TYPES
# =====================================================================

class MacroTier(str, Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"

    @classmethod
    def _missing_(cls, value: Any):
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


class TailRiskCategory(str, Enum):
    LEFT_TAIL = "LEFT_TAIL"
    RIGHT_TAIL = "RIGHT_TAIL"


class TrafficLightStatus(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class ShockType(str, Enum):
    BANK_FAILURE_FDIC = "BANK_FAILURE_FDIC"
    SOVEREIGN_RATING_ACTION = "SOVEREIGN_RATING_ACTION"
    GEOPOLITICAL_KINETIC = "GEOPOLITICAL_KINETIC"
    PBOC_STEALTH_LIQUIDITY = "PBOC_STEALTH_LIQUIDITY"


class SourceCategory(str, Enum):
    MACRO_CALENDAR = "MACRO_CALENDAR"
    CENTRAL_BANKING = "CENTRAL_BANKING"
    TREASURY_AND_YIELDS = "TREASURY_AND_YIELDS"
    CORPORATE_AND_EARNINGS = "CORPORATE_AND_EARNINGS"
    DERIVATIVES_AND_OPEX = "DERIVATIVES_AND_OPEX"
    SECTOR_AND_COMMODITY = "SECTOR_AND_COMMODITY"
    GEOPOLITICS_AND_NEWS = "GEOPOLITICS_AND_NEWS"


# =====================================================================
# UNSCHEDULED SHOCK MONITOR SCHEMAS
# =====================================================================

class UnscheduledShockItem(BaseModel):
    shock_type: ShockType = Field(..., description="Classification of unscheduled shock")
    title: str = Field(..., description="Headline of breaking shock event")
    summary: str = Field(..., description="Clean plain-text summary of intervention or disruption")
    source_url: str = Field(..., description="Source verification URL")
    epistemic_tag: EpistemicTag = Field(default=EpistemicTag.VERIFIED_OFFICIAL)
    timestamp_et: str = Field(..., description="Timestamp of detection in US Eastern Time")
    severity_score: int = Field(..., ge=1, le=5, description="Severity rating 1 to 5")


class ShockMonitorResult(BaseModel):
    shocks_detected: bool = Field(..., description="True if any unscheduled shocks were detected")
    active_shock_alerts: List[UnscheduledShockItem] = Field(default_factory=list, description="List of detected shocks")
    is_emergency_regime: bool = Field(default=False, description="True if Tier-1 bank failure or sovereign downgrade detected")


# =====================================================================
# STAGE 1 SCHEMAS (TEMPORAL & REGIME)
# =====================================================================

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
    event_name: str
    event_date: date
    tier: MacroTier
    source_citation: str
    epistemic_tag: EpistemicTag = Field(default=EpistemicTag.VERIFIED_OFFICIAL)
    is_verified: bool = Field(default=True)


class DominantThemeClassification(BaseModel):
    tier: MacroTier
    dominant_theme: str
    rationale: str
    anchor_events: List[AnchorEvent] = Field(default_factory=list)


class Stage1TemporalOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    windows: WeeklyCalendarWindows
    regime: DominantThemeClassification
    degraded_mode: bool = False
    audit_trace: List[str] = Field(default_factory=list)


# =====================================================================
# STAGE 2 SCHEMAS (HARVESTER & 7 RISK MODULES)
# =====================================================================

class KeyValueItem(BaseModel):
    key: str = Field(..., description="Metric key name")
    value: str = Field(..., description="Raw metric value string or UNKNOWN")


class TreasuryAuctionRow(BaseModel):
    auction_date: str
    security_type: str
    term: str
    offering_size_usd: str
    settlement_date: str
    auction_url: str
    retrieval_timestamp_US_Eastern: str


class CentralBankEventRow(BaseModel):
    event_date: str
    central_bank: str
    event_type: str
    expected_action: str
    press_release_url: str
    retrieval_timestamp_US_Eastern: str


class EarningsBellwetherRow(BaseModel):
    ticker: str
    company: str
    earnings_date: str
    expected_eps: str
    implied_move_pct: str
    hist_realized_move_pct: str
    ir_release_url: str
    retrieval_timestamp_US_Eastern: str


class OpExGammaRow(BaseModel):
    opex_date: str
    description: str
    zero_gamma_level: str = Field(default="UNKNOWN")
    markets_affected: str
    source_url: str
    retrieval_timestamp_US_Eastern: str


class CotPositioningRow(BaseModel):
    report_date: str
    asset_class: str
    managed_money_net_positions: str
    change_vs_prior_week: str
    source_url: str
    retrieval_timestamp_US_Eastern: str


class VixTermStructureRow(BaseModel):
    as_of_date: str
    spot_vix: str
    m1_future: str
    m2_future: str
    m3_future: str
    curve_slope_m1_m2: str
    source_url: str
    retrieval_timestamp_US_Eastern: str


class AuditLogRow(BaseModel):
    rank: int = Field(..., ge=1, le=5)
    load_bearing_claim: str
    search_query: str
    retrieved_snippet: str
    source_url: str
    retrieval_timestamp_US_Eastern: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    epistemic_tag: EpistemicTag


class ModuleDataKV(BaseModel):
    module_1_plumbing: List[KeyValueItem] = Field(default_factory=list)
    module_2_macro_surprises: List[KeyValueItem] = Field(default_factory=list)
    module_3_earnings: List[KeyValueItem] = Field(default_factory=list)
    module_4_derivatives: List[KeyValueItem] = Field(default_factory=list)
    module_5_regulatory: List[KeyValueItem] = Field(default_factory=list)
    module_6_geopolitics: List[KeyValueItem] = Field(default_factory=list)
    module_7_narratives: List[KeyValueItem] = Field(default_factory=list)


class Stage2HarvesterOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    dominant_theme: str
    raw_kv_store: ModuleDataKV
    treasury_auctions_table: List[TreasuryAuctionRow] = Field(default_factory=list)
    central_bank_events_table: List[CentralBankEventRow] = Field(default_factory=list)
    earnings_bellwethers_table: List[EarningsBellwetherRow] = Field(default_factory=list)
    opex_and_gamma_table: List[OpExGammaRow] = Field(default_factory=list)
    cot_positioning_table: List[CotPositioningRow] = Field(default_factory=list)
    vix_term_structure_table: List[VixTermStructureRow] = Field(default_factory=list)
    audit_log_table: List[AuditLogRow] = Field(default_factory=list)
    degraded_mode: bool = False
    audit_trace: List[str] = Field(default_factory=list)


# =====================================================================
# STAGE 3 SCHEMAS (QUANT SYNTHESIS & TALEB STRESS TESTING)
# =====================================================================

class TailRiskItem(BaseModel):
    category: TailRiskCategory
    rank: int = Field(..., ge=1, le=3)
    catalyst_event: str
    date_horizon: str
    est_prob_pct: str
    direct_impact_asset: str
    spillover_vector: str
    desk_hedging_stance: str


class FactorRotationRegime(BaseModel):
    factor_pair: str
    regime_state: str
    spread_observation: str
    transmission_mechanics: str


class CrossAssetSpilloverItem(BaseModel):
    forward_macro_event: str
    us_10y_yield_impact: str
    dxy_impact: str
    crude_oil_impact: str
    equity_sector_factor_tilts: str


class TalebStressTest(BaseModel):
    systemic_shock_10pct_drawdown: str
    idiosyncratic_liquidity_shock: str


class TacticalScenario(BaseModel):
    scenario_name: str
    probability_pct: str
    core_thesis: str
    multi_asset_positioning: str


class Stage3QuantSynthesisOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    dominant_theme: str
    vix_curve_slope_pts: str
    atm_straddle_implied_moves: List[KeyValueItem] = Field(default_factory=list)
    factor_rotations: List[FactorRotationRegime] = Field(default_factory=list)
    top_left_tail_risks: List[TailRiskItem] = Field(default_factory=list)
    top_right_tail_risks: List[TailRiskItem] = Field(default_factory=list)
    cross_asset_spillovers: List[CrossAssetSpilloverItem] = Field(default_factory=list)
    taleb_stress_test: TalebStressTest
    tactical_scenarios: List[TacticalScenario] = Field(default_factory=list)
    degraded_mode: bool = False
    audit_trace: List[str] = Field(default_factory=list)


# =====================================================================
# STAGE 4 SCHEMAS (INSTITUTIONAL FORMATTER)
# =====================================================================

class Stage4FormatterOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    report_markdown: str
    report_file_path: str
    csv_file_paths: List[str] = Field(default_factory=list)
    word_count_briefing: int
    audit_trace: List[str] = Field(default_factory=list)


# =====================================================================
# STAGE 5 SCHEMAS (RETAIL FORMATTER)
# =====================================================================

class RetailActionItem(BaseModel):
    asset_bucket: str = Field(..., description="Stocks / 401k, Bonds / CD, Cash / High-Yield")
    action_guidance: str = Field(..., description="Clear plain-English allocation advice")


class Stage5RetailFormatterOutput(BaseModel):
    as_of_timestamp_et: datetime
    coverage_start_date: date
    coverage_end_date: date
    traffic_light_status: TrafficLightStatus = Field(..., description="GREEN, YELLOW, or RED")
    traffic_light_summary: str = Field(..., description="1-sentence plain English summary of market risk level")
    retail_report_markdown: str = Field(..., description="Complete plain-English retail newsletter markdown")
    retail_file_path: str = Field(..., description="Persisted path to Production retail note")
    action_checklist: List[RetailActionItem] = Field(default_factory=list, description="Actionable portfolio checklist")
    audit_trace: List[str] = Field(default_factory=list)
