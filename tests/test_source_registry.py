"""
Unit Tests for src/data/source_registry.py.
Verifies registration of all 47 public macro endpoints across 7 categories.
"""
import pytest
from src.data.source_registry import (
    SourceCategory,
    SourceEndpoint,
    get_all_registered_sources,
    get_endpoints_by_category,
)


def test_registry_contains_exact_47_sources():
    """Verify that the registry contains exactly 47 validated public endpoints."""
    all_sources = get_all_registered_sources()
    assert len(all_sources) == 47
    assert all(isinstance(s, SourceEndpoint) for s in all_sources)


def test_registry_categories_coverage():
    """Verify that all 7 institutional categories contain registered sources."""
    for cat in SourceCategory:
        sources_in_cat = get_endpoints_by_category(cat)
        assert len(sources_in_cat) >= 1, f"Category {cat.value} has no registered sources!"


def test_fdic_and_reuters_rss_flags():
    """Verify that FDIC and newswires are flagged with RSS capability for shock detection."""
    all_sources = {s.name: s for s in get_all_registered_sources()}
    assert all_sources["FDIC_Press_Releases"].is_rss is True
    assert all_sources["Reuters_RSS_index"].is_rss is True
    assert "https://" in all_sources["TradingEconomics"].url
