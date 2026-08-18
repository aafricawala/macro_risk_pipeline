"""
Unit Tests for Stage 4: Executive Formatter & Serialization.
"""
from datetime import datetime, date
import pytz
import pytest

from src.core.schemas import (
    MacroTier,
    EpistemicTag,
    DateWindow,
    WeeklyCalendarWindows,
    AnchorEvent,
    DominantThemeClassification,
    Stage1TemporalOutput,
    Stage2HarvesterOutput,
    Stage3QuantSynthesisOutput,
    Stage4FormatterOutput,
    ModuleDataKV,
    KeyValueItem,
    TalebStressTest,
    TacticalScenario,
)
from src.stages.stage_4_formatter import (
    serialize_table_to_csv,
    render_section_2_risk_matrix,
    render_section_3_calendar,
    render_section_6_appendices,
    run_stage_4,
)


def create_mock_pipeline_states():
    tz_et = pytz.timezone("America/New_York")
    now_et = datetime.now(pytz.utc).astimezone(tz_et)
    start_d = date(2026, 8, 18)
    end_d = date(2026, 9, 14)

    w1 = DateWindow(week_number=1, start_date=start_d, end_date=date(2026, 8, 24), label="W1")
    w2 = DateWindow(week_number=2, start_date=date(2026, 8, 25), end_date=date(2026, 8, 31), label="W2")
    w3 = DateWindow(week_number=3, start_date=date(2026, 9, 1), end_date=date(2026, 9, 7), label="W3")
    w4 = DateWindow(week_number=4, start_date=date(2026, 9, 8), end_date=end_d, label="W4")
    windows = WeeklyCalendarWindows(week_1=w1, week_2=w2, week_3=w3, week_4=w4)

    regime = DominantThemeClassification(
        tier=MacroTier.TIER_2,
        dominant_theme="Central Banking Policy Prelude",
        rationale="FOMC Minutes & PMIs",
        anchor_events=[
            AnchorEvent(
                event_name="FOMC Minutes Release",
                event_date=date(2026, 8, 19),
                tier=MacroTier.TIER_2,
                source_citation="federalreserve.gov",
            )
        ]
    )
    s1 = Stage1TemporalOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        windows=windows,
        regime=regime
    )

    s2 = Stage2HarvesterOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        dominant_theme="Central Banking Policy Prelude",
        raw_kv_store=ModuleDataKV(),
    )

    s3 = Stage3QuantSynthesisOutput(
        as_of_timestamp_et=now_et,
        coverage_start_date=start_d,
        coverage_end_date=end_d,
        dominant_theme="Central Banking Policy Prelude",
        vix_curve_slope_pts="+0.75 pts (Contango)",
        taleb_stress_test=TalebStressTest(
            systemic_shock_10pct_drawdown="Credit spreads widen.",
            idiosyncratic_liquidity_shock="CTA stop triggers."
        ),
        tactical_scenarios=[
            TacticalScenario(
                scenario_name="Base Case",
                probability_pct="60%",
                core_thesis="Steady growth.",
                multi_asset_positioning="Neutral duration."
            )
        ]
    )
    return s1, s2, s3


def test_serialize_table_to_csv_null_state():
    """Verify empty rows return single row with N/A."""
    csv_str = serialize_table_to_csv([], ["col_a", "col_b"], "test.csv")
    assert "# Filename: test.csv" in csv_str
    assert "col_a,col_b" in csv_str
    assert "N/A,N/A" in csv_str


def test_render_section_3_calendar_null_states():
    """Verify weeks without catalysts output the standardized null-state bullet."""
    s1, s2, s3 = create_mock_pipeline_states()
    cal_md = render_section_3_calendar(s1, s2)
    assert "#### WEEK 1:" in cal_md
    assert "#### WEEK 2:" in cal_md
    assert "#### WEEK 3:" in cal_md
    assert "#### WEEK 4:" in cal_md
    assert "* No Tier-1/Tier-2 catalysts identified across current calendar horizon" in cal_md


def test_run_stage_4_end_to_end():
    """Verify complete Stage 4 formatting output."""
    s1, s2, s3 = create_mock_pipeline_states()
    out = run_stage_4(stage_1_input=s1, stage_2_input=s2, stage_3_input=s3, api_key="", save_production=False)
    assert isinstance(out, Stage4FormatterOutput)
    assert "MACRORISK WEEKLY INTELLIGENCE REPORT" in out.report_markdown
    assert "SECTION 1:" in out.report_markdown
    assert "SECTION 6:" in out.report_markdown
    assert "```csv" in out.report_markdown
