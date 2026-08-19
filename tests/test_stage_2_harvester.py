"""
Unit Tests for Stage 2: Market Plumbing & Catalyst Harvester.
"""
from datetime import datetime, date
import pytz
import pytest

from src.core.schemas import (
    MacroTier, DateWindow, WeeklyCalendarWindows,
    DominantThemeClassification, Stage1TemporalOutput, Stage2HarvesterOutput
)
from src.stages.stage_2_harvester import (
    fallback_baseline_harvester,
    run_stage_2,
)

def create_sample_stage_1_output() -> Stage1TemporalOutput:
    tz_et = pytz.timezone("America/New_York")
    now_et = datetime.now(pytz.utc).astimezone(tz_et)
    start_d = date(2026, 8, 18)
    end_d = date(2026, 9, 14)
    w = DateWindow(week_number=1, start_date=start_d, end_date=date(2026, 8, 24), label="W1")
    windows = WeeklyCalendarWindows(week_1=w, week_2=w, week_3=w, week_4=w)
    regime = DominantThemeClassification(
        tier=MacroTier.TIER_2,
        dominant_theme="Central Banking Policy Prelude",
        rationale="FOMC Minutes & PMIs",
        anchor_events=[]
    )
    return Stage1TemporalOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        windows=windows,
        regime=regime
    )

def test_fallback_baseline_harvester_v14_rules():
    s1_input = create_sample_stage_1_output()
    s2_output = fallback_baseline_harvester(s1_input)
    assert isinstance(s2_output, Stage2HarvesterOutput)
    assert s2_output.degraded_mode is True
    assert any(kv.key == "ZERO_GAMMA_LEVEL" and kv.value == "UNKNOWN" for kv in s2_output.raw_kv_store.module_4_derivatives)

def test_run_stage_2_mocked_success():
    s1_input = create_sample_stage_1_output()
    result = run_stage_2(stage_1_input=s1_input, api_key="mock_key", save_artifact=False)
    assert result.dominant_theme == "Central Banking Policy Prelude"
    assert result.degraded_mode is False
    assert any(kv.key == "TGA_BALANCE" for kv in result.raw_kv_store.module_1_plumbing)
