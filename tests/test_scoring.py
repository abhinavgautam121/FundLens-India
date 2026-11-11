import numpy as np
import pandas as pd
import pytest

from analytics.peer_analysis import peer_percentile
from analytics.scoring import composite_score, load_weights, validate_weights


def test_percentiles_ties_and_direction():
    s = pd.Series([10, 20, 30])
    assert peer_percentile(s).tolist() == [0, 50, 100]
    assert peer_percentile(s, higher_better=False).tolist() == [100, 50, 0]
    assert peer_percentile(pd.Series([1, 1, 1])).tolist() == [50, 50, 50]
    assert peer_percentile(s.iloc[:2]).isna().all()


def test_composite_hand_calculation():
    weights = load_weights()["default"]
    values = {"consistency": 80, "risk": 60, "benchmark": 100, "recency": 20}
    assert composite_score(values, weights) == pytest.approx(28 + 15 + 25 + 3)
    values["benchmark"] = np.nan
    assert composite_score(values, weights) is None
    weights["benchmark"] = 0
    weights["recency"] += 0.25
    assert composite_score(values, weights) is None  # Missing inputs still disclosed.


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        validate_weights(dict(consistency=0.5, risk=0.5, benchmark=0.2, recency=0.1))
