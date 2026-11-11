import pandas as pd
import plotly.express as px
import streamlit as st

from pages.common import empty_guard, table
from services.fund_service import quality_report
from services.report_service import csv_bytes
from visualizations.charts import COLORS, style


def render(ctx):
    st.title("The research overview")
    st.caption(
        "A transparent view of performance, risk and the evidence behind every analytical profile."
    )
    if empty_guard(ctx):
        return
    data = ctx["analysis"]
    categories = sorted(data.category.dropna().unique())
    selected = st.multiselect("Categories", categories, default=categories)
    filtered = data.loc[data.category.isin(selected)] if selected else data.iloc[:0]
    cols = st.columns(4)
    for col, label, value in zip(
        cols,
        ["Funds in view", "Categories", "TRI benchmarks", "Scores available"],
        [
            len(filtered),
            filtered.category.nunique(),
            len(ctx["tables"]["benchmarks"]),
            int(filtered.research_score.notna().sum()),
        ],
        strict=True,
    ):
        col.metric(label, value)
    quality = quality_report(ctx["tables"], filtered, ctx["as_of"])
    latest = data.latest_date.max()
    latest_label = (
        latest.strftime("%d %b %Y") if latest is not None and not pd.isna(latest) else "Unavailable"
    )
    st.caption(
        f"Latest NAV: {latest_label} · {int(filtered.eligible.sum())} funds meet history and coverage requirements · {len(quality)} quality alerts in view"
    )
    if filtered.empty:
        st.info("Choose at least one available category.")
        return
    a, b = st.columns([1.45, 1])
    with a:
        median = filtered.groupby("category", as_index=False).cagr_3y.median()
        fig = px.bar(
            median,
            x="category",
            y="cagr_3y",
            color_discrete_sequence=COLORS,
            labels={"category": "Category", "cagr_3y": "Median CAGR"},
        )
        st.plotly_chart(
            style(fig, "Category performance · median 3Y CAGR", "Annualised return", True),
            width="stretch",
        )
        st.caption(
            "Category summaries are descriptive. Fund ranks and scores use category, subcategory, fund type and benchmark peers."
        )
    with b:
        counts = filtered.profile.value_counts().reset_index()
        fig = px.pie(
            counts, names="profile", values="count", hole=0.7, color_discrete_sequence=COLORS
        )
        fig.update_traces(textinfo="value", hovertemplate="%{label}: %{value}<extra></extra>")
        st.plotly_chart(style(fig, "Research profile distribution"), width="stretch")
    st.subheader("Performance at a glance")
    metric = st.selectbox(
        "Sort within the selected category",
        ["cagr_3y", "return_1y", "annualised_volatility", "maximum_drawdown"],
    )
    category = st.selectbox("Ranking category", sorted(filtered.category.dropna().unique()))
    ranked = filtered.loc[filtered.category == category].sort_values(metric, ascending=False)
    show = ranked[["scheme_name", metric, "data_coverage", "peer_count", "profile"]]
    table(show, [metric, "data_coverage"])
    st.download_button(
        "Download overview CSV", csv_bytes(show), "fundlens-overview.csv", "text/csv"
    )
