import pandas as pd
import streamlit as st

from analytics.benchmark_analysis import benchmark_metrics
from analytics.returns import cagr, trailing_return
from analytics.risk_metrics import drawdown_series, risk_metrics
from analytics.rolling_returns import rolling_returns
from pages.common import benchmark_for, empty_guard, nav_for, table
from services.report_service import csv_bytes
from visualizations.charts import line_chart


def render(ctx):
    st.title("Fund Comparison")
    st.caption("Compare up to four funds over common observation dates.")
    if empty_guard(ctx):
        return
    frame = ctx["analysis"]
    codes = st.multiselect(
        "Funds to compare",
        frame.scheme_id.tolist(),
        default=frame.scheme_id.iloc[:2].tolist(),
        max_selections=4,
        format_func=lambda code: frame.loc[frame.scheme_id == code, "scheme_name"].iloc[0],
    )
    if not codes:
        st.info("Select at least one fund.")
        return
    selected = frame.loc[frame.scheme_id.isin(codes)]
    if selected.category.nunique() > 1 or selected.fund_type.nunique() > 1:
        st.warning(
            "The selection includes different categories or fund types. Their research scores and percentiles refer to different peer groups and are not a common ranking."
        )
    series = {row.scheme_name: nav_for(ctx, row) for _, row in selected.iterrows()}
    common = pd.concat(series, axis=1).dropna()
    if len(common) < 2:
        st.info("There are not enough overlapping observations for this comparison.")
        return
    st.caption(
        f"Common dates: {common.index[0]:%d %b %Y} – {common.index[-1]:%d %b %Y} · {len(common):,} observations · No interpolation"
    )
    st.plotly_chart(
        line_chart(
            {k: common[k] / common[k].iloc[0] * 100 for k in common},
            "Growth of 100 · common dates",
            "Normalised NAV",
        ),
        width="stretch",
    )
    st.plotly_chart(
        line_chart(
            {k: drawdown_series(common[k]) for k in common},
            "Drawdown comparison · common dates",
            "Drawdown",
            True,
        ),
        width="stretch",
    )
    st.plotly_chart(
        line_chart(
            {k: rolling_returns(common[k]) for k in common},
            "Rolling 1Y returns · common dates",
            "Rolling return",
            True,
        ),
        width="stretch",
    )
    rows = []
    for _, row in selected.iterrows():
        s = common[row.scheme_name]
        b = benchmark_for(ctx, row).loc[common.index[0] : common.index[-1]]
        bm = benchmark_metrics(s, b) if row.benchmark_type == "TRI" else {}
        rows.append(
            {
                "scheme_name": row.scheme_name,
                "category": row.category,
                "common_range_return": s.iloc[-1] / s.iloc[0] - 1,
                "common_range_cagr": cagr(s) if (s.index[-1] - s.index[0]).days >= 365 else None,
                "return_1y": trailing_return(s, 12),
                "cagr_3y": trailing_return(s, 36),
                **risk_metrics(s, ctx["risk_free_rate"]),
                "benchmark_excess_return": bm.get("benchmark_excess_return"),
                "research_score_3y": row.research_score,
                "category_percentile_3y": row.category_percentile,
            }
        )
    result = pd.DataFrame(rows)
    table(
        result,
        [
            "common_range_return",
            "common_range_cagr",
            "return_1y",
            "cagr_3y",
            "annualised_volatility",
            "maximum_drawdown",
            "downside_deviation",
            "benchmark_excess_return",
        ],
    )
    st.caption(
        "Risk and return metrics above are recalculated over the common date range. Scores and category percentiles retain their documented 3Y cohort at the selected analysis date."
    )
    st.download_button(
        "Download comparison", csv_bytes(result), "fundlens-comparison.csv", "text/csv"
    )
