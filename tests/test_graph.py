"""
Integration Tests for Master LangGraph StateGraph Orchestrator (src/graph.py).
"""
from datetime import datetime, date
from unittest.mock import patch, MagicMock
import pytz
import pytest

from src.core.schemas import Stage4FormatterOutput, Stage5RetailFormatterOutput
from src.graph import run_pipeline, build_macrorisk_graph


def test_build_macrorisk_graph_compilation_with_dual_audit():
    """Verify LangGraph compiles with all 6 nodes and convergent dual-auditor edge."""
    graph = build_macrorisk_graph()
    assert graph is not None
    assert "temporal_regime" in graph.nodes
    assert "market_plumbing_harvester" in graph.nodes
    assert "quant_synthesis" in graph.nodes
    assert "executive_formatter" in graph.nodes
    assert "retail_formatter" in graph.nodes
    assert "fact_auditor_critic" in graph.nodes


@patch("src.stages.stage_1_temporal.execute_dynamic_json_query")
@patch("src.stages.stage_2_harvester.execute_dynamic_json_query")
@patch("src.stages.stage_3_quant.execute_dynamic_json_query")
def test_run_pipeline_dual_audited_end_to_end_mocked(mock_s3, mock_s2, mock_s1):
    """Verify master LangGraph executes both branches and audits both documents."""
    tz_et = pytz.timezone("America/New_York")
    fixed_dt = tz_et.localize(datetime(2026, 8, 18, 9, 30, 0))

    mock_s1.return_value = (
        {
            "tier": "TIER_2",
            "dominant_theme": "Central Banking Policy Prelude",
            "rationale": "FOMC Minutes & Flash PMIs",
            "anchor_events": []
        },
        "gemini-3.7-flash"
    )

    mock_s2.return_value = (
        {
            "as_of_timestamp_et": "2026-08-18T09:30:00-04:00",
            "coverage_start_date": "2026-08-18",
            "coverage_end_date": "2026-09-14",
            "dominant_theme": "Central Banking Policy Prelude",
            "raw_kv_store": {
                "module_1_plumbing": [{"key": "TGA_BALANCE", "value": "$780B"}],
                "module_2_macro_surprises": [],
                "module_3_earnings": [],
                "module_4_derivatives": [{"key": "ZERO_GAMMA_LEVEL", "value": "UNKNOWN"}],
                "module_5_regulatory": [],
                "module_6_geopolitics": [],
                "module_7_narratives": [{"key": "NAAIM_EXPOSURE_INDEX", "value": "82.5"}]
            },
            "treasury_auctions_table": [],
            "central_bank_events_table": [],
            "earnings_bellwethers_table": [],
            "opex_and_gamma_table": [],
            "cot_positioning_table": [],
            "vix_term_structure_table": [],
            "audit_log_table": [],
            "degraded_mode": False,
            "audit_trace": []
        },
        "gemini-3.7-flash"
    )

    mock_s3.return_value = (
        {
            "as_of_timestamp_et": "2026-08-18T09:30:00-04:00",
            "coverage_start_date": "2026-08-18",
            "coverage_end_date": "2026-09-14",
            "dominant_theme": "Central Banking Policy Prelude",
            "vix_curve_slope_pts": "+0.75 pts (Contango)",
            "atm_straddle_implied_moves": [],
            "factor_rotations": [],
            "top_left_tail_risks": [],
            "top_right_tail_risks": [],
            "cross_asset_spillovers": [],
            "taleb_stress_test": {
                "systemic_shock_10pct_drawdown": "Credit spreads widen 50bps.",
                "idiosyncratic_liquidity_shock": "CTA unwinds trigger."
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
            "audit_trace": []
        },
        "gemini-3.7-flash"
    )

    final_output = run_pipeline(
        anchor_dt=fixed_dt,
        api_key="mock_key",
        save_artifacts=False
    )

    assert type(final_output).__name__ == "Stage4FormatterOutput"
    assert "MACRORISK WEEKLY INTELLIGENCE REPORT" in final_output.report_markdown
    assert any("Institutional Audit" in t for t in final_output.audit_trace)
    assert any("Retail Note Audit" in t for t in final_output.audit_trace)
