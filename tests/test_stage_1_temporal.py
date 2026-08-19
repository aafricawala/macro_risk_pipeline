"""
Unit Tests for Stage 1: Temporal Anchoring & Regime Engine.
"""
from datetime import datetime, date
import pytz
import pytest

from src.core.schemas import MacroTier, Stage1TemporalOutput
from src.stages.stage_1_temporal import (
    compute_calendar_windows,
    classify_macro_regime_routed,
    fallback_baseline_regime,
    run_stage_1,
)

def test_compute_calendar_windows_math():
    tz_et = pytz.timezone("America/New_York")
    fixed_dt = tz_et.localize(datetime(2026, 8, 18, 9, 30, 0))
    windows = compute_calendar_windows(anchor_dt=fixed_dt)
    assert windows.week_1.start_date == date(2026, 8, 18)
    assert windows.week_1.end_date == date(2026, 8, 24)
    assert windows.week_4.end_date == date(2026, 9, 14)

def test_fallback_baseline_regime():
    regime = fallback_baseline_regime(date(2026, 8, 18), date(2026, 8, 24))
    assert regime.tier == MacroTier.TIER_3
    assert "Baseline" in regime.dominant_theme

def test_classify_macro_regime_routed_mocked():
    tz_et = pytz.timezone("America/New_York")
    fixed_dt = tz_et.localize(datetime(2026, 8, 18, 9, 30, 0))
    regime, model_used = classify_macro_regime_routed(
        start_date=date(2026, 8, 18),
        end_date=date(2026, 8, 24),
        as_of_time=fixed_dt,
        api_key="mock_key",
    )
    assert regime.tier == MacroTier.TIER_1
    assert model_used == "gemini-3.7-flash"

def test_run_stage_1_degraded_end_to_end():
    tz_et = pytz.timezone("America/New_York")
    fixed_dt = tz_et.localize(datetime(2026, 8, 18, 9, 30, 0))
    result = run_stage_1(anchor_dt=fixed_dt, api_key="", save_artifact=False)
    assert isinstance(result, Stage1TemporalOutput)
    assert result.degraded_mode is True
    assert result.regime.tier == MacroTier.TIER_3
