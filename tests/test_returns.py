import numpy as np
import pandas as pd
import pytest

from analytics.returns import cagr, clean_series, daily_returns, trailing_return
from analytics.rolling_returns import rolling_returns


def test_hand_calculated_cagr():
    s = pd.Series([100, 121], index=pd.to_datetime(["2020-01-01", "2022-01-01"]))
    # 731 actual calendar days; the documented 365.25 convention gives 9.9928%.
    assert cagr(s) == pytest.approx(1.21 ** (365.25 / 731) - 1)
    assert cagr(s) == pytest.approx(0.10, abs=0.0001)


def test_daily_returns_and_gaps():
    s = pd.Series(
        [100, 110, 99, 108],
        index=pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06", "2025-01-08"]),
    )
    assert daily_returns(s).tolist() == pytest.approx([0.1, -0.1])


def test_calendar_period_not_row_count():
    dates = pd.bdate_range("2020-01-01", "2025-01-01")
    s = pd.Series(100 * 1.10 ** ((dates - dates[0]).days / 365.25), index=dates)
    assert trailing_return(s, 36) == pytest.approx(0.10)
    assert trailing_return(s.loc["2024-07-01":], 12) is None
    assert trailing_return(s, 12, "2025-02-01") is None


def test_rolling_known_compound_path():
    dates = pd.bdate_range("2018-01-01", "2025-01-01")
    s = pd.Series(100 * 1.10 ** ((dates - dates[0]).days / 365.25), index=dates)
    assert rolling_returns(s, 3).to_numpy() == pytest.approx(0.10)
    assert rolling_returns(s.iloc[:50], 1).empty
    assert rolling_returns(s, 5).index.min() >= pd.Timestamp("2023-01-01")


@pytest.mark.parametrize("values", [[0, 10], [np.nan, 10], [10, np.inf], [-5, 10]])
def test_invalid_prices_rejected(values):
    with pytest.raises(ValueError):
        clean_series(pd.Series(values, index=pd.date_range("2020-01-01", periods=2)))
