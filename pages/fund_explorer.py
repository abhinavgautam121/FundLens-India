import streamlit as st

from pages.common import empty_guard, table
from services.report_service import csv_bytes


def render(ctx):
    st.title("Fund Explorer")
    st.caption("Find comparable funds. Inspect returns alongside risk, coverage and peer context.")
    if empty_guard(ctx):
        return
    data = ctx["analysis"].copy()
    query = st.text_input("Search funds", placeholder="Search by fund name or scheme code")
    if query:
        data = data.loc[
            data.scheme_name.str.contains(query, case=False, regex=False)
            | data.scheme_code.str.contains(query, case=False, regex=False)
        ]
    cols = st.columns(3)
    for i, (label, key) in enumerate(
        [
            ("AMC", "amc_name"),
            ("Category", "category"),
            ("Subcategory", "subcategory"),
            ("Fund type", "fund_type"),
            ("Benchmark", "benchmark_code"),
        ]
    ):
        options = sorted(ctx["analysis"][key].dropna().unique())
        chosen = cols[i % 3].multiselect(label, options)
        if chosen:
            data = data.loc[data[key].isin(chosen)]
    availability = cols[2].selectbox(
        "Data availability", ["All funds", "Score available", "Score withheld"]
    )
    if availability != "All funds":
        data = data.loc[
            data.research_score.notna()
            if availability == "Score available"
            else data.research_score.isna()
        ]
    period = st.selectbox(
        "Historical period to highlight",
        ["return_1m", "return_3m", "return_6m", "return_1y", "cagr_3y", "cagr_5y"],
        index=3,
    )
    columns = list(
        dict.fromkeys(
            [
                "scheme_name",
                "category",
                "fund_type",
                "latest_nav",
                period,
                "return_1y",
                "cagr_3y",
                "annualised_volatility",
                "maximum_drawdown",
                "data_coverage",
                "category_percentile",
                "peer_count",
                "research_score",
            ]
        )
    )
    st.caption(
        f"{len(data)} funds · Click a column heading to sort · Unavailable metrics remain blank"
    )
    table(
        data[columns],
        [
            period,
            "return_1y",
            "cagr_3y",
            "annualised_volatility",
            "maximum_drawdown",
            "data_coverage",
        ],
    )
    st.download_button(
        "Export filtered funds", csv_bytes(data[columns]), "fundlens-explorer.csv", "text/csv"
    )
