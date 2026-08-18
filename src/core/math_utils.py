"""
Module Name: math_utils.py
Repo Path: src/core/math_utils.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Deterministic Quantitative Math Engine and Severity Scoring.
- Formulas:
  1. ATM Straddle Implied Move: (ATM Call + ATM Put) / Underlying Spot * 100%
  2. VIX Curve Slope: M2 Future - M1 Future (Index Points)
  3. Event Severity Score: Algorithmic mapping [1-5 / 5] based on Tier and Asset Breadth.
"""

# Import typing primitives for strict type safety
from typing import Optional, Tuple

# Import MacroTier enum from schemas
from src.core.schemas import MacroTier


# Deterministic calculation of ATM Straddle Options Implied Move
def calculate_atm_straddle_implied_move(
    call_price: Optional[float],
    put_price: Optional[float],
    spot_price: Optional[float],
) -> str:
    """
    Calculates the options-implied percentage move from an ATM straddle.
    Formula: Implied Move (%) = (ATM Call + ATM Put) / Spot Price
    Returns: Formatted string (e.g. '±4.85%') or 'UNKNOWN' if inputs are missing/invalid.
    """
    # Verify that all three required pricing inputs are present and not None
    if call_price is None or put_price is None or spot_price is None:
        # Return UNKNOWN if any pricing component is missing
        return "UNKNOWN"

    # Verify that spot price is strictly positive to prevent division by zero
    if spot_price <= 0:
        # Return UNKNOWN if spot price is invalid
        return "UNKNOWN"

    # Verify call and put prices are non-negative
    if call_price < 0 or put_price < 0:
        # Return UNKNOWN if option prices are negative
        return "UNKNOWN"

    # Calculate total straddle cost (Call premium + Put premium)
    straddle_cost = call_price + put_price

    # Compute percentage move relative to spot price
    implied_pct = (straddle_cost / spot_price) * 100.0

    # Return formatted string with plus-minus symbol and 2 decimal precision
    return f"±{implied_pct:.2f}%"


# Deterministic calculation of VIX Futures Curve Slope
def calculate_vix_curve_slope_math(
    m1_future: Optional[float],
    m2_future: Optional[float],
) -> Tuple[Optional[float], str]:
    """
    Calculates VIX Term Structure Curve Slope: M2 - M1.
    Returns: Tuple of (raw_slope_float, formatted_string_with_regime).
    """
    # Verify both front month (M1) and second month (M2) future prices exist
    if m1_future is None or m2_future is None:
        # Return None and UNKNOWN if inputs are missing
        return None, "UNKNOWN"

    # Calculate spread in index points (M2 - M1)
    slope = m2_future - m1_future

    # Determine curve term structure regime
    if slope > 0.05:
        # Positive slope represents Contango
        regime = "Contango"
    elif slope < -0.05:
        # Negative slope represents Backwardation (volatility inversion/stress)
        regime = "Backwardation"
    else:
        # Near zero represents Flat term structure
        regime = "Flat"

    # Format string with signed float and regime designation
    formatted_str = f"{slope:+.2f} pts ({regime})"

    # Return raw numeric slope and formatted label
    return slope, formatted_str


# Algorithmic calculation of Event Severity Score (1 to 5 scale)
def calculate_event_severity_score(
    tier: MacroTier,
    is_marquee_release: bool = False,
    asset_classes_exposed_count: int = 1,
) -> int:
    """
    Computes deterministic event severity score (1-5 / 5) based on Algorithmic Priority Matrix.
    - Tier 1: Base 4/5 (Upgrades to 5/5 if Marquee FOMC/CPI/NFP or >= 3 assets exposed)
    - Tier 2: Base 3/5 (Upgrades to 4/5 if >= 3 assets exposed)
    - Tier 3: Base 1/5 (Upgrades to 2/5 if multiple assets exposed)
    """
    # Handle Tier 1 (Highest Priority)
    if tier == MacroTier.TIER_1:
        # If marquee event (FOMC Rate Decision, CPI, NFP) or broad contagion across 3+ asset classes
        if is_marquee_release or asset_classes_exposed_count >= 3:
            # Assign maximum severity score 5
            return 5
        # Standard Tier 1 catalyst
        return 4

    # Handle Tier 2 (Secondary Priority)
    elif tier == MacroTier.TIER_2:
        # If event impacts 3 or more asset classes simultaneously
        if asset_classes_exposed_count >= 3:
            # Assign elevated severity score 4
            return 4
        # Standard Tier 2 indicator
        return 3

    # Handle Tier 3 (Baseline Plumbing)
    else:
        # If plumbing event affects multiple markets
        if asset_classes_exposed_count >= 2:
            # Assign score 2
            return 2
        # Baseline single-market plumbing release
        return 1
