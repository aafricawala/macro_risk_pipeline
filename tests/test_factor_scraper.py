"""
Unit Tests for src/data/factor_scraper.py.
Verifies return calculation, regime state assignment, and fallback resilience.
"""
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.core.schemas import FactorRotationRegime
from src.data.factor_scraper import (
    compute_return_pct,
    fetch_factor_etf_spreads,
)


def test_compute_return_pct_math():
    """Verify return percentage calculation formula."""
    # Prices: 100 -> 105 -> return = +5.0%
    assert compute_return_pct([100.0, 105.0]) == pytest.approx(5.0)

    # Prices: 50 -> 45 -> return = -10.0%
    assert compute_return_pct([50.0, 45.0]) == pytest.approx(-10.0)

    # Empty or single price edge cases
    assert compute_return_pct([]) == 0.0
    assert compute_return_pct([100.0]) == 0.0


@patch("yfinance.download")
def test_fetch_factor_etf_spreads_mocked_success(mock_yf_download):
    """Verify live spread calculations and regime assignment with mocked price dataframe."""
    # Build mock multi-index DataFrame mimicking yfinance output
    dates = pd.date_range("2026-08-10", periods=5)
    tickers = ["MTUM", "VLUE", "QUAL", "USMV", "IWM", "SPY"]
    
    # Create test prices where MTUM outperforms VLUE, QUAL outperforms USMV, SPY outperforms IWM
    mock_data = {
        ("Close", "MTUM"): [100.0, 101.0, 102.0, 103.0, 104.0],  # +4.0%
        ("Close", "VLUE"): [100.0, 100.2, 100.5, 100.8, 101.0],  # +1.0% (Spread: +3.0%)
        ("Close", "QUAL"): [50.0, 50.5, 51.0, 51.5, 52.0],        # +4.0%
        ("Close", "USMV"): [50.0, 50.1, 50.2, 50.3, 50.5],        # +1.0% (Spread: +3.0%)
        ("Close", "IWM"):  [200.0, 199.0, 198.0, 197.0, 196.0],   # -2.0%
        ("Close", "SPY"):  [500.0, 502.0, 504.0, 506.0, 510.0],   # +2.0% (Spread: -4.0%)
    }
    df = pd.DataFrame(mock_data, index=dates)
    mock_yf_download.return_value = df

    regimes = fetch_factor_etf_spreads()

    assert len(regimes) == 3
    assert "Momentum Leadership" in regimes[0].regime_state
    assert "+3.00%" in regimes[0].spread_observation

    assert "Quality Leadership" in regimes[1].regime_state
    assert "+3.00%" in regimes[1].spread_observation

    assert "Large-Cap Dominance" in regimes[2].regime_state
    assert "-4.00%" in regimes[2].spread_observation


def test_fetch_factor_etf_spreads_fallback_on_network_error():
    """Verify scraper gracefully returns baseline regimes if network/API fails."""
    with patch("yfinance.download", side_effect=Exception("Network Connection Timeout")):
        regimes = fetch_factor_etf_spreads()
        assert len(regimes) == 3
        assert isinstance(regimes[0], FactorRotationRegime)
        assert "Momentum" in regimes[0].factor_pair
