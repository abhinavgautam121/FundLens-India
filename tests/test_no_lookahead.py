import pandas as pd
import pytest

from analytics.scoring import load_weights
from database.connection import connect
from services.data_service import read_tables
from services.demo_data import seed_demo
from services.fund_service import analyse, persist_analysis


@pytest.fixture(scope="module")
def demo(tmp_path_factory):
    engine, factory = connect(f"sqlite:///{tmp_path_factory.mktemp('demo')}/test.db")
    seed_demo(factory)
    return engine, factory, read_tables(engine)


def test_future_nav_and_benchmark_do_not_change_historical_analysis(demo):
    _, _, tables = demo
    config = load_weights()
    base = analyse(tables, "2025-10-30", 0.06, config)
    changed = {k: v.copy() for k, v in tables.items()}
    changed["nav_history"].loc[
        changed["nav_history"].nav_date > pd.Timestamp("2025-10-30"), "nav"
    ] *= 20
    changed["benchmark_history"].loc[
        changed["benchmark_history"].benchmark_date > pd.Timestamp("2025-10-30"), "tri_value"
    ] *= 40
    check = analyse(changed, "2025-10-30", 0.06, config)
    pd.testing.assert_frame_equal(base, check)


def test_future_metadata_is_not_applied_to_past(demo):
    _, _, tables = demo
    changed = {k: v.copy() for k, v in tables.items()}
    changed["schemes"]["metadata_as_of"] = pd.Timestamp("2026-10-01")
    result = analyse(changed, "2025-10-30", 0.06, load_weights())
    assert result.research_score.isna().all()
    assert not result.eligible.any()


def test_demo_quality_scores_and_idempotent_snapshots(demo):
    engine, factory, tables = demo
    config = load_weights()
    frame = analyse(tables, "2026-10-30", 0.06, config)
    assert len(frame) == 24
    assert frame.research_score.notna().sum() >= 18
    assert frame.loc[frame.scheme_code == "DEMO-E-8", "research_score"].isna().all()
    assert frame.loc[frame.scheme_code == "DEMO-D-4", "research_score"].isna().all()
    for _ in range(2):
        persist_analysis(factory, frame, "2026-10-30", config, 0.06)
    snapshots = read_tables(engine)["rating_snapshots"]
    assert len(snapshots) == 24
    rated = snapshots.dropna(subset=["research_score"])
    assert rated.research_score.to_numpy() == pytest.approx(
        rated[
            ["consistency_component", "risk_component", "benchmark_component", "recency_component"]
        ]
        .sum(axis=1)
        .to_numpy()
    )
