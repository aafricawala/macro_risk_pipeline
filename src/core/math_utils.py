"""
Module Name: math_utils.py
Repo Path: src/core/math_utils.py

BCBS 239 Data Lineage & Compliance Standards:
- Role: Deterministic Quantitative Math Engine, Severity Scoring & Sentence-Boundary Truncation.
- Formulas:
  1. ATM Straddle Implied Move: (ATM Call + ATM Put) / Underlying Spot * 100%
  2. VIX Curve Slope: M2 Future - M1 Future (Index Points)
  3. Event Severity Score: Algorithmic mapping [1-5 / 5] based on Tier and Asset Breadth.
  4. Sentence-Boundary Truncation: Hard guardrail (<= 200 words) without mid-sentence cut-offs.
"""

# Import regular expressions module for sentence boundary splitting
import re

# Import typing primitives for strict type safety
from typing import Optional, Tuple, List

# Import MacroTier enum from schemas
from src.core.schemas import MacroTier


# Deterministic calculation of ATM Straddle Options Implied Move
def calculate_atm_straddle_implied_move(
    call_price: Optional[float],
    put_price: Optional[float],
    spot_price: Optional[float],
) -> str:
    """
    Calculates options-implied percentage move from an ATM straddle.
    Formula: Implied Move (%) = (ATM Call + ATM Put) / Spot Price
    """
    # Check if any required pricing component is None
    if call_price is None or put_price is None or spot_price is None:
        return "UNKNOWN"

    # Verify spot price is positive to avoid division by zero
    if spot_price <= 0:
        return "UNKNOWN"

    # Verify option prices are non-negative
    if call_price < 0 or put_price < 0:
        return "UNKNOWN"

    # Calculate total straddle cost (Call + Put)
    straddle_cost = call_price + put_price

    # Compute percentage move relative to spot price
    implied_pct = (straddle_cost / spot_price) * 100.0

    # Return formatted string with plus-minus symbol
    return f"±{implied_pct:.2f}%"


# Deterministic calculation of VIX Futures Curve Slope
def calculate_vix_curve_slope_math(
    m1_future: Optional[float],
    m2_future: Optional[float],
) -> Tuple[Optional[float], str]:
    """
    Calculates VIX Term Structure Curve Slope: M2 - M1.
    """
    # Verify both M1 and M2 future prices exist
    if m1_future is None or m2_future is None:
        return None, "UNKNOWN"

    # Calculate spread in index points (M2 - M1)
    slope = m2_future - m1_future

    # Determine curve term structure regime
    if slope > 0.05:
        regime = "Contango"
    elif slope < -0.05:
        regime = "Backwardation"
    else:
        regime = "Flat"

    # Format string with signed float and regime designation
    formatted_str = f"{slope:+.2f} pts ({regime})"

    # Return raw slope and formatted label
    return slope, formatted_str


# Algorithmic calculation of Event Severity Score (1 to 5 scale)
def calculate_event_severity_score(
    tier: MacroTier,
    is_marquee_release: bool = False,
    asset_classes_exposed_count: int = 1,
) -> int:
    """
    Computes deterministic event severity score (1-5 / 5) based on Priority Matrix.
    """
    # Check if event is Tier 1
    if tier == MacroTier.TIER_1:
        # Upgrade to 5 if marquee or broad cross-asset contagion
        if is_marquee_release or asset_classes_exposed_count >= 3:
            return 5
        return 4

    # Check if event is Tier 2
    elif tier == MacroTier.TIER_2:
        # Upgrade to 4 if affecting 3+ asset classes
        if asset_classes_exposed_count >= 3:
            return 4
        return 3

    # Tier 3 baseline plumbing
    else:
        if asset_classes_exposed_count >= 2:
            return 2
        return 1


# Deterministic Sentence-Boundary Truncation Guardrail (<= max_words, No Mid-Sentence Cuts)
def truncate_to_word_limit_clean(text: str, max_words: int = 200) -> str:
    """
    Enforces a strict word count limit (<= max_words) while preserving full sentence integrity.
    Never truncates mid-sentence; cleanly closes at the last valid sentence boundary (. / ! / ?).
    """
    # Strip whitespace from input text
    clean_text = text.strip()

    # Split text into word tokens
    words = clean_text.split()

    # If total word count is already within budget, return text unchanged
    if len(words) <= max_words:
        return clean_text

    # Split text into structural line blocks
    lines = clean_text.split("\n")

    # Container to collect validated output lines
    result_lines: List[str] = []

    # Counter to track accumulated word count
    accumulated_words = 0

    # Iterate through each line block
    for line in lines:
        stripped_line = line.strip()

        # Handle empty separator lines
        if not stripped_line:
            result_lines.append("")
            continue

        # Check if line is a markdown header or bullet prefix
        prefix = ""
        content = stripped_line

        if stripped_line.startswith(("#", "* **", "- **", "* ", "- ")):
            if ":" in stripped_line and not stripped_line.startswith("#"):
                parts = stripped_line.split(":", 1)
                prefix = parts[0] + ":"
                content = parts[1].strip()

        # Split content into distinct sentences using regex lookbehind
        sentences = re.split(r"(?<=[.!?])\s+", content)
        accepted_sentences: List[str] = []

        for sent in sentences:
            s_clean = sent.strip()
            if not s_clean:
                continue

            sent_word_count = len(s_clean.split()) + (len(prefix.split()) if not accepted_sentences and prefix else 0)

            if accumulated_words + sent_word_count <= max_words:
                accepted_sentences.append(s_clean)
                accumulated_words += sent_word_count
            else:
                break

        if accepted_sentences:
            rebuilt_line = " ".join(accepted_sentences)
            if prefix and not rebuilt_line.startswith(prefix):
                rebuilt_line = f"{prefix} {rebuilt_line}"
            result_lines.append(rebuilt_line)

        if accumulated_words >= max_words:
            break

    final_output = "\n".join(result_lines).strip()

    if not final_output:
        final_output = " ".join(words[:max_words]).rstrip(",;:-") + "."

    return final_output
