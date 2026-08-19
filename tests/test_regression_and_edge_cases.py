"""
Module Name: test_regression_and_edge_cases.py
Repo Path: tests/test_regression_and_edge_cases.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Comprehensive Edge-Case Stress Testing and Regression Suite.
- Coverage:
  1. Temporal Rollovers (Leap Year Feb 29, Year-End Dec 31 to Jan).
  2. Extreme Market Crash Math (VIX Backwardation Inversion M1-M2 > 10 pts).
  3. Zero-Division & Negative Price Inputs in ATM Straddle & Factor Spreads.
  4. Total Offline / Missing API Key Graceful Degradation across all Stages.
  5. Deterministic Sentence-Boundary Truncation under extreme word counts.
  6. RFC 4180 CSV Comma Escaping & N/A Null-State Guarantees.
"""

# Import date and datetime types
from datetime import datetime, date

# Import pytz for timezone assertions
import pytz

# Import pytest for assertions
import pytest

# Import core schemas
from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    TrafficLightStatus,
    ModuleDataKV,
    KeyValueItem,
    Stage1TemporalOutput,
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
    Stage4FormatterOutput,
    Stage5RetailFormatterOutput,
)

# Import math utilities
from src.core.math_utils import (
    calculate_atm_straddle_implied_move,
    calculate_vix_curve_slope_math,
    calculate_event_severity_score,
    truncate_to_word_limit_clean,
)

# Import stage modules
from src.stages.stage_1_temporal import compute_calendar_windows, run_stage_1
from src.stages.stage_2_harvester import fallback_baseline_harvester
from src.stages.stage_3_quant import fallback_baseline_synthesis
from src.stages.stage_4_formatter import serialize_table_to_csv, run_stage_4
from src.stages.stage_5_retail import determine_traffic_light_status, fallback_baseline_retail_note
from src.core.fact_auditor import audit_report_against_raw_kv


# =====================================================================
# 1. TEMPORAL BOUNDARY & LEAP YEAR EDGE CASES
# =====================================================================

def test_leap_year_february_rollover_math():
    """Verify calendar math correctly handles February 29 leap year."""
    tz_et = pytz.timezone("America/New_York")
    # Leap year date: Feb 26, 2028
    leap_anchor = tz_et.localize(datetime(2028, 2, 26, 9, 30, 0))
    windows = compute_calendar_windows(anchor_dt=leap_anchor)

    # Week 1 should span through leap day Feb 29
    assert windows.week_1.start_date == date(2028, 2, 26)
    assert windows.week_1.end_date == date(2028, 3, 3)
    # Total 28-day coverage should end March 24, 2028
    assert windows.week_4.end_date == date(2028, 3, 24)


def test_year_end_december_to_january_rollover():
    """Verify calendar math correctly rolls from December into January of next year."""
    tz_et = pytz.timezone("America/New_York")
    # Year-end date: Dec 28, 2026
    year_end_dt = tz_et.localize(datetime(2026, 12, 28, 9, 30, 0))
    windows = compute_calendar_windows(anchor_dt=year_end_dt)

    assert windows.week_1.start_date == date(2026, 12, 28)
    assert windows.week_1.end_date == date(2027, 1, 3)
    assert windows.week_4.end_date == date(2027, 1, 24)


# =====================================================================
# 2. QUANTITATIVE MATH EXTREME CRASH & ZERO-DIVISION EDGE CASES
# =====================================================================

def test_extreme_vix_backwardation_market_crash_scenario():
    """Verify extreme volatility inversion (M1 >> M2) assigns Backwardation."""
    # Market crash: Spot VIX=45.0, M1=38.0, M2=26.0 (Slope = -12.00 pts)
    slope, label = calculate_vix_curve_slope_math(m1_future=38.0, m2_future=26.0)
    assert slope == pytest.approx(-12.0)
    assert label == "-12.00 pts (Backwardation)"


def test_atm_straddle_zero_and_negative_inputs():
    """Verify invalid/zero spot prices return UNKNOWN without crashing."""
    # Zero spot price
    assert calculate_atm_straddle_implied_move(10.0, 10.0, 0.0) == "UNKNOWN"
    # Negative spot price
    assert calculate_atm_straddle_implied_move(10.0, 10.0, -100.0) == "UNKNOWN"
    # Negative call price
    assert calculate_atm_straddle_implied_move(-5.0, 10.0, 100.0) == "UNKNOWN"
    # All None
    assert calculate_atm_straddle_implied_move(None, None, None) == "UNKNOWN"


