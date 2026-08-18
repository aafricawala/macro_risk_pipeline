"""
Unit Tests for Stage 2: Market Plumbing & Catalyst Harvester.
"""
from datetime import datetime, date
from unittest.mock import patch
import pytz
import pytest

from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    DateWindow,
    WeeklyCalendarWindows,
    DominantThemeClassification,
    Stage1TemporalOutput,
    Stage2HarvesterOutput,
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
    assert any(item.key == "ZERO_GAMMA_LEVEL" and item.value == "UNKNOWN" for item in s2_output.raw_kv_store.module_4_derivatives)
    assert len(s2_output.audit_log_table) >= 1

@patch("src.stages.stage_2_harvester.execute_dynamic_json_query")
def test_run_stage_2_mocked_success(mock_execute_query):
    s1_input = create_sample_stage_1_output()
    mock_payload = {
        "as_of_timestamp_et": "2026-08-18T09:30:00-04:00",
        "coverage_start_date": "2026-08-18",
        "coverage_end_date": "2026-09-14",
        "dominant_theme": "Central Banking Policy Prelude",
        "raw_kv_store": {
            "module_1_plumbing": [{"key": "TGA_BALANCE", "value": "$750B"}],
            "module_2_macro_surprises": [],
            "module_3_earnings": [],
            "module_4_derivatives": [{"key": "ZERO_GAMMA_LEVEL", "value": "UNKNOWN"}],
            "module_5_regulatory": [],
            "module_6_geopolitics": [],
            "module_7_narratives": [{"key": "LEADERSHIP_STATEMENT", "value": "Tariff review [VERIFIED_OFFICIAL]"}]
        },
        "treasury_auctions_table": [],
        "central_bank_events_table": [],
        "earnings_bellwethers_table": [],
        "opex_and_gamma_table": [],
        "cot_positioning_table": [],
        "vix_term_structure_table": [],
        "audit_log_table": [
            {
                "rank": 1,
                "load_bearing_claim": "TGA balance at $750B",
                "search_query": "site:fiscaldata.treasury.gov TGA balance",
                "retrieved_snippet": "Closing balance $750B",
                "source_url": "fiscaldata.treasury.gov",
                "retrieval_timestamp_US_Eastern": "2026-08-18 09:30:00 ET",
                "confidence_score": 0.98,
                "epistemic_tag": "[VERIFIED_OFFICIAL]"
            }
        ],
        "degraded_mode": False,
        "audit_trace": ["Harvested successfully."]
    }
    mock_execute_query.return_value = (mock_payload, "gemini-3.7-flash")
    result = run_stage_2(stage_1_input=s1_input, api_key="mock_key", save_artifact=False)
    assert result.dominant_theme == "Central Banking Policy Prelude"
    assert result.raw_kv_store.module_1_plumbing[0].value == "$750B"
    assert len(result.audit_log_table) == 1
