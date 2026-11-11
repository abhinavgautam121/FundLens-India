import numpy as np
import pandas as pd

from analytics.returns import cagr, clean_series, daily_returns
from analytics.rolling_returns import rolling_returns


def align_series(fund: pd.Series, benchmark: pd.Series, as_of=None) -> pd.DataFrame:
    return pd.concat(
        [
            clean_series(fund, as_of).rename("Fund"),
            clean_series(benchmark, as_of).rename("Benchmark"),
        ],
        axis=1,
    ).dropna()


def benchmark_metrics(fund: pd.Series, benchmark: pd.Series, as_of=None) -> dict:
    aligned = align_series(fund, benchmark, as_of)
    result = dict.fromkeys(
        [
            "fund_cagr",
            "benchmark_cagr",
            "benchmark_excess_return",
            "tracking_error",
            "tracking_difference",
            "benchmark_win_rate",
        ]
    )
    result["aligned_observations"] = len(aligned)
    expected = len(clean_series(fund, as_of))
    result["alignment_coverage"] = len(aligned) / expected if expected else 0.0
    if len(aligned) < 2 or (aligned.index[-1] - aligned.index[0]).days < 365:
        return result
    fc, bc = cagr(aligned.Fund), cagr(aligned.Benchmark)
    # Tracking difference is the difference of CAGRs on identical level dates.
    result.update(
        fund_cagr=fc,
        benchmark_cagr=bc,
        benchmark_excess_return=fc - bc,
        tracking_difference=fc - bc,
    )
    active = pd.concat(
        [daily_returns(aligned.Fund), daily_returns(aligned.Benchmark)], axis=1
    ).dropna()
    if len(active) >= 30:
        result["tracking_error"] = float(
            (active.iloc[:, 0] - active.iloc[:, 1]).std(ddof=1) * np.sqrt(252)
        )
    rolling = pd.concat(
        [rolling_returns(aligned.Fund), rolling_returns(aligned.Benchmark)], axis=1
    ).dropna()
    if len(rolling) >= 252:
        result["benchmark_win_rate"] = float((rolling.iloc[:, 0] > rolling.iloc[:, 1]).mean())
    return result
