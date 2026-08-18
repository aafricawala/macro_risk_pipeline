"""
Unit Tests for src/data/public_macro_api.py.
Verifies Fiscal Data REST parsing and fallback handling.
"""
from unittest.mock import patch, MagicMock
import pytest

from src.core.schemas import TreasuryAuctionRow
from src.data.public_macro_api import (
    fetch_live_tga_balance,
    fetch_live_treasury_auctions,
    collect_live_public_macro_data,
)


@patch("requests.get")
def test_fetch_live_tga_balance_mocked_success(mock_get):
    """Verify parsing of Fiscal Data DTS Table 1 JSON response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "record_date": "2026-08-14",
                "open_today_bal": "782410",
                "account_type": "Treasury General Account (TGA) Closing Balance"
            }
        ]
    }
    mock_get.return_value = mock_resp

    tga_str, rec_date = fetch_live_tga_balance()
    assert "[VERIFIED_OFFICIAL]" in tga_str
    assert "$782.4B" in tga_str
    assert rec_date == "2026-08-14"


@patch("requests.get")
def test_fetch_live_treasury_auctions_mocked_success(mock_get):
    """Verify parsing of Fiscal Data Auctions query response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [
            {
                "record_date": "2026-08-19",
                "security_type": "Bond",
                "security_term": "20-Year",
                "offering_amt": "16000000000",
                "issue_date": "2026-08-31"
            }
        ]
    }
    mock_get.return_value = mock_resp

    auctions = fetch_live_treasury_auctions()
    assert len(auctions) == 1
    assert isinstance(auctions[0], TreasuryAuctionRow)
    assert auctions[0].term == "20-Year"
    assert auctions[0].offering_size_usd == "$16.0B"


def test_public_macro_api_fallback_on_network_error():
    """Verify collector returns baseline plumbing values if government API times out."""
    with patch("requests.get", side_effect=Exception("Connection Timeout")):
        plumbing_kv, auctions = collect_live_public_macro_data()
        assert "TGA_BALANCE" in plumbing_kv
        assert len(auctions) >= 1
        assert isinstance(auctions[0], TreasuryAuctionRow)