def test_severity_scoring_boundary_clamping():
    """Verify severity score is strictly clamped between 1 and 5."""
    assert calculate_event_severity_score(MacroTier.TIER_1, is_marquee_release=True, asset_classes_exposed_count=10) == 5
    assert calculate_event_severity_score(MacroTier.TIER_3, is_marquee_release=False, asset_classes_exposed_count=0) == 1


# =====================================================================
# 3. SENTENCE-BOUNDARY TRUNCATION STRESS TESTING
# =====================================================================

def test_sentence_boundary_truncation_extreme_word_counts():
    """Verify 500-word block truncates to <= 200 words strictly on sentence endings."""
    long_text = " ".join([f"Sentence number {i} provides detailed macroeconomic analysis for institutional desks." for i in range(1, 60)])
    assert len(long_text.split()) > 400

    truncated = truncate_to_word_limit_clean(long_text, max_words=200)

    # Assert word limit is respected
    word_count = len(truncated.split())
    assert word_count <= 200
    # Assert string ends with a period (complete sentence)
    assert truncated.endswith(".")
    # Assert no trailing dangling comma or hyphen
    assert not truncated.endswith((",", "-", ":", ";"))


# =====================================================================
# 4. RFC 4180 CSV ESCAPING & NULL-STATE GUARANTEES
# =====================================================================

def test_csv_comma_escaping_and_null_states():
    """Verify strings with commas are quoted and empty lists emit N/A."""
    # 1. Comma escaping
    test_rows = [
        {"col_a": "Powell, Jerome", "col_b": "Speech on rates, inflation, and growth"}
    ]
    csv_out = serialize_table_to_csv(test_rows, ["col_a", "col_b"], "test_quotes.csv")
    assert '"Powell, Jerome"' in csv_out
    assert '"Speech on rates, inflation, and growth"' in csv_out

    # 2. Empty table null state
    empty_csv = serialize_table_to_csv([], ["ticker", "company", "eps"], "empty.csv")
    assert "N/A,N/A,N/A" in empty_csv


# =====================================================================
# 5. TOTAL OFFLINE DEGRADATION ACROSS ALL 5 STAGES
# =====================================================================

def test_full_pipeline_offline_degradation_integrity():
    """Verify all 5 stages degrade gracefully without exceptions when API key is empty."""
    tz_et = pytz.timezone("America/New_York")
    fixed_dt = tz_et.localize(datetime(2026, 8, 18, 9, 30, 0))

    # Stage 1 Offline
    s1 = run_stage_1(anchor_dt=fixed_dt, api_key="", save_artifact=False)
    assert isinstance(s1, Stage1TemporalOutput)
    assert s1.degraded_mode is True

    # Stage 2 Offline
    s2 = fallback_baseline_harvester(s1)
    assert isinstance(s2, Stage2HarvesterOutput)
    assert s2.degraded_mode is True

    # Stage 3 Offline
    s3 = fallback_baseline_synthesis(s2)
    assert isinstance(s3, Stage3QuantSynthesisOutput)
    assert s3.degraded_mode is True
    assert len(s3.top_left_tail_risks) == 3
    assert len(s3.top_right_tail_risks) == 3

    # Stage 4 Offline
    s4 = run_stage_4(stage_1_input=s1, stage_2_input=s2, stage_3_input=s3, api_key="", save_production=False)
    assert isinstance(s4, Stage4FormatterOutput)
    assert "MACRORISK WEEKLY INTELLIGENCE REPORT" in s4.report_markdown

    # Stage 5 Offline
    s5 = fallback_baseline_retail_note(s1, s3)
    assert isinstance(s5, Stage5RetailFormatterOutput)
    assert s5.traffic_light_status in [TrafficLightStatus.GREEN, TrafficLightStatus.YELLOW, TrafficLightStatus.RED]
    assert len(s5.action_checklist) == 3


# =====================================================================
# 6. ANTI-HALLUCINATION FACT AUDITOR ADVERSARIAL STRESS TEST
# =====================================================================

def test_fact_auditor_adversarial_redaction():
    """Verify fact auditor redacts fabricated numbers when strict_redaction is enabled."""
    raw_kv = ModuleDataKV(
        module_1_plumbing=[KeyValueItem(key="TGA_BALANCE", value="$782.4B")]
    )

    # Prose contains verified $782.4B and fabricated $1234.5B
    report_text = "Verified cash is $782.4B. Hallucinated debt is $1234.5B."
    audit_res = audit_report_against_raw_kv(report_text, raw_kv, strict_redaction=True)

    assert audit_res.is_clean is False
    assert len(audit_res.hallucination_alerts) >= 1
    # Check that fabricated number received redaction tag
    assert "$1234.5B [UNVERIFIED_FIGURE]" in audit_res.sanitized_report_markdown
