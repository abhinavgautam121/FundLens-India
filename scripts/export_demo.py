"""Generate standalone Power BI datasets and a sample report from real application code."""

import argparse
from pathlib import Path

from analytics.scoring import load_weights
from database.connection import connect
from services.data_service import read_tables
from services.demo_data import seed_demo
from services.fund_service import analyse, persist_analysis
from services.report_service import analytical_report, csv_bytes, powerbi_frames, powerbi_zip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default="sqlite:///data/fundlens-demo.db")
    parser.add_argument("--output", default="powerbi/exports")
    args = parser.parse_args()
    engine, factory = connect(args.database_url)
    seed_demo(factory)
    tables = read_tables(engine)
    weights = load_weights()
    for date in ["2025-10-30", "2026-10-30"]:
        frame = analyse(tables, date, 0.06, weights)
        persist_analysis(factory, frame, date, weights, 0.06)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    fresh = read_tables(engine)
    for name, data in powerbi_frames(fresh, "2026-10-30").items():
        (output / f"{name}.csv").write_bytes(csv_bytes(data))
    (output / "fundlens-demo-powerbi.zip").write_bytes(powerbi_zip(fresh, "2026-10-30", True))
    row = frame.loc[frame.research_score.notna()].iloc[0]
    Path("docs/SAMPLE_REPORT.md").write_text(
        analytical_report(row.to_dict(), "2026-10-30", 0.06, True)
    )
    print(
        f"Generated {len(fresh['nav_history']):,} fictional NAV observations and {len(frame)} fund profiles in {output}"
    )


if __name__ == "__main__":
    main()
