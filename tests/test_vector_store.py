"""
Unit Tests for src/core/vector_store.py.
"""
import pytest
from src.core.schemas import EpistemicTag
from src.data.source_registry import SourceCategory
from src.core.vector_store import (
    index_macro_documents,
    query_macro_context,
)


def test_chromadb_index_and_query_flow():
    """Verify document upsert and metadata-filtered semantic retrieval."""
    test_docs = [
        {
            "id": "fed_test_001",
            "text": "The Federal Open Market Committee noted that balance sheet runoff continues at scheduled pace.",
            "source_name": "Fed_H4.1",
            "category": SourceCategory.CENTRAL_BANKING.value,
            "as_of_date": "2026-08-18",
            "epistemic_tag": EpistemicTag.VERIFIED_OFFICIAL.value,
        },
        {
            "id": "tga_test_002",
            "text": "Daily Treasury Statement confirms operating cash balance in the Federal Reserve account closed at $782.4B.",
            "source_name": "Treasury_Auctions",
            "category": SourceCategory.TREASURY_AND_YIELDS.value,
            "as_of_date": "2026-08-18",
            "epistemic_tag": EpistemicTag.VERIFIED_OFFICIAL.value,
        },
        {
            "id": "earnings_test_003",
            "text": "NVIDIA scheduled second quarter fiscal 2027 financial results conference call.",
            "source_name": "Nvidia_IR",
            "category": SourceCategory.CORPORATE_AND_EARNINGS.value,
            "as_of_date": "2026-08-18",
            "epistemic_tag": EpistemicTag.VERIFIED_OFFICIAL.value,
        }
    ]

    indexed_count = index_macro_documents(test_docs, collection_name="test_macro_collection")
    assert indexed_count == 3

    cb_results = query_macro_context(
        query_text="balance sheet runoff and reserves",
        n_results=1,
        category_filter=SourceCategory.CENTRAL_BANKING.value,
        collection_name="test_macro_collection"
    )
    assert len(cb_results) == 1
    assert "Federal Open Market Committee" in cb_results[0]["text"]
    assert cb_results[0]["metadata"]["source_name"] == "Fed_H4.1"

    tga_results = query_macro_context(
        query_text="Treasury cash balance closing amount",
        n_results=1,
        category_filter=SourceCategory.TREASURY_AND_YIELDS.value,
        collection_name="test_macro_collection"
    )
    assert len(tga_results) == 1
    assert "$782.4B" in tga_results[0]["text"]


def test_chromadb_empty_query_fallback():
    """Verify empty search results handle gracefully without crashing."""
    res = query_macro_context(
        query_text="completely unrelated query string 12345",
        n_results=1,
        category_filter=SourceCategory.SECTOR_AND_COMMODITY.value,
        collection_name="test_empty_collection"
    )
    assert isinstance(res, list)
