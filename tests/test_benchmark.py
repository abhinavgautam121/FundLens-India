import numpy as np
import pandas as pd
import pytest

from analytics.benchmark_analysis import align_series, benchmark_metrics


def test_identical_fund_tracking():
    dates = pd.bdate_range("2020-01-01", "2025-01-01")
    s = pd.Series(
        100 * np.cumprod(1 + np.random.default_rng(1).normal(0.0004, 0.01, len(dates))), index=dates
    )
    bm = benchmark_metrics(s, s * 10)
    assert bm["tracking_error"] == pytest.approx(0, abs=1e-12)
    assert bm["tracking_difference"] == pytest.approx(0, abs=1e-12)
    assert bm["benchmark_cagr"] == pytest.approx(bm["fund_cagr"])


def test_alignment_has_no_forward_fill_or_future_dates():
    dates = pd.bdate_range("2024-01-01", periods=40)
    a = pd.Series(np.arange(40) + 100, index=dates)
    b = a.drop(dates[4])
    frame = align_series(a, b, dates[20])
    assert dates[4] not in frame.index
    assert frame.index.max() == dates[20]


def test_tracking_error_independent_daily_difference():
    dates = pd.bdate_range("2020-01-01", periods=800)
    r = np.tile([0.003, -0.002, 0.001, 0.004], 200)
    active = np.tile([0.001, -0.001, 0.002, -0.002], 200)
    # Include level zero so each supplied return has an observed previous level.
    fund = pd.Series(
        np.r_[100, 100 * np.cumprod(1 + r + active)], index=pd.bdate_range(dates[0], periods=801)
    )
    bench = pd.Series(np.r_[100, 100 * np.cumprod(1 + r)], index=fund.index)
    assert benchmark_metrics(fund, bench)["tracking_error"] == pytest.approx(
        np.std(active, ddof=1) * np.sqrt(252)
    )
