"""FundLens India — launch with `streamlit run app.py`."""

import logging
import os
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml
from dotenv import load_dotenv

from analytics.scoring import COMPONENTS, load_weights, validate_weights
from database.connection import connect
from pages import (
    data_quality,
    explainability,
    fund_comparison,
    fund_detail,
    fund_explorer,
    methodology,
    overview,
)
from services.data_service import read_tables
from services.demo_data import seed_demo
from services.fund_service import analyse, persist_analysis
from services.report_service import DISCLAIMER

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
st.set_page_config(page_title="FundLens India | Explainable research", page_icon="◈", layout="wide")
st.markdown(
    """<style>
    .stApp {font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;}
    [data-testid="stSidebar"] {background:#14243b;}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {color:#ecf2fa;}
    [data-testid="stSidebar"] .stRadio label {padding:7px 0;}
    .block-container {padding-top:2.3rem; padding-bottom:2rem; max-width:1480px;}
    h1 {font-size:2rem !important; font-weight:650 !important; letter-spacing:-.04em;}
    h2 {font-size:1.35rem !important; letter-spacing:-.02em;}
    [data-testid="stMetric"] {background:white; border:1px solid #e2e8f0; border-radius:12px; padding:20px;}
    [data-testid="stMetricLabel"] {color:#64748b; font-size:.8rem;}
    [data-testid="stMetricValue"] {font-size:1.8rem; color:#14243b;}
    [data-testid="stPlotlyChart"] {background:white; border:1px solid #e6ebf1; border-radius:12px; padding:8px;}
    .brand {font-size:1.8rem; font-weight:700; letter-spacing:-.05em; color:white;}
    .brand span {color:#79c9bf;}
    .brand-sub {color:#aabbd1; font-size:.73rem; letter-spacing:.13em; margin-bottom:25px;}
    .dataset-tag {display:inline-block; border:1px solid #d7e5df; padding:5px 11px; border-radius:6px;
                  color:#176f63; font-size:.75rem; font-weight:600; margin-bottom:12px; background:#edf7f2;}
    .footer {font-size:.73rem; color:#65748a; border-top:1px solid #dce3ec; margin-top:2rem; padding-top:1rem; line-height:1.6;}
    @media (max-width:700px) {.block-container {padding:1rem;} h1 {font-size:1.65rem !important;}}
</style>""",
    unsafe_allow_html=True,
)


@st.cache_resource
def database(url):
    return connect(url)


@st.cache_data(show_spinner=False)
def calculate(tables, as_of, rate, weights, minimum_peers, minimum_coverage):
    return analyse(tables, as_of, rate, weights, minimum_peers, minimum_coverage)


def main():
    settings = yaml.safe_load(Path("config/settings.yaml").read_text())
    weights = load_weights()
    with st.sidebar:
        st.markdown(
            '<div class="brand">FundLens<span> India</span></div><div class="brand-sub">EXPLAINABLE FUND RESEARCH</div>',
            unsafe_allow_html=True,
        )
        dataset = st.selectbox("Research dataset", ["Demo data", "Uploaded data"])
        demo = dataset == "Demo data"
        routes = {
            "Executive Overview": overview,
            "Fund Explorer": fund_explorer,
            "Fund Deep Dive": fund_detail,
            "Fund Comparison": fund_comparison,
            "Explainability Lab": explainability,
            "Data Quality Centre": data_quality,
            "Methodology & Assumptions": methodology,
        }
        page = st.radio("Workspace", list(routes), label_visibility="collapsed")
    url = (
        os.getenv("DEMO_DATABASE_URL", "sqlite:///data/fundlens-demo.db")
        if demo
        else os.getenv("DATABASE_URL", "sqlite:///data/fundlens.db")
    )
    other_url = (
        os.getenv("DATABASE_URL", "sqlite:///data/fundlens.db")
        if demo
        else os.getenv("DEMO_DATABASE_URL", "sqlite:///data/fundlens-demo.db")
    )
    if url == other_url:
        st.error(
            "Demo and uploaded databases must have different URLs to keep synthetic and imported data separate."
        )
        return
    engine, factory = database(url)
    if demo:
        seed_demo(factory)
    tables = read_tables(engine)
    latest = pd.to_datetime(tables["nav_history"].nav_date).max()
    default_date = latest.date() if pd.notna(latest) else pd.Timestamp.today().date()
    with st.sidebar:
        st.divider()
        # Distinct keys ensure changing datasets resets the selected analysis date.
        as_of = st.date_input(
            "Analysis date",
            value=default_date,
            max_value=pd.Timestamp.today().date(),
            key=f"asof_{demo}",
        )
        with st.expander("Research settings"):
            rate = (
                st.number_input(
                    "Annual risk-free rate (%)",
                    min_value=0.0,
                    max_value=30.0,
                    value=float(os.getenv("RISK_FREE_RATE", ".06")) * 100,
                    step=0.25,
                )
                / 100
            )
            override = st.checkbox("Override weights for this session")
            if override:
                chosen = {
                    k: st.number_input(
                        f"{k.title()} (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(weights["default"][k]) * 100,
                        step=1.0,
                    )
                    / 100
                    for k in COMPONENTS
                }
                try:
                    validate_weights(chosen)
                    weights = {"default": chosen, "categories": {}}
                except ValueError as exc:
                    st.error(str(exc))
                    st.stop()
        st.caption(
            "Independent educational prototype. Experimental indicators; no investment recommendations."
        )
    label = (
        "DEMO DATA · FICTIONAL SCHEMES & SYNTHETIC RETURNS"
        if demo
        else "USER-IMPORTED DATA · VERIFY SOURCES & COVERAGE"
    )
    st.markdown(f'<div class="dataset-tag">{label}</div>', unsafe_allow_html=True)
    if demo:
        st.caption(
            "Every fund and index in this dataset is fictional. No synthetic return represents actual mutual fund performance."
        )
    with st.spinner("Calculating point-in-time analytics…"):
        analysis = calculate(
            tables, as_of, rate, weights, settings["minimum_peers"], settings["minimum_coverage"]
        )
    if not analysis.empty:
        persist_analysis(factory, analysis, as_of, weights, rate)
    ctx = dict(
        tables=tables,
        analysis=analysis,
        as_of=as_of,
        risk_free_rate=rate,
        weights=weights,
        settings=settings,
        demo=demo,
        engine=engine,
        factory=factory,
    )
    routes[page].render(ctx)
    st.markdown(f'<div class="footer">{DISCLAIMER}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
