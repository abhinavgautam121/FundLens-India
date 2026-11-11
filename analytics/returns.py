"""Calendar-aware returns: no interpolation, backfill, or future observations."""

import numpy as np
import pandas as pd


def clean_series(series: pd.Series, as_of=None) -> pd.Series:
    s = series.copy().astype(float)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    if as_of is not None:
        s = s.loc[: pd.Timestamp(as_of)]
    if s.index.has_duplicates:
        raise ValueError("Duplicate dates must be resolved before analytics.")
    if s.isna().any() or (~np.isfinite(s)).any() or (s <= 0).any():
        raise ValueError("Prices must be finite, positive, and non-missing.")
    return s


def daily_returns(series: pd.Series) -> pd.Series:
    """Only consecutive business-day observations; gaps are not treated as daily returns.

    Weekends are excluded. Exchange holidays cannot be inferred without a calendar.
    """
    s = clean_series(series)
    r = s.pct_change(fill_method=None)
    if len(s) < 2:
        return r.dropna()
    gaps = np.busday_count(
        s.index[:-1].values.astype("datetime64[D]"), s.index[1:].values.astype("datetime64[D]")
    )
    r.iloc[1:] = r.iloc[1:].where(gaps == 1)
    return r.dropna()


def cagr(series: pd.Series) -> float | None:
    s = clean_series(series)
    if len(s) < 2:
        return None
    days = (s.index[-1] - s.index[0]).days
    return float((s.iloc[-1] / s.iloc[0]) ** (365.25 / days) - 1) if days > 0 else None


def period_series(series: pd.Series, months: int, as_of=None) -> pd.Series:
    s = clean_series(series, as_of)
    if s.empty:
        return s
    end = pd.Timestamp(as_of) if as_of is not None else s.index[-1]
    if (end - s.index[-1]).days > 7:
        return s.iloc[:0]
    target = end - pd.DateOffset(months=months)
    prior = s.loc[:target]
    if prior.empty or (target - prior.index[-1]).days > 7:
        return s.iloc[:0]
    return s.loc[prior.index[-1] :]


def trailing_return(series: pd.Series, months: int, as_of=None) -> float | None:
    s = period_series(series, months, as_of)
    if len(s) < 2:
        return None
    return cagr(s) if months > 12 else float(s.iloc[-1] / s.iloc[0] - 1)


def coverage(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    expected = len(pd.bdate_range(series.index[0], series.index[-1]))
    observed = int((series.index.dayofweek < 5).sum())
    return min(observed / max(expected, 1), 1.0)
