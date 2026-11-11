from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from analytics.peer_analysis import PEER_KEYS, peer_percentile

COMPONENTS = ("consistency", "risk", "benchmark", "recency")


def load_weights(path="config/scoring_weights.yaml") -> dict:
    with Path(path).open() as file:
        config = yaml.safe_load(file)
    validate_weights(config["default"])
    for weights in config.get("categories", {}).values():
        validate_weights(weights)
    return config


def validate_weights(weights: dict) -> None:
    if set(weights) != set(COMPONENTS):
        raise ValueError("Supply consistency, risk, benchmark and recency weights.")
    values = list(weights.values())
    if not all(np.isfinite(v) and v >= 0 for v in values) or not np.isclose(sum(values), 1):
        raise ValueError("Weights must be finite, non-negative, and sum to 100%.")


def composite_score(components: dict, weights: dict) -> float | None:
    validate_weights(weights)
    if any(components.get(k) is None or not np.isfinite(components[k]) for k in COMPONENTS):
        return None
    if any(not 0 <= components[k] <= 100 for k in COMPONENTS):
        raise ValueError("Normalised component scores must be between 0 and 100.")
    return float(sum(components[k] * weights[k] for k in COMPONENTS))


def profile_label(score) -> str:
    if score is None or not np.isfinite(score):
        return "Insufficient data"
    if score >= 75:
        return "Strong relative profile"
    if score >= 50:
        return "Above-median profile"
    if score >= 25:
        return "Mixed profile"
    return "Below-median profile"


def score_frame(frame: pd.DataFrame, config: dict, minimum: int = 3) -> pd.DataFrame:
    frame = frame.copy()
    for component in COMPONENTS:
        frame[f"{component}_component"] = float("nan")
        frame[f"{component}_contribution"] = float("nan")
    frame["research_score"] = float("nan")
    frame["score_peer_count"] = 0
    frame["score_reason"] = "Insufficient history, metadata, coverage, or benchmark alignment"
    # Use a complete peer cohort for every component: no changing denominators or missing weights.
    inputs = ["consistency_raw", "sortino_ratio", "benchmark_raw", "return_1y"]
    complete = frame.loc[frame.eligible].dropna(subset=inputs)
    for _, group in complete.groupby(PEER_KEYS, dropna=True):
        frame.loc[group.index, "score_peer_count"] = len(group)
        if len(group) < minimum:
            frame.loc[group.index, "score_reason"] = (
                f"At least {minimum} complete comparable peers required"
            )
            continue
        weights = config.get("categories", {}).get(group.iloc[0].category, config["default"])
        validate_weights(weights)
        for component, raw in zip(COMPONENTS, inputs, strict=True):
            percentiles = peer_percentile(group[raw], minimum)
            frame.loc[group.index, f"{component}_component"] = percentiles
            frame.loc[group.index, f"{component}_contribution"] = percentiles * weights[component]
        for idx in group.index:
            components = {k: frame.loc[idx, f"{k}_component"] for k in COMPONENTS}
            frame.loc[idx, "research_score"] = composite_score(components, weights)
            frame.loc[idx, "score_reason"] = "Complete comparable peer cohort"
    frame["profile"] = frame.research_score.map(profile_label)
    return frame
