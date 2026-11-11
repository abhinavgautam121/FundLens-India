import pandas as pd
import plotly.express as px
import streamlit as st

from analytics.benchmark_analysis import align_series
from analytics.returns import daily_returns, period_series
from analytics.risk_metrics import drawdown_series
from analytics.rolling_returns import rolling_returns, rolling_summary
from pages.common import benchmark_for, empty_guard, fmt, fund_picker, nav_for, score_notice, table
from services.report_service import analytical_report
from visualizations.charts import contributions, line_chart, rolling_distribution, style


def render(ctx):
    st.title("Fund Deep Dive")
    st.caption("Follow the evidence from NAV history to the experimental research score.")
    if empty_guard(ctx):
        return
    row = fund_picker(ctx)
    nav = nav_for(ctx, row)
    if nav.empty:
        st.info("No NAV observations exist on or before this analysis date.")
        return
    score_notice(row)
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["1Y return", "3Y CAGR", "Annualised volatility · 3Y", "Research score / 100"],
        [
            fmt(row.return_1y, True),
            fmt(row.cagr_3y, True),
            fmt(row.annualised_volatility, True),
            fmt(row.research_score, decimals=1),
        ],
        strict=True,
    ):
        col.metric(label, value)
    tabs = st.tabs(["Performance", "Rolling returns", "Risk & drawdown", "Peers & score"])
    with tabs[0]:
        st.plotly_chart(
            line_chart({row.scheme_name: nav}, "NAV history", "NAV (INR per unit)"), width="stretch"
        )
        benchmark = benchmark_for(ctx, row)
        aligned = align_series(nav, benchmark) if row.benchmark_type == "TRI" else pd.DataFrame()
        if len(aligned) >= 2:
            st.plotly_chart(
                line_chart(
                    {k: aligned[k] / aligned[k].iloc[0] * 100 for k in aligned},
                    "Growth of 100 · common observation dates",
                    "Normalised value",
                ),
                width="stretch",
            )
            st.caption(
                f"Common date range: {aligned.index[0]:%d %b %Y} to {aligned.index[-1]:%d %b %Y}. Only verified TRI benchmarks are shown."
            )
        else:
            st.info(
                "A matching TRI benchmark is unavailable. Import its series and scheme metadata."
            )
        st.plotly_chart(
            line_chart(
                {"Fund": nav / nav.iloc[0] - 1},
                "Cumulative return since first observation",
                "Cumulative return",
                True,
            ),
            width="stretch",
        )
        st.caption(
            f"Benchmark excess CAGR · 3Y: {fmt(row.benchmark_excess_return, True)} · Tracking difference: {fmt(row.tracking_difference, True)} · Tracking error: {fmt(row.tracking_error, True)}"
        )
        table(
            pd.DataFrame(
                [
                    {
                        "1M": row.return_1m,
                        "3M": row.return_3m,
                        "6M": row.return_6m,
                        "1Y": row.return_1y,
                        "3Y CAGR": row.cagr_3y,
                        "5Y CAGR": row.cagr_5y,
                    }
                ]
            ),
            ["1M", "3M", "6M", "1Y", "3Y CAGR", "5Y CAGR"],
        )
    with tabs[1]:
        years = st.selectbox(
            "Rolling window", [1, 3, 5], format_func=lambda n: f"{n} year{'s' if n > 1 else ''}"
        )
        roll = rolling_returns(nav, years)
        st.info(
            "Rolling returns ask: what return would the same holding period have earned on each eligible end date? Overlapping windows are correlated; they are not independent outcomes."
        )
        if roll.empty:
            st.info("This rolling window needs more historical data.")
        else:
            st.plotly_chart(
                line_chart(
                    {"Fund": roll},
                    f"Rolling {years}Y returns" + (" · annualised" if years > 1 else ""),
                    "Rolling return",
                    True,
                ),
                width="stretch",
            )
            st.plotly_chart(rolling_distribution(roll), width="stretch")
            table(pd.DataFrame([rolling_summary(roll)]), ["median", "best", "worst", "p25", "p75"])
            common_levels = align_series(nav, benchmark_for(ctx, row))
            pair = pd.concat(
                [
                    rolling_returns(common_levels.Fund, years).rename("Fund"),
                    rolling_returns(common_levels.Benchmark, years).rename("Benchmark"),
                ],
                axis=1,
            ).dropna()
            if not pair.empty and row.benchmark_type == "TRI":
                st.plotly_chart(
                    line_chart(
                        {"Fund minus benchmark": pair.Fund - pair.Benchmark},
                        "Rolling excess return · common end dates",
                        "Return difference",
                        True,
                    ),
                    width="stretch",
                )
                st.caption(
                    f"Fund outperformed in {(pair.Fund > pair.Benchmark).mean():.1%} of {len(pair):,} eligible overlapping windows."
                )
    with tabs[2]:
        three = period_series(nav, 36, ctx["as_of"])
        risk_nav = three if len(three) else nav
        st.caption(
            "Risk cards use the trailing three-year horizon. Charts show the available history when three years are unavailable."
        )
        st.plotly_chart(
            line_chart(
                {"Drawdown": drawdown_series(risk_nav)},
                "Decline from running NAV peak",
                "Drawdown",
                True,
            ),
            width="stretch",
        )
        vol = daily_returns(risk_nav).rolling(63, min_periods=63).std() * 252**0.5
        st.plotly_chart(
            line_chart(
                {"63 observed daily returns": vol.dropna()},
                "Volatility history · annualised",
                "Annualised volatility",
                True,
            ),
            width="stretch",
        )
        cols = st.columns(4)
        for col, key, label, pct in zip(
            cols,
            ["maximum_drawdown", "downside_deviation", "sharpe_ratio", "sortino_ratio"],
            ["Maximum drawdown", "Downside deviation", "Sharpe ratio", "Sortino ratio"],
            [True, True, False, False],
            strict=True,
        ):
            col.metric(label, fmt(row[key], pct))
        st.caption(
            f"Annual risk-free rate and downside target: {ctx['risk_free_rate']:.2%}. Ratios use arithmetic daily excess returns and 252-day annualisation."
        )
    with tabs[3]:
        st.plotly_chart(contributions(row), width="stretch")
        st.caption(
            f"3Y return percentile: {fmt(row.category_percentile, decimals=1)} · Category rank: {fmt(row.category_rank, decimals=0)} / {int(row.peer_count)} · Peer median 3Y CAGR: {fmt(row.category_median_return, True)}"
        )
        peers = ctx["analysis"]
        for key in ["category", "subcategory", "fund_type", "benchmark_code"]:
            peers = peers.loc[peers[key] == row[key]]
        table(
            peers[
                [
                    "scheme_name",
                    "cagr_3y",
                    "annualised_volatility",
                    "consistency_raw",
                    "category_percentile",
                    "research_score",
                ]
            ],
            ["cagr_3y", "annualised_volatility"],
        )
        if not peers.empty and peers.annualised_volatility.notna().any():
            distribution = px.box(
                peers, y="annualised_volatility", points="all", hover_name="scheme_name"
            )
            st.plotly_chart(
                style(
                    distribution,
                    "Comparable peers · volatility distribution",
                    "Annualised volatility",
                    True,
                ),
                width="stretch",
            )
        st.caption(
            "Consistency is median 1Y rolling return divided by its interquartile range plus 0.01. Risk uses Sortino, not an assumption that all lower-volatility funds are better."
        )
    st.download_button(
        "Download analytical report",
        analytical_report(row.to_dict(), ctx["as_of"], ctx["risk_free_rate"], ctx["demo"]),
        f"fundlens-{row.scheme_code}-report.md",
        "text/markdown",
    )
