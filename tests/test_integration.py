import io
import json
import sqlite3
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import select

from analytics.benchmark_analysis import benchmark_metrics
from analytics.returns import clean_series
from analytics.scoring import load_weights
from database.connection import ImportLog, Scheme, connect
from services.data_service import import_file, read_tables
from services.demo_data import seed_demo
from services.fund_service import analyse, persist_analysis
from services.report_service import csv_bytes, powerbi_zip


@pytest.fixture
def db(tmp_path):
    return connect(f"sqlite:///{tmp_path}/data.db")


def test_benchmark_metadata_and_nav_workflow(db):
    engine, factory = db
    benchmark = b"date,benchmark_code,benchmark_name,tri_value\n2025-01-03,INDEX,Example TRI,1000\n"
    metadata = b"scheme_code,scheme_name,amc_name,category,subcategory,fund_type,benchmark_code,inception_date,data_source,metadata_as_of,expense_ratio,aum\n123456,Example Fund,Example AMC,Equity,Large Cap,Active,INDEX,2020-01-01,Verified source,2025-01-03,,\n"
    nav = b"Scheme Code;Scheme Name;Net Asset Value;Date\n123456;Example Fund;100;03-Jan-2025\n"
    # Unknown benchmark mapping is explicitly rejected.
    result = import_file(factory, "Scheme metadata CSV", metadata, "meta.csv", "Test source")
    assert result["rejected"] == 1
    assert (
        import_file(
            factory, "Benchmark CSV", benchmark, "benchmark.csv", "Official provider", "TRI"
        )["inserted"]
        == 1
    )
    assert (
        import_file(factory, "Scheme metadata CSV", metadata, "meta.csv", "Metadata provider")[
            "inserted"
        ]
        == 1
    )
    assert import_file(factory, "AMFI NAV", nav, "nav.txt", "AMFI")["inserted"] == 1
    tables = read_tables(engine)
    assert len(tables["nav_history"]) == 1
    assert tables["nav_history"].source.iloc[0] == "AMFI"
    assert pd.isna(tables["schemes"].expense_ratio.iloc[0])
    assert pd.isna(tables["schemes"].aum.iloc[0])
    frame = analyse(tables, "2025-01-03", 0.06, load_weights())
    assert frame.research_score.isna().all() and frame.cagr_3y.isna().all()


def test_benchmark_identity_cannot_silently_change(db):
    _, factory = db
    payload = b"date,benchmark_code,benchmark_name,tri_value\n2025-01-03,I,Example,100\n"
    import_file(factory, "Benchmark CSV", payload, "b.csv", "Source", "Price")
    changed = import_file(factory, "Benchmark CSV", payload, "b.csv", "Source", "TRI")
    assert changed["rejected"] == 1
    assert "conflicts" in changed["issues"][0]["issue"]


def test_future_invalid_values_are_not_used_in_past():
    s = pd.Series([100.0, 101.0, -1.0], index=pd.bdate_range("2025-01-01", periods=3))
    assert len(clean_series(s, "2025-01-02")) == 2
    with pytest.raises(ValueError):
        clean_series(s)


def test_benchmark_alignment_coverage_denominator_is_fund():
    dates = pd.bdate_range("2020-01-01", periods=1000)
    s = pd.Series(np.arange(1000) + 100, index=dates)
    bm = benchmark_metrics(s, s.iloc[500:])
    assert bm["alignment_coverage"] == 0.5


def test_nontri_and_future_metadata_withhold_relative_metrics(db):
    engine, factory = db
    seed_demo(factory)
    tables = read_tables(engine)
    tables["benchmarks"]["benchmark_type"] = "Price"
    frame = analyse(tables, "2026-10-30", 0.06, load_weights())
    assert frame.research_score.isna().all()
    assert frame.benchmark_excess_return.isna().all()
    tables["benchmarks"]["benchmark_type"] = "TRI"
    tables["schemes"]["metadata_as_of"] = pd.Timestamp("2026-10-30")
    frame = analyse(tables, "2025-10-30", 0.06, load_weights())
    assert frame.benchmark_excess_return.isna().all()
    assert frame.amc_name.isna().all()


def test_export_and_sql_queries_on_calculated_database(db):
    engine, factory = db
    seed_demo(factory)
    tables = read_tables(engine)
    config = load_weights()
    for date in ["2025-10-30", "2026-10-30"]:
        frame = analyse(tables, date, 0.06, config)
        persist_analysis(factory, frame, date, config, 0.06)
    tables = read_tables(engine)
    payload = powerbi_zip(tables, "2025-10-30", True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert len(archive.namelist()) == 10
        assert json.loads(archive.read("manifest.json"))["demo_data"] is True
        levels = pd.read_csv(archive.open("fact_daily_nav.csv"))
        assert pd.to_datetime(levels.nav_date).max() <= pd.Timestamp("2025-10-30")
        metrics = pd.read_csv(archive.open("fact_fund_metrics.csv"))
        assert json.loads(metrics.parameters_json.iloc[0])["risk_free_rate"] == 0.06
    sql = "\n".join(
        line
        for line in Path("sql/business_queries.sql").read_text().splitlines()
        if not line.lstrip().startswith("--")
    )
    statements = sql.split(";")
    parameters = tables["calculated_metrics"].parameters.iloc[0]
    with engine.connect() as connection:
        from sqlalchemy import text

        for statement in statements:
            if statement.strip():
                connection.execute(
                    text(statement),
                    {
                        "analysis_date": "2026-10-30",
                        "parameters": parameters,
                        "earlier_date": "2025-10-30",
                        "later_date": "2026-10-30",
                        "methodology_version": parameters,
                    },
                ).fetchall()


def test_schema_script_and_orm_have_same_tables():
    with sqlite3.connect(":memory:") as db:
        db.executescript(Path("database/schema.sql").read_text())
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert names == {
        "schemes",
        "nav_history",
        "benchmarks",
        "benchmark_history",
        "calculated_metrics",
        "rating_snapshots",
        "data_import_logs",
    }


def test_csv_spreadsheet_formulas_are_escaped():
    df = pd.DataFrame(
        {"scheme_name": ["=1+2", " @command", "Normal fund"], "return": [-0.1, 0.1, 0.2]}
    )
    exported = pd.read_csv(io.BytesIO(csv_bytes(df)))
    assert exported.scheme_name.iloc[0].startswith("'")
    assert exported.scheme_name.iloc[1].startswith("'")
    assert exported["return"].iloc[0] == -0.1


def test_duplicate_metadata_and_malformed_benchmark_are_audited(db):
    _, factory = db
    result = import_file(factory, "Benchmark CSV", b"wrong,header\na,b\n", "bad.csv", "Source")
    assert result["status"] == "rejected"
    with factory() as session:
        assert session.scalar(select(ImportLog)).records_rejected == 1
        assert session.scalar(select(Scheme)) is None
