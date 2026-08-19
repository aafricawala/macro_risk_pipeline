"""
Unit Tests for Stage 5 Retail Formatter (src/stages/stage_5_retail.py).
"""
from datetime import datetime, date
from unittest.mock import patch, MagicMock
import pytz
import pytest

from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    DateWindow,
    WeeklyCalendarWindows,
    AnchorEvent,
    DominantThemeClassification,
    Stage1TemporalOutput,
    Stage3QuantSynthesisOutput,
    Stage5RetailFormatterOutput,
    TrafficLightStatus,
    TalebStressTest,
    TacticalScenario,
)
from src.stages.stage_5_retail import (
    determine_traffic_light_status,
    fallback_baseline_retail_note,
    run_stage_5,
)


def create_mock_s1_and_s3():
    tz_et = pytz.timezone("America/New_York")
    now_et = datetime.now(pytz.utc).astimezone(tz_et)
    start_d = date(2026, 8, 18)
    end_d = date(2026, 9, 14)

    w1 = DateWindow(week_number=1, start_date=start_d, end_date=date(2026, 8, 24), label="W1")
    windows = WeeklyCalendarWindows(week_1=w1, week_2=w1, week_3=w1, week_4=w1)
    regime = DominantThemeClassification(
        tier=MacroTier.TIER_2,
        dominant_theme="Central Banking Policy Prelude",
        rationale="FOMC Minutes & PMIs",
        anchor_events=[]
    )
    s1 = Stage1TemporalOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        windows=windows,
        regime=regime
    )

    s3 = Stage3QuantSynthesisOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        dominant_theme="Central Banking Policy Prelude",
        vix_curve_slope_pts="+0.75 pts (Contango)",
        taleb_stress_test=TalebStressTest(
            systemic_shock_10pct_drawdown="Credit spreads widen.",
            idiosyncratic_liquidity_shock="CTA stop triggers."
        ),
        tactical_scenarios=[
            TacticalScenario(
                scenario_name="Base Case",
                probability_pct="60%",
                core_thesis="Steady growth.",
                multi_asset_positioning="Neutral duration."
            )
        ]
    )
    return s1, s3


def test_determine_traffic_light_status_logic():
    s1, s3 = create_mock_s1_and_s3()
    # Contango -> GREEN
    status, summary = determine_traffic_light_status(s3)
    assert status == TrafficLightStatus.GREEN

    # Backwardation -> RED
    s3.vix_curve_slope_pts = "-2.50 pts (Backwardation)"
    status_red, _ = determine_traffic_light_status(s3)
    assert status_red == TrafficLightStatus.RED


def test_fallback_baseline_retail_note_structure():
    s1, s3 = create_mock_s1_and_s3()
    out = fallback_baseline_retail_note(s1, s3)

    assert isinstance(out, Stage5RetailFormatterOutput)
    assert "MACRORISK WEEKLY RETAIL NOTE" in out.retail_report_markdown
    assert "Jargon Buster" in out.retail_report_markdown
    assert len(out.action_checklist) == 3


def test_run_stage_5_end_to_end_degraded():
    s1, s3 = create_mock_s1_and_s3()
    result = run_stage_5(stage_1_input=s1, stage_3_input=s3, api_key="", save_production=False)

    assert isinstance(result, Stage5RetailFormatterOutput)
    assert result.traffic_light_status in [TrafficLightStatus.GREEN, TrafficLightStatus.YELLOW, TrafficLightStatus.RED]
    assert len(result.action_checklist) >= 1
