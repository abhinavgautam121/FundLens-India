import pandas as pd

PEER_KEYS = ["category", "subcategory", "fund_type", "benchmark_code"]


def peer_percentile(values: pd.Series, minimum: int = 3, higher_better: bool = True) -> pd.Series:
    """Average-rank percentile with endpoints 0 and 100; ties share their rank.

    For fewer than minimum non-missing finite values, every result is unavailable.
    """
    valid = (
        pd.to_numeric(values, errors="coerce")
        .replace([float("inf"), -float("inf")], float("nan"))
        .dropna()
    )
    out = pd.Series(float("nan"), index=values.index)
    if len(valid) >= max(minimum, 2):
        out.loc[valid.index] = (
            (valid.rank(method="average", ascending=higher_better) - 1) / (len(valid) - 1) * 100
        )
    return out


def category_context(frame: pd.DataFrame, minimum: int = 3) -> pd.DataFrame:
    frame = frame.copy()
    frame["category_percentile"] = float("nan")
    frame["category_rank"] = float("nan")
    frame["peer_count"] = 0
    frame["category_median_return"] = float("nan")
    for _, group in frame.loc[frame.eligible].groupby(PEER_KEYS, dropna=True):
        idx = group.index
        frame.loc[idx, "peer_count"] = len(group)
        frame.loc[idx, "category_percentile"] = peer_percentile(group.cagr_3y, minimum)
        if len(group) >= minimum:
            frame.loc[idx, "category_rank"] = group.cagr_3y.rank(ascending=False, method="min")
            frame.loc[idx, "category_median_return"] = group.cagr_3y.median()
    return frame
