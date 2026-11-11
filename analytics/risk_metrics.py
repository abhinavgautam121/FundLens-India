import numpy as np
import pandas as pd

from analytics.returns import clean_series, daily_returns


def drawdown_series(series: pd.Series) -> pd.Series:
    s = clean_series(series)
    return (s / s.cummax() - 1).rename("Drawdown")


def risk_metrics(series: pd.Series, risk_free_rate: float = 0.06) -> dict:
    """Arithmetic daily excess mean / daily dispersion, annualised using 252.

    Daily target = (1 + annual rate) ** (1/252) - 1. Downside uses all daily
    observations in the denominator, with positive excess returns set to zero.
    """
    if not np.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("Annual risk-free rate must be finite and greater than -100%.")
    r = daily_returns(series)
    result = dict.fromkeys(
        [
            "annualised_volatility",
            "maximum_drawdown",
            "downside_deviation",
            "sharpe_ratio",
            "sortino_ratio",
        ]
    )
    if len(series) >= 2:
        result["maximum_drawdown"] = float(drawdown_series(series).min())
    if len(r) < 30:
        return result
    target = (1 + risk_free_rate) ** (1 / 252) - 1
    excess = r - target
    std = float(r.std(ddof=1))
    downside = float(np.sqrt(np.mean(np.minimum(excess, 0) ** 2)))
    result.update(
        annualised_volatility=std * np.sqrt(252),
        downside_deviation=downside * np.sqrt(252),
        sharpe_ratio=float(excess.mean() / std * np.sqrt(252)) if std > 1e-12 else None,
        sortino_ratio=float(excess.mean() / downside * np.sqrt(252)) if downside > 1e-12 else None,
    )
    return result
