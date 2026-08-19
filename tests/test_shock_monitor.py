"""
Unit Tests for src/data/shock_monitor.py using Dependency Injection.
"""
import pytest
from src.core.schemas import ShockType, ShockMonitorResult
from src.data.shock_monitor import (
    scan_fdic_bank_failures,
    scan_newswire_breaking_shocks,
    scan_for_unscheduled_shocks,
)

def test_scan_fdic_bank_failure_detected():
    sample_data = [
        {
            "title": "FDIC Enters Receivership of Signature Bank",
            "summary": "State regulators closed the institution; FDIC assumes all deposits.",
            "link": "https://fdic.gov/news/press-releases/2026/pr123",
            "published": "2026-08-18"
        }
    ]
    shocks = scan_fdic_bank_failures(items_feed=sample_data)
    assert len(shocks) == 1
    assert shocks[0].shock_type == ShockType.BANK_FAILURE_FDIC
    assert shocks[0].severity_score == 5
    assert "Signature Bank" in shocks[0].title

def test_scan_newswire_sovereign_downgrade_detected():
    sample_data = [
        {
            "title": "Rating Agency Downgrades Sovereign Debt Outlook to Negative",
            "summary": "Fiscal deficit pressures lead to credit watch negative placement.",
            "link": "https://reuters.com/markets/123",
            "published": "2026-08-18"
        }
    ]
    shocks = scan_newswire_breaking_shocks(items_feed=sample_data)
    assert len(shocks) == 1
    assert shocks[0].shock_type == ShockType.SOVEREIGN_RATING_ACTION
    assert shocks[0].severity_score == 5

def test_scan_for_unscheduled_shocks_clean():
    res = scan_for_unscheduled_shocks()
    assert isinstance(res, ShockMonitorResult)
