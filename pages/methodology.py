from pathlib import Path

import pandas as pd
import streamlit as st


def render(ctx):
    st.title("Methodology & Assumptions")
    st.caption("Every formula, data policy and scoring assumption is open to inspection.")
    st.info(
        f"Methodology v1.0.0 · Annual risk-free rate: {ctx['risk_free_rate']:.2%} · Analysis date: {ctx['as_of']:%d %b %Y} · 252 trading days · 365.25 calendar days"
    )
    st.subheader("Current scoring configuration")
    config = [{"category": "Default", **ctx["weights"]["default"]}]
    config += [{"category": k, **v} for k, v in ctx["weights"].get("categories", {}).items()]
    st.dataframe(pd.DataFrame(config), hide_index=True, width="stretch")
    st.caption(
        "Weights are illustrative. Use Research settings in the sidebar to apply a session override, or edit config/scoring_weights.yaml for category-specific persistent defaults."
    )
    st.markdown(Path("docs/METHODOLOGY.md").read_text())
    st.subheader("Data refresh and provenance")
    logs = ctx["tables"]["data_import_logs"]
    st.dataframe(
        logs[["filename", "data_source", "uploaded_at", "import_status"]],
        hide_index=True,
        width="stretch",
    )
