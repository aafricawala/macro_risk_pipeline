"""
Unit Tests for Stage 5 Retail Schemas in src/core/schemas.py.
"""
from datetime import datetime, date
import pytest
from src.core.schemas import (
    TrafficLightStatus,
    RetailActionItem,
    Stage5RetailFormatterOutput,
)


def test_stage_5_retail_schema_instantiation():
    action1 = RetailActionItem(
        asset_bucket="Stocks (401k / IRA)",
        action_guidance="Favor broad market index funds; avoid concentrated bets on high-multiple tech."
    )

    output = Stage5RetailFormatterOutput(
        as_of_timestamp_et=datetime.now(),
        coverage_start_date=date(2026, 8, 18),
        coverage_end_date=date(2026, 9, 14),
        traffic_light_status=TrafficLightStatus.YELLOW,
        traffic_light_summary="Market environment is in cautious consolidation ahead of Fed policy announcements.",
        retail_report_markdown="# Retail Weekly Note\nMarket is yellow.",
        retail_file_path="./Production/Retail_Note.md",
        action_checklist=[action1]
    )

    assert output.traffic_light_status == TrafficLightStatus.YELLOW
    assert len(output.action_checklist) == 1
    assert "Stocks" in output.action_checklist[0].asset_bucket
