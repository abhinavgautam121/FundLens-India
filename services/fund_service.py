"""Point-in-time analytics service; the UI never calculates financial metrics."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sqlalchemy import select

from analytics.benchmark_analysis import benchmark_metrics
from analytics.peer_analysis import category_context
from analytics.returns import clean_series, coverage, period_series, trailing_return
from analytics.risk_metrics import risk_metrics
from analytics.rolling_returns import rolling_returns, rolling_summary
from analytics.scoring import COMPONENTS, score_frame
from database.connection import Metric, Snapshot


def price_series(
    frame: pd.DataFrame, id_column: str, code, date_column: str, value: str, as_of=None
) -> pd.Series:
    df = frame.loc[frame[id_column] == code].sort_values(date_column)
    return clean_series(
        pd.Series(df[value].to_numpy(), index=pd.to_datetime(df[date_column])), as_of
    )


def analyse(
    tables: dict,
    as_of,
    risk_free_rate: float,
    config: dict,
    minimum_peers: int = 3,
    minimum_coverage: float = 0.90,
) -> pd.DataFrame:
    as_of = pd.Timestamp(as_of)
    rows = []
    for _, scheme in tables["schemes"].iterrows():
        row = scheme.to_dict()
        nav = price_series(
            tables["nav_history"], "scheme_id", scheme.scheme_id, "nav_date", "nav", as_of
        )
        three = period_series(nav, 36, as_of)
        row.update(
            latest_nav=float(nav.iloc[-1]) if len(nav) else None,
            latest_date=nav.index[-1] if len(nav) else pd.NaT,
            observations=len(nav),
            data_coverage=coverage(three) if len(three) else 0,
            cumulative_return=float(nav.iloc[-1] / nav.iloc[0] - 1) if len(nav) > 1 else None,
            total_return_3y=float(three.iloc[-1] / three.iloc[0] - 1) if len(three) > 1 else None,
        )
        for months, key in [
            (1, "return_1m"),
            (3, "return_3m"),
            (6, "return_6m"),
            (12, "return_1y"),
            (36, "cagr_3y"),
            (60, "cagr_5y"),
        ]:
            row[key] = trailing_return(nav, months, as_of)
        row.update(risk_metrics(three, risk_free_rate))
        roll = rolling_returns(three, 1, as_of)
        summary = rolling_summary(roll)
        row.update({f"rolling_{k}": v for k, v in summary.items()})
        row["rolling_observations"] = len(roll)
        row["consistency_raw"] = (
            summary["median"] / (summary["p75"] - summary["p25"] + 0.01)
            if len(roll) >= 252
            else None
        )
        metadata_valid = (
            pd.notna(scheme.metadata_as_of) and pd.Timestamp(scheme.metadata_as_of) <= as_of
        )
        assigned_benchmark = scheme.benchmark_code if metadata_valid else None
        bench_def = tables["benchmarks"].loc[
            tables["benchmarks"].benchmark_code == assigned_benchmark
        ]
        bench_type = bench_def.iloc[0].benchmark_type if not bench_def.empty else None
        row["benchmark_type"] = bench_type
        benchmark = price_series(
            tables["benchmark_history"],
            "benchmark_code",
            assigned_benchmark,
            "benchmark_date",
            "tri_value",
            as_of,
        )
        if len(three):
            benchmark = benchmark.loc[three.index[0] : three.index[-1]]
        bm = (
            benchmark_metrics(three, benchmark, as_of)
            if bench_type == "TRI"
            else benchmark_metrics(pd.Series(dtype=float), pd.Series(dtype=float))
        )
        row.update(bm)
        row["benchmark_raw"] = (
            -bm["tracking_error"]
            if scheme.fund_type == "Passive" and bm["tracking_error"] is not None
            else bm["benchmark_win_rate"]
        )
        if not metadata_valid:
            # Never apply metadata from a future date to a historical cohort.
            row.update(
                {
                    key: None
                    for key in [
                        "amc_name",
                        "category",
                        "subcategory",
                        "fund_type",
                        "benchmark_code",
                        "inception_date",
                        "expense_ratio",
                        "aum",
                    ]
                }
            )
        row["metadata_valid"] = metadata_valid
        row["stale_days"] = (as_of - nav.index[-1]).days if len(nav) else None
        required = [row.get(k) for k in ("category", "subcategory", "fund_type", "benchmark_code")]
        row["eligible"] = bool(
            len(three) >= 500
            and all(pd.notna(v) for v in required)
            and metadata_valid
            and row["data_coverage"] >= minimum_coverage
            and len(roll) >= 252
            and row["stale_days"] <= 7
            and bench_type == "TRI"
            and bm["alignment_coverage"] >= minimum_coverage
        )
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows).replace([np.inf, -np.inf], np.nan)
    return score_frame(category_context(frame, minimum_peers), config, minimum_peers)


def parameter_payload(config: dict, risk_free_rate: float) -> str:
    settings = yaml.safe_load(Path("config/settings.yaml").read_text())
    return json.dumps(
        {"weights": config, "risk_free_rate": risk_free_rate, "settings": settings}, sort_keys=True
    )


def parameters_key(config: dict, risk_free_rate: float) -> str:
    payload = parameter_payload(config, risk_free_rate)
    return "1.0.0-" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def persist_analysis(
    factory, frame: pd.DataFrame, as_of, config: dict, risk_free_rate: float
) -> None:
    if frame.empty:
        return
    date = pd.Timestamp(as_of).date()
    version = parameters_key(config, risk_free_rate)

    def nullable(value):
        return float(value) if value is not None and pd.notna(value) else None

    with factory.begin() as session:
        for _, row in frame.iterrows():
            scheme_id = int(row.scheme_id)
            existing = session.scalar(
                select(Snapshot).where(
                    Snapshot.scheme_id == scheme_id,
                    Snapshot.snapshot_date == date,
                    Snapshot.methodology_version == version,
                )
            )
            snapshot = existing or Snapshot(
                scheme_id=scheme_id, snapshot_date=date, methodology_version=version
            )
            snapshot.parameters_json = parameter_payload(config, risk_free_rate)
            for key in ["research_score", "category_percentile"]:
                setattr(snapshot, key, nullable(row[key]))
            for component in COMPONENTS:
                setattr(
                    snapshot, f"{component}_component", nullable(row[f"{component}_contribution"])
                )
            session.add(snapshot)
            metric = session.scalar(
                select(Metric).where(
                    Metric.scheme_id == scheme_id,
                    Metric.calculation_date == date,
                    Metric.period == "3Y",
                    Metric.parameters == version,
                )
            )
            metric = metric or Metric(
                scheme_id=scheme_id, calculation_date=date, period="3Y", parameters=version
            )
            metric.parameters_json = parameter_payload(config, risk_free_rate)
            for key in [
                "annualised_volatility",
                "maximum_drawdown",
                "sharpe_ratio",
                "sortino_ratio",
                "benchmark_excess_return",
                "tracking_error",
                "tracking_difference",
                "data_coverage",
                "rolling_median",
                "benchmark_win_rate",
            ]:
                setattr(metric, key, nullable(row[key]))
            metric.cagr = nullable(row.cagr_3y)
            # Total return over the documented 3Y analytics horizon.
            metric.total_return = nullable(row.total_return_3y)
            session.add(metric)


def quality_report(tables: dict, analysis: pd.DataFrame, as_of) -> pd.DataFrame:
    issues = []
    if not analysis.empty:
        for _, row in analysis.iterrows():

            def add(message):
                issues.append(
                    {
                        "scheme_code": row.scheme_code,
                        "scheme_name": row.scheme_name,
                        "issue": message,
                    }
                )

            if not row.metadata_valid:
                add("Missing metadata at the selected analysis date")
            if pd.isna(row.cagr_3y):
                add("Insufficient three-year history")
            if row.data_coverage < 0.90:
                add(
                    f"Incomplete weekday coverage ({row.data_coverage:.1%}); exchange holidays are not modelled"
                )
            if pd.notna(row.stale_days) and row.stale_days > 7:
                add(f"Stale NAV relative to analysis date ({int(row.stale_days)} calendar days)")
            if row.benchmark_type != "TRI" or row.alignment_coverage < 0.90:
                add("Missing, non-TRI, or incompletely aligned benchmark")
            if pd.isna(row.research_score):
                add(f"Score withheld: {row.score_reason}")
            nav = price_series(
                tables["nav_history"], "scheme_id", row.scheme_id, "nav_date", "nav", as_of
            )
            if len(nav) > 1:
                missing = len(pd.bdate_range(nav.index[0], nav.index[-1]).difference(nav.index))
                if missing:
                    add(f"{missing} unobserved weekdays (may include exchange holidays)")
    return pd.DataFrame(issues, columns=["scheme_code", "scheme_name", "issue"])
