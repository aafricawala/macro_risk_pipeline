"""
Unit Tests for src/core/schemas.py
Verifies Pydantic v2 data models and date-order validation rules.
"""

# Import date type for testing date fields
from datetime import date

# Import pytest to check for expected errors
import pytest

# Import ValidationError from Pydantic to test invalid data inputs
from pydantic import ValidationError

# Import the models we created in schemas.py
from src.core.schemas import DateWindow, MacroTier, EpistemicTag, AnchorEvent


def test_date_window_valid():
    """Verify that a valid DateWindow instance is successfully created."""
    # Create a valid DateWindow for Week 1
    window = DateWindow(
        week_number=1,
        start_date=date(2026, 8, 18),
        end_date=date(2026, 8, 24),
        label="WEEK 1: 2026-08-18 to 2026-08-24"
    )
    # Check that week_number is stored correctly as 1
    assert window.week_number == 1
    # Check that start_date matches what was provided
    assert window.start_date == date(2026, 8, 18)
    # Check that end_date matches what was provided
    assert window.end_date == date(2026, 8, 24)


def test_date_window_invalid_order():
    """Verify that end_date occurring before start_date raises a ValidationError."""
    # Tell pytest that we expect a ValidationError to be raised inside this block
    with pytest.raises(ValidationError):
        # Attempt to create an invalid DateWindow where end_date is before start_date
        DateWindow(
            week_number=1,
            start_date=date(2026, 8, 24),
            end_date=date(2026, 8, 18),  # Invalid: before start_date
            label="Invalid Window"
        )


def test_anchor_event_defaults():
    """Verify default values on AnchorEvent model."""
    # Create an AnchorEvent without specifying optional defaults
    event = AnchorEvent(
        event_name="FOMC Interest Rate Decision",
        event_date=date(2026, 8, 20),
        tier=MacroTier.TIER_1,
        source_citation="federalreserve.gov"
    )
    # Check that default epistemic tag is VERIFIED_OFFICIAL
    assert event.epistemic_tag == EpistemicTag.VERIFIED_OFFICIAL
    # Check that default verification status is True
    assert event.is_verified is True
