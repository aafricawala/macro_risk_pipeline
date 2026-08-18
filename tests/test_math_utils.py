"""
Unit Tests for src/core/math_utils.py.
Verifies ATM Straddle formulas, VIX Slope calculations, and Severity Scoring.
"""
import pytest
from src.core.schemas import MacroTier
from src.core.math_utils import (
    calculate_atm_straddle_implied_move,
    calculate_vix_curve_slope_math,
    calculate_event_severity_score,
)


def test_atm_straddle_implied_move_valid():
    """Verify exact formula: (Call + Put) / Spot * 100%."""
    # Test case: SPX spot=5000, Call=120, Put=130 -> Straddle=250 -> 250/5000 = 5.00%
    result = calculate_atm_straddle_implied_move(call_price=120.0, put_price=130.0, spot_price=5000.0)
    assert result == "±5.00%"

    # Test case: NVDA spot=125, Call=4.5, Put=4.2 -> Straddle=8.7 -> 8.7/125 = 6.96%
    result_nvda = calculate_atm_straddle_implied_move(call_price=4.5, put_price=4.2, spot_price=125.0)
    assert result_nvda == "±6.96%"


def test_atm_straddle_implied_move_unknown_fallback():
    """Verify missing or invalid inputs return UNKNOWN per v14.6 rule."""
    assert calculate_atm_straddle_implied_move(None, 10.0, 100.0) == "UNKNOWN"
    assert calculate_atm_straddle_implied_move(10.0, None, 100.0) == "UNKNOWN"
    assert calculate_atm_straddle_implied_move(10.0, 10.0, None) == "UNKNOWN"
    assert calculate_atm_straddle_implied_move(10.0, 10.0, 0.0) == "UNKNOWN"
    assert calculate_atm_straddle_implied_move(-5.0, 10.0, 100.0) == "UNKNOWN"


def test_vix_curve_slope_contango_and_backwardation():
    """Verify VIX Slope M2 - M1 math and regime classification."""
    # Contango: M1=15.50, M2=16.25 -> Slope=+0.75 pts
    slope, label = calculate_vix_curve_slope_math(m1_future=15.50, m2_future=16.25)
    assert slope == pytest.approx(0.75)
    assert label == "+0.75 pts (Contango)"

    # Backwardation (Inversion): M1=22.00, M2=19.50 -> Slope=-2.50 pts
    slope_inv, label_inv = calculate_vix_curve_slope_math(m1_future=22.00, m2_future=19.50)
    assert slope_inv == pytest.approx(-2.50)
    assert label_inv == "-2.50 pts (Backwardation)"

    # Missing inputs
    slope_none, label_none = calculate_vix_curve_slope_math(None, 16.0)
    assert slope_none is None
    assert label_none == "UNKNOWN"


def test_calculate_event_severity_score():
    """Verify algorithmic 1-5 severity mapping."""
    # Tier 1 marquee event (FOMC/CPI) -> 5/5
    assert calculate_event_severity_score(MacroTier.TIER_1, is_marquee_release=True) == 5

    # Tier 1 standard event -> 4/5
    assert calculate_event_severity_score(MacroTier.TIER_1, is_marquee_release=False, asset_classes_exposed_count=1) == 4

    # Tier 2 multi-asset event -> 4/5
    assert calculate_event_severity_score(MacroTier.TIER_2, asset_classes_exposed_count=3) == 4

    # Tier 2 standard event -> 3/5
    assert calculate_event_severity_score(MacroTier.TIER_2, asset_classes_exposed_count=1) == 3

    # Tier 3 plumbing event -> 1/5 or 2/5
    assert calculate_event_severity_score(MacroTier.TIER_3, asset_classes_exposed_count=1) == 1
    assert calculate_event_severity_score(MacroTier.TIER_3, asset_classes_exposed_count=2) == 2
