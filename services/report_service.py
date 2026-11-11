import io
import json
import zipfile

import pandas as pd

from analytics.returns import cagr, period_series
from analytics.risk_metrics import risk_metrics

DISCLAIMER = (
    "FundLens India is an independent educational mutual fund analytics prototype. "
    "It is not affiliated with or endorsed by PowerUp Money, AMFI, SEBI or any asset management company. "
    "Its analytical scores are experimental research indicators and do not constitute investment advice "
    "or recommendations. Past performance does not guarantee future results. Verify all data and consult "
    "a qualified, appropriately registered professional before making investment decisions."
)


def csv_bytes(frame: pd.DataFrame) -> bytes:
    """Escape spreadsheet formula prefixes on textual cells in downloaded data."""
    safe = frame.copy()
    for col in safe.select_dtypes(include=["object", "string"]).columns:
        safe[col] = safe[col].map(
            lambda v: (
                "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v
            )
        )
    return safe.to_csv(index=False).encode("utf-8-sig")


def analytical_report(row: dict, as_of, risk_free_rate: float, demo: bool) -> str:
    lines = [
        "# FundLens India — analytical report",
        "",
        f"Dataset: {'DEMO DATA — fictional synthetic series' if demo else 'User-imported data'}",
        f"Analysis date: {as_of}",
        f"Fund: {row['scheme_name']}",
        f"Code: {row['scheme_code']}",
        f"Annual risk-free assumption: {risk_free_rate:.2%}",
        "",
        "Risk and benchmark metrics use a trailing three-year horizon. Returns use calendar periods.",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key in [
        "return_1m",
        "return_3m",
        "return_6m",
        "return_1y",
        "cagr_3y",
        "cagr_5y",
        "annualised_volatility",
        "maximum_drawdown",
        "sharpe_ratio",
        "sortino_ratio",
        "benchmark_excess_return",
        "tracking_error",
        "tracking_difference",
        "data_coverage",
        "category_percentile",
        "peer_count",
        "score_peer_count",
        "research_score",
    ]:
        value = row.get(key)
        text = f"{value:.6f}" if value is not None and pd.notna(value) else "Unavailable"
        lines.append(f"| {key} | {text} |")
    lines.extend(
        [
            "",
            "Returns and volatility are decimal fractions; ratios and score are unitless.",
            f"Profile: {row.get('profile')}",
            f"Score eligibility: {row.get('score_reason')}",
            "",
            "## Component contributions (points)",
            "",
        ]
    )
    for key in ("consistency", "risk", "benchmark", "recency"):
        value = row.get(f"{key}_contribution")
        lines.append(
            f"- {key}: {value:.4f}"
            if value is not None and pd.notna(value)
            else f"- {key}: Unavailable"
        )
    lines.extend(
        [
            "",
            "Peer selection, formula definitions and limitations: docs/METHODOLOGY.md.",
            "No causal market explanation is inferred from these descriptive metrics.",
            "",
            DISCLAIMER,
        ]
    )
    return "\n".join(lines)


def powerbi_frames(tables: dict, as_of=None) -> dict[str, pd.DataFrame]:
    schemes = tables["schemes"].copy()
    categories = (
        schemes[["category", "subcategory"]].drop_duplicates().dropna().reset_index(drop=True)
    )
    categories["category_id"] = categories.index + 1
    dim = schemes.merge(categories, on=["category", "subcategory"], how="left")
    nav = tables["nav_history"].copy()
    benchmarks = tables["benchmark_history"].copy()
    metrics = tables["calculated_metrics"].copy()
    snapshots = tables["rating_snapshots"].copy()
    if as_of is not None:
        for frame, date in [
            (nav, "nav_date"),
            (benchmarks, "benchmark_date"),
            (metrics, "calculation_date"),
            (snapshots, "snapshot_date"),
        ]:
            if not frame.empty:
                frame.drop(
                    frame.index[pd.to_datetime(frame[date]) > pd.Timestamp(as_of)], inplace=True
                )
    all_dates = pd.concat([nav.nav_date, benchmarks.benchmark_date]).dropna()
    dates = (
        pd.DataFrame({"date": pd.date_range(all_dates.min(), all_dates.max())})
        if len(all_dates)
        else pd.DataFrame({"date": pd.to_datetime([])})
    )
    dates["date_key"] = dates.date.dt.strftime("%Y%m%d")
    dates["year"] = dates.date.dt.year
    dates["month"] = dates.date.dt.month
    dates["quarter"] = dates.date.dt.quarter
    benchmark_metrics = []
    for code, group in benchmarks.groupby("benchmark_code"):
        s = pd.Series(
            group.tri_value.to_numpy(), index=pd.to_datetime(group.benchmark_date)
        ).sort_index()
        end = pd.Timestamp(as_of) if as_of is not None else s.index[-1]
        three = period_series(s, 36, end)
        benchmark_metrics.append(
            {
                "benchmark_code": code,
                "calculation_date": end.date(),
                "period": "3Y",
                "cagr": cagr(three),
                **{
                    k: v
                    for k, v in risk_metrics(three, 0).items()
                    if k in {"annualised_volatility", "maximum_drawdown"}
                },
            }
        )
    return {
        "dim_fund": dim,
        "dim_category": categories,
        "dim_date": dates,
        "dim_benchmark": tables["benchmarks"],
        "fact_daily_nav": nav,
        "fact_fund_metrics": metrics,
        "fact_benchmark_levels": benchmarks,
        "fact_benchmark_metrics": pd.DataFrame(benchmark_metrics),
        "fact_research_snapshots": snapshots,
    }


def powerbi_zip(tables: dict, as_of, demo: bool) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, frame in powerbi_frames(tables, as_of).items():
            archive.writestr(f"{name}.csv", csv_bytes(frame))
        archive.writestr(
            "manifest.json",
            json.dumps(
                {
                    "as_of": str(as_of),
                    "demo_data": demo,
                    "disclaimer": DISCLAIMER,
                    "metric_period": "3Y",
                    "fact_benchmark_metrics_grain": "one benchmark per analysis date, trailing 3Y",
                    "parameters": "Full weights, risk-free assumption and settings are retained in fact parameters_json columns.",
                },
                indent=2,
            ),
        )
    return buffer.getvalue()
