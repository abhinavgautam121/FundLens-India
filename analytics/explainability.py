"""Deterministic statements describe changes; they do not infer market causes."""

import numpy as np


def explain_changes(before: dict, after: dict) -> list[str]:
    result = []
    metrics = [
        ("annualised_volatility", "Annualised volatility", 100, "percentage points"),
        ("maximum_drawdown", "Maximum drawdown", 100, "percentage points"),
        ("benchmark_excess_return", "Benchmark excess CAGR", 100, "percentage points"),
        ("category_percentile", "Category percentile", 1, "percentile points"),
        ("research_score", "Research score", 1, "points"),
        ("consistency_raw", "Rolling-return stability ratio", 1, "ratio units"),
        ("benchmark_win_rate", "Benchmark rolling win rate", 100, "percentage points"),
    ]
    for key, label, scale, unit in metrics:
        a, b = before.get(key), after.get(key)
        if a is None or b is None or not np.isfinite(a) or not np.isfinite(b):
            result.append(
                f"{label}: change unavailable because at least one date lacks eligible data."
            )
            continue
        delta = (b - a) * scale
        if abs(delta) < 0.005:
            result.append(f"{label} was broadly unchanged.")
        else:
            direction = "increased" if delta > 0 else "decreased"
            result.append(
                f"{label} {direction} by {abs(delta):.2f} {unit} ({a * scale:.2f} to {b * scale:.2f})."
            )
    return result
