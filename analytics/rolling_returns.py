import numpy as np
import pandas as pd

from analytics.returns import clean_series


def rolling_returns(series: pd.Series, years: int = 1, as_of=None) -> pd.Series:
    """For each end date, use the last NAV on/before the calendar anniversary.

    A start more than seven calendar days before that anniversary is ineligible.
    Returns longer than one year are annualised by actual elapsed days.
    """
    s = clean_series(series, as_of)
    if s.empty:
        return pd.Series(dtype=float, name=f"{years}Y rolling return")
    targets = s.index - pd.DateOffset(years=years)
    pos = s.index.searchsorted(targets, side="right") - 1
    valid = pos >= 0
    safe = np.maximum(pos, 0)
    start_dates = s.index[safe]
    valid &= (targets - start_dates).days <= 7
    days = (s.index - start_dates).days.to_numpy()
    ratio = s.to_numpy() / s.to_numpy()[safe]
    exponent = np.divide(365.25, days, out=np.ones(len(s)), where=days > 0)
    values = ratio**exponent - 1 if years > 1 else ratio - 1
    return pd.Series(values[valid], index=s.index[valid], name=f"{years}Y rolling return")


def rolling_summary(returns: pd.Series) -> dict:
    if returns.empty:
        return {k: None for k in ("median", "best", "worst", "p25", "p75")}
    return {
        "median": float(returns.median()),
        "best": float(returns.max()),
        "worst": float(returns.min()),
        "p25": float(returns.quantile(0.25)),
        "p75": float(returns.quantile(0.75)),
    }
