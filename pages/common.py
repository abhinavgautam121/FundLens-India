import pandas as pd
import streamlit as st

from services.fund_service import price_series


def fmt(value, percentage=False, decimals=2):
    if value is None or pd.isna(value):
        return "Unavailable"
    return f"{value:.{decimals}%}" if percentage else f"{value:,.{decimals}f}"


def fund_picker(ctx, key="fund_picker"):
    frame = ctx["analysis"]
    selected = st.selectbox(
        "Select a fund",
        frame.scheme_id.tolist(),
        format_func=lambda code: frame.loc[frame.scheme_id == code, "scheme_name"].iloc[0],
        key=key,
    )
    return frame.loc[frame.scheme_id == selected].iloc[0]


def nav_for(ctx, row):
    return price_series(
        ctx["tables"]["nav_history"], "scheme_id", row.scheme_id, "nav_date", "nav", ctx["as_of"]
    )


def benchmark_for(ctx, row):
    return price_series(
        ctx["tables"]["benchmark_history"],
        "benchmark_code",
        row.benchmark_code,
        "benchmark_date",
        "tri_value",
        ctx["as_of"],
    )


def empty_guard(ctx):
    if ctx["analysis"].empty:
        st.info(
            "No funds are available. Open Data Quality Centre to import benchmark, metadata and NAV files."
        )
        return True
    return False


def score_notice(row):
    if pd.isna(row.research_score):
        st.warning(f"Research score withheld. {row.score_reason}.")
    else:
        st.caption(
            f"{row.profile} · {int(row.score_peer_count)} complete scoring peers · Experimental research score"
        )


def table(frame, percentage_columns=()):
    config = {
        col: st.column_config.NumberColumn(col.replace("_", " ").title(), format="percent")
        for col in percentage_columns
        if col in frame
    }
    st.dataframe(frame, hide_index=True, width="stretch", column_config=config)
