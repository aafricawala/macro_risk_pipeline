"""
Unit Tests for Stage 2 Pydantic Schemas in src/core/schemas.py.
"""
from datetime import datetime, date
import pytest
from src.core.schemas import (
    EpistemicTag,
    KeyValueItem,
    TreasuryAuctionRow,
    AuditLogRow,
    ModuleDataKV,
    Stage2HarvesterOutput
)

def test_audit_log_row_schema_validation():
    row = AuditLogRow(
        rank=1,
        load_bearing_claim="Fed balance sheet contracted by $15B.",
        search_query="site:federalreserve.gov H.4.1",
        retrieved_snippet="Total assets declined to $6.82T.",
        source_url="federalreserve.gov",
        retrieval_timestamp_US_Eastern="2026-08-18 09:30:00 ET",
        confidence_score=0.95,
        epistemic_tag=EpistemicTag.VERIFIED_OFFICIAL,
    )
    assert row.rank == 1
    assert row.confidence_score == 0.95

def test_stage_2_harvester_output_defaults():
    kv = ModuleDataKV(
        module_1_plumbing=[KeyValueItem(key="TGA_BALANCE", value="$780B")],
        module_7_narratives=[KeyValueItem(key="TARIFF_STANCE", value="Steel quotas [VERIFIED_OFFICIAL]")]
    )
    output = Stage2HarvesterOutput(
        as_of_timestamp_et=datetime.now(),
        coverage_start_date=date(2026, 8, 18),
        coverage_end_date=date(2026, 9, 14),
        dominant_theme="Central Banking Policy Prelude",
        raw_kv_store=kv,
    )
    assert output.dominant_theme == "Central Banking Policy Prelude"
    assert output.raw_kv_store.module_1_plumbing[0].key == "TGA_BALANCE"
