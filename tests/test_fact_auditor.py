"""
Unit Tests for src/core/fact_auditor.py.
"""
import pytest
from src.core.schemas import ModuleDataKV, KeyValueItem
from src.core.fact_auditor import (
    extract_raw_kv_text_corpus,
    audit_report_against_raw_kv,
)


def test_fact_auditor_verified_clean():
    raw_kv = ModuleDataKV(
        module_1_plumbing=[
            KeyValueItem(key="TGA_BALANCE", value="$782.4B as of August 14, 2026"),
            KeyValueItem(key="ON_RRP", value="$312.8B")
        ],
        module_2_macro_surprises=[
            KeyValueItem(key="CPI_HEADLINE", value="+2.8% YoY reported on 2026-08-14")
        ]
    )

    report_text = "The Treasury General Account stood at $782.4B with ON RRP at $312.8B and CPI at +2.8% on 2026-08-14."
    result = audit_report_against_raw_kv(report_text, raw_kv)

    assert result.is_clean is True
    assert len(result.hallucination_alerts) == 0
    assert result.verified_matches >= 3


def test_fact_auditor_flags_hallucinated_figures():
    raw_kv = ModuleDataKV(
        module_1_plumbing=[KeyValueItem(key="TGA_BALANCE", value="$782.4B")]
    )

    report_text = "TGA balance closed at $782.4B. Fabricated metric is $999.5B and +9.9%."
    result = audit_report_against_raw_kv(report_text, raw_kv)

    assert result.is_clean is False
    assert len(result.hallucination_alerts) >= 1
    assert any("$999.5B" in alert for alert in result.hallucination_alerts)
