"""
Unit Tests for Stage 3: Quant Synthesis & Taleb Stress Tester.
"""
from datetime import datetime, date
from unittest.mock import patch
import pytz
import pytest

from src.core.schemas import (
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
    ModuleDataKV,
    KeyValueItem,
    VixTermStructureRow,
    TailRiskCategory,
)
from src.stages.stage_3_quant import (
    calculate_vix_curve_slope,
    fallback_baseline_synthesis,
    run_stage_3,
)


def create_sample_stage_2_output() -> Stage2HarvesterOutput:
    tz_et = pytz.timezone("America/New_York")
    now_et = datetime.now(pytz.utc).astimezone(tz_et)
    return Stage2HarvesterOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=date(2026, 8, 18),
        coverage_end_date=date(2026, 9, 14),
        dominant_theme="Central Banking Policy Prelude",
        raw_kv_store=ModuleDataKV(
            module_1_plumbing=[KeyValueItem(key="TGA_BALANCE", value="$780B")],
            module_4_derivatives=[KeyValueItem(key="ZERO_GAMMA_LEVEL", value="UNKNOWN")]
        ),
        vix_term_structure_table=[
            VixTermStructureRow(
                as_of_date="2026-08-18",
                spot_vix="15.00",
                m1_future="15.80",
                m2_future="16.55",
                m3_future="17.10",
                curve_slope_m1_m2="+0.75",
                source_url="cboe.com",
                retrieval_timestamp_US_Eastern="2026-08-18 09:30:00 ET"
            )
        ]
    )


def test_calculate_vix_curve_slope_math():
    """Verify deterministic math formula for VIX slope: M2 - M1."""
    s2_input = create_sample_stage_2_output()
    slope_str = calculate_vix_curve_slope(s2_input)
    assert "+0.75 pts (Contango)" in slope_str


def test_fallback_baseline_synthesis_structure():
    """Verify baseline synthesis contains 3 left tail and 3 right tail risks."""
    s2_input = create_sample_stage_2_output()
    s3_output = fallback_baseline_synthesis(s2_input)

    assert isinstance(s3_output, Stage3QuantSynthesisOutput)
    assert s3_output.degraded_mode is True
    assert len(s3_output.top_left_tail_risks) == 3
    assert len(s3_output.top_right_tail_risks) == 3
    assert len(s3_output.tactical_scenarios) == 3
    assert s3_output.top_left_tail_risks[0].category == TailRiskCategory.LEFT_TAIL
    assert s3_output.top_right_tail_risks[0].category == TailRiskCategory.RIGHT_TAIL


@patch("src.stages.stage_3_quant.execute_dynamic_json_query")
def test_run_stage_3_mocked_success(mock_execute_query):
    """Verify run_stage_3 parses mocked dynamic JSON response."""
    s2_input = create_sample_stage_2_output()
    mock_payload = {
        "as_of_timestamp_et": "2026-08-18T09:30:00-04:00",
        "coverage_start_date": "2026-08-18",
        "coverage_end_date": "2026-09-14",
        "dominant_theme": "Central Banking Policy Prelude",
        "vix_curve_slope_pts": "+0.75 pts (Contango)",
        "atm_straddle_implied_moves": [],
        "factor_rotations": [],
        "top_left_tail_risks": [
            {
                "category": "LEFT_TAIL",
                "rank": 1,
                "catalyst_event": "Jackson Hole Hawkish Surprise",
                "date_horizon": "2026-08-21",
                "est_prob_pct": "30%",
                "direct_impact_asset": "US 10Y Yield",
                "spillover_vector": "Rates push higher",
                "desk_hedging_stance": "Long Put Spreads"
            }
        ],
        "top_right_tail_risks": [
            {
                "category": "RIGHT_TAIL",
                "rank": 1,
                "catalyst_event": "Soft Landing Confirmation",
                "date_horizon": "Rolling 4 Weeks",
                "est_prob_pct": "45%",
                "direct_impact_asset": "SPX Beta",
                "spillover_vector": "Multiple expansion",
                "desk_hedging_stance": "Call Ladders"
            }
        ],
        "cross_asset_spillovers": [],
        "taleb_stress_test": {
            "systemic_shock_10pct_drawdown": "Credit spreads widen 50bps.",
            "idiosyncratic_liquidity_shock": "CTA unwinds accelerate."
        },
        "tactical_scenarios": [
            {
                "scenario_name": "Base Case",
                "probability_pct": "60%",
                "core_thesis": "Growth remains steady.",
                "multi_asset_positioning": "Neutral duration."
            }
        ],
        "degraded_mode": False,
        "audit_trace": ["Synthesized successfully."]
    }
    mock_execute_query.return_value = (mock_payload, "gemini-3.7-flash")

    result = run_stage_3(stage_2_input=s2_input, api_key="mock_key", save_artifact=False)

    assert result.dominant_theme == "Central Banking Policy Prelude"
    assert result.vix_curve_slope_pts == "+0.75 pts (Contango)"
    assert len(result.top_left_tail_risks) == 1
    assert result.degraded_mode is False
