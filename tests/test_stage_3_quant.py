"""
Unit Tests for Stage 3: Quant Synthesis & Taleb Stress Tester.
"""
from datetime import datetime, date
from unittest.mock import patch
import pytz
import pytest

from src.core.schemas import (
    Stage2HarvesterOutput, Stage3QuantSynthesisOutput,
    ModuleDataKV, KeyValueItem, VixTermStructureRow, FactorRotationRegime
)
from src.stages.stage_3_quant import (
    compute_vix_slope_from_stage_2,
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

def test_compute_vix_slope_from_stage_2():
    s2_input = create_sample_stage_2_output()
    slope_str = compute_vix_slope_from_stage_2(s2_input)
    assert "+0.75 pts (Contango)" in slope_str

def test_fallback_baseline_synthesis_structure():
    s2_input = create_sample_stage_2_output()
    s3_output = fallback_baseline_synthesis(s2_input)
    assert isinstance(s3_output, Stage3QuantSynthesisOutput)
    assert s3_output.degraded_mode is True
    assert len(s3_output.top_left_tail_risks) == 3

def test_run_stage_3_mocked_success():
    s2_input = create_sample_stage_2_output()
    result = run_stage_3(stage_2_input=s2_input, api_key="mock_key", save_artifact=False)
    assert result.dominant_theme == "Central Banking Policy Prelude"
    assert "+0.75 pts (Contango)" in result.vix_curve_slope_pts
    assert len(result.top_left_tail_risks) == 1
    assert result.degraded_mode is False
