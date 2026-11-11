import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import select

from analytics.explainability import explain_changes
from analytics.scoring import COMPONENTS
from database.connection import Snapshot
from pages.common import empty_guard, fmt, fund_picker, score_notice, table
from services.fund_service import analyse, parameters_key, persist_analysis
from visualizations.charts import contributions, line_chart, style


@st.cache_data(show_spinner=False)
def historical_analysis(tables, date, rate, weights, minimum_peers, coverage):
    return analyse(tables, date, rate, weights, minimum_peers, coverage)


def render(ctx):
    st.title("Explainability Lab")
    st.caption("See each contribution. Trace profile changes to calculated facts.")
    if empty_guard(ctx):
        return
    row = fund_picker(ctx, "explain_fund")
    score_notice(row)
    a, b = st.columns([1, 2])
    with a:
        st.metric("Experimental research score", fmt(row.research_score, decimals=1))
        st.caption("Out of 100, within a comparable peer cohort")
        st.metric("3Y return percentile", fmt(row.category_percentile, decimals=1))
        st.caption(
            f"{int(row.score_peer_count)} complete scoring peers · {row.fund_type} · {row.subcategory}"
        )
    with b:
        st.plotly_chart(contributions(row), width="stretch")
    weights = ctx["weights"].get("categories", {}).get(row.category, ctx["weights"]["default"])
    components = pd.DataFrame(
        [
            {
                "dimension": c.title(),
                "weight": weights[c],
                "peer_percentile": row[f"{c}_component"],
                "contribution_points": row[f"{c}_contribution"],
                "relative_to_midpoint": row[f"{c}_contribution"] - weights[c] * 50,
            }
            for c in COMPONENTS
        ]
    )
    table(components, ["weight"])
    st.caption(
        "Positive/negative values in relative_to_midpoint show the contribution above/below a 50th-percentile peer baseline. All absolute contributions are non-negative."
    )
    with st.expander("How is this calculated?"):
        st.write(
            "Average-rank percentiles normalise four inputs within category + subcategory + fund type + benchmark. Consistency uses rolling-return stability; risk uses Sortino; active benchmark performance uses rolling win rate; passive benchmark performance uses negative tracking error; recency uses 1Y return. Each percentile is multiplied by its displayed weight. A complete cohort of at least three funds is required."
        )
    st.subheader("Why did this score change?")
    col1, col2 = st.columns(2)
    limit = pd.Timestamp(ctx["as_of"])
    before = col1.date_input(
        "Earlier snapshot",
        value=(limit - pd.DateOffset(years=1)).date(),
        min_value=pd.Timestamp("1990-01-01").date(),
        max_value=limit.date(),
    )
    after = col2.date_input(
        "Later snapshot", value=limit.date(), min_value=before, max_value=limit.date()
    )
    with st.spinner("Recalculating eligible peers at both historical dates…"):
        results = []
        for date in [before, after]:
            historical = historical_analysis(
                ctx["tables"],
                date,
                ctx["risk_free_rate"],
                ctx["weights"],
                ctx["settings"]["minimum_peers"],
                ctx["settings"]["minimum_coverage"],
            )
            persist_analysis(
                ctx["factory"], historical, date, ctx["weights"], ctx["risk_free_rate"]
            )
            results.append(historical.loc[historical.scheme_id == row.scheme_id].iloc[0])
    for explanation in explain_changes(results[0].to_dict(), results[1].to_dict()):
        st.write(explanation)
    if all(pd.notna(r.research_score) for r in results):
        differences = [
            results[1][f"{c}_contribution"] - results[0][f"{c}_contribution"] for c in COMPONENTS
        ]
        fig = go.Figure(
            go.Waterfall(
                x=["Earlier score", *[c.title() for c in COMPONENTS], "Later score"],
                measure=["absolute", "relative", "relative", "relative", "relative", "total"],
                y=[results[0].research_score, *differences, 0],
                increasing=dict(marker_color="#16796f"),
                decreasing=dict(marker_color="#b76464"),
            )
        )
        st.plotly_chart(
            style(
                fig, "Score change explained by component contributions", "Research score points"
            ),
            width="stretch",
        )
    version = parameters_key(ctx["weights"], ctx["risk_free_rate"])
    with ctx["factory"]() as session:
        snapshots = session.scalars(
            select(Snapshot)
            .where(
                Snapshot.scheme_id == int(row.scheme_id),
                Snapshot.methodology_version == version,
                Snapshot.snapshot_date <= limit.date(),
            )
            .order_by(Snapshot.snapshot_date)
        ).all()
    history = pd.Series(
        [s.research_score for s in snapshots],
        index=pd.to_datetime([s.snapshot_date for s in snapshots]),
        dtype=float,
    )
    st.plotly_chart(
        line_chart(
            {"Research score": history.dropna()},
            "Saved research score snapshots · same parameters",
            "Score out of 100",
        ),
        width="stretch",
    )
    st.caption(
        "Changes are descriptive, not explanations of market causes. Peer membership can change. Both dates use the same weights and risk-free assumption; future observations and future-dated metadata are excluded."
    )
