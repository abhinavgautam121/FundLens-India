import numpy as np
import pandas as pd
import pytest

from analytics.risk_metrics import drawdown_series, risk_metrics


def test_drawdown_hand_calculation():
    s = pd.Series([100, 120, 90, 110], index=pd.bdate_range("2025-01-01", periods=4))
    assert drawdown_series(s).min() == pytest.approx(-0.25)


def test_volatility_sharpe_sortino_independent_calculation():
    r = np.tile([0.01, -0.02, 0.015, -0.005], 20)
    s = pd.Series(
        np.r_[100, 100 * np.cumprod(1 + r)], index=pd.bdate_range("2024-01-01", periods=len(r) + 1)
    )
    metrics = risk_metrics(s, 0.06)
    target = 1.06 ** (1 / 252) - 1
    excess = r - target
    downside = np.sqrt(np.sum(np.minimum(excess, 0) ** 2) / len(r))
    assert metrics["annualised_volatility"] == pytest.approx(np.std(r, ddof=1) * np.sqrt(252))
    assert metrics["sharpe_ratio"] == pytest.approx(
        np.mean(excess) / np.std(r, ddof=1) * np.sqrt(252)
    )
    assert metrics["sortino_ratio"] == pytest.approx(np.mean(excess) / downside * np.sqrt(252))
    assert metrics["downside_deviation"] == pytest.approx(downside * np.sqrt(252))


def test_insufficient_and_zero_dispersion():
    short = pd.Series([100, 101], index=pd.bdate_range("2024-01-01", periods=2))
    assert risk_metrics(short)["sharpe_ratio"] is None
    flat = pd.Series(100, index=pd.bdate_range("2024-01-01", periods=100))
    assert risk_metrics(flat, 0)["sortino_ratio"] is None
    assert risk_metrics(flat, 0)["sharpe_ratio"] is None
