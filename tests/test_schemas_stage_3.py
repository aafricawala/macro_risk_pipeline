"""
Unit Tests for Stage 3 Pydantic Schemas.
"""
from datetime import datetime, date
import pytest
from src.core.schemas import (
    TailRiskCategory,
    TailRiskItem,
    FactorRotationRegime,
    TalebStressTest,
    TacticalScenario,
    Stage3QuantSynthesisOutput,
)


def test_stage_3_tail_risk_item():
    item = TailRiskItem(
        category=TailRiskCategory.LEFT_TAIL,
        rank=1,
        catalyst_event="Hawkish Jackson Hole Keynote",
        date_horizon="2026-08-21",
        est_prob_pct="35%",
        direct_impact_asset="US 10Y Yield",
        spillover_vector="Real rates spike -> Tech multiple compression",
        desk_hedging_stance="Long SPX 1M 25-delta Put Spreads",
    )
    assert item.rank == 1
    assert item.category == TailRiskCategory.LEFT_TAIL


def test_stage_3_quant_synthesis_output():
    out = Stage3QuantSynthesisOutput(
        as_of_timestamp_et=datetime.now(),
        coverage_start_date=date(2026, 8, 18),
        coverage_end_date=date(2026, 9, 14),
        dominant_theme="Jackson Hole Guidance",
        vix_curve_slope_pts="+0.75 pts (Contango)",
        top_left_tail_risks=[],
        top_right_tail_risks=[],
        taleb_stress_test=TalebStressTest(
            systemic_shock_10pct_drawdown="Dealer balance sheets widen spreads by 25bps.",
            idiosyncratic_liquidity_shock="CTA stop triggers breached below 200-DMA."
        ),
        tactical_scenarios=[
            TacticalScenario(
                scenario_name="Base Case",
                probability_pct="60%",
                core_thesis="Fed signals balanced trajectory.",
                multi_asset_positioning="Neutral duration, Overweight Quality."
            )
        ]
    )
    assert out.vix_curve_slope_pts == "+0.75 pts (Contango)"
    assert len(out.tactical_scenarios) == 1
