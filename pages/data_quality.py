import json
from datetime import date

import pandas as pd
import streamlit as st

from ingestion.validation import date_windows
from services.data_service import import_file
from services.fund_service import quality_report
from services.report_service import csv_bytes, powerbi_zip


def render(ctx):
    st.title("Data Quality Centre")
    st.caption(
        "Import traceable data, inspect validation results and export an auditable research dataset."
    )
    logs = ctx["tables"]["data_import_logs"]
    quality = quality_report(ctx["tables"], ctx["analysis"], ctx["as_of"])
    cols = st.columns(4)
    values = [
        int(logs.records_processed.sum()),
        int(logs.duplicates.sum()),
        int(logs.records_rejected.sum()),
        len(quality),
    ]
    for col, label, value in zip(
        cols,
        ["Records processed", "Duplicates detected", "Rejected records", "Fund quality alerts"],
        values,
        strict=True,
    ):
        col.metric(label, f"{value:,}")
    imports, monitor, exports = st.tabs(["Import data", "Validation & audit", "Exports & Power BI"])
    with imports:
        if ctx["demo"]:
            st.info(
                "Demo data is kept separate. Choose ‘Uploaded data’ in the sidebar to import your files."
            )
        st.markdown(
            "Import benchmark CSV first, scheme metadata second, then AMFI NAV files. NAV-only imports work, with scores withheld until metadata and benchmark history are available."
        )
        with st.form("import_form", clear_on_submit=False):
            kind = st.selectbox("Import type", ["AMFI NAV", "Benchmark CSV", "Scheme metadata CSV"])
            source = st.text_input(
                "Traceable source", placeholder="Official source URL or dataset reference"
            )
            benchmark_type = st.selectbox(
                "Benchmark type (for benchmark CSV)",
                ["Unverified", "TRI", "Price"],
                help="Select TRI only if you have verified that the data is a Total Return Index. Price and unverified indices are excluded from fund comparisons and scores.",
            )
            upload = st.file_uploader(
                "Choose a text or CSV file", type=["txt", "csv"], max_upload_size=20
            )
            submitted = st.form_submit_button("Validate and import", disabled=ctx["demo"])
        if submitted:
            if upload is None or not source.strip():
                st.error("Choose a file and enter its traceable data source.")
            else:
                try:
                    result = import_file(
                        ctx["factory"], kind, upload.getvalue(), upload.name, source, benchmark_type
                    )
                    st.session_state["last_import"] = result
                    st.cache_data.clear()
                    st.rerun()
                except (ValueError, UnicodeError) as exc:
                    st.error(str(exc))
        if "last_import" in st.session_state and not ctx["demo"]:
            result = st.session_state.last_import
            message = f"{result['status'].title()}: {result['inserted']:,} imported, {result['duplicates']:,} duplicates, {result['rejected']:,} rejected."
            (st.success if result["status"] == "success" else st.warning)(message)
            if result["issues"]:
                st.dataframe(pd.DataFrame(result["issues"]), hide_index=True, width="stretch")
        with st.expander("Download file templates"):
            st.download_button(
                "Benchmark CSV template",
                "date,benchmark_code,benchmark_name,tri_value\n",
                "benchmark-template.csv",
                "text/csv",
            )
            st.download_button(
                "Scheme metadata CSV template",
                "scheme_code,scheme_name,amc_name,category,subcategory,fund_type,benchmark_code,inception_date,expense_ratio,aum,data_source,metadata_as_of\n",
                "scheme-template.csv",
                "text/csv",
            )
            st.caption(
                "CSV dates: YYYY-MM-DD. Expense ratio: annual percentage points. AUM: INR crore. Optional expense ratio and AUM may be blank."
            )
        with st.expander("Plan AMFI historical downloads · up to 90 days per request"):
            st.link_button(
                "Open official AMFI NAV downloads",
                "https://www.amfiindia.com/net-asset-value/nav-download",
            )
            a, b = st.columns(2)
            start = a.date_input("Download start", value=date(2025, 1, 1))
            end = b.date_input("Download end", value=date.today())
            if start <= end:
                windows = pd.DataFrame(date_windows(start, end), columns=["start_date", "end_date"])
                st.dataframe(windows, hide_index=True, width="stretch")
                st.download_button(
                    "Download request plan", csv_bytes(windows), "amfi-request-plan.csv", "text/csv"
                )
            else:
                st.error("End date must be on or after start date.")
    with monitor:
        if quality.empty:
            st.info("No fund-level alerts to display. Import data if the dataset is empty.")
        else:
            st.dataframe(quality, hide_index=True, width="stretch")
        st.download_button(
            "Download fund validation report",
            csv_bytes(quality),
            "fundlens-validation.csv",
            "text/csv",
        )
        st.subheader("Import audit trail")
        st.dataframe(logs.drop(columns=["error_summary"]), hide_index=True, width="stretch")
        details = []
        for _, log in logs.iterrows():
            for item in json.loads(log.error_summary or "[]"):
                details.append({"import_id": log.import_id, "filename": log.filename, **item})
        if details:
            st.dataframe(pd.DataFrame(details), hide_index=True, width="stretch")
        st.download_button(
            "Download import audit", csv_bytes(logs), "fundlens-import-audit.csv", "text/csv"
        )
        st.caption(
            "Duplicate counts include both identical and conflicting duplicates. Rejected counts include conflicts, so these categories can overlap. Unobserved weekdays may include Indian exchange holidays."
        )
    with exports:
        st.write(
            "Power BI export includes dimensions, daily NAV, benchmark levels, calculated metrics and parameter-versioned research snapshots. The manifest preserves the dataset label and analysis date."
        )
        if not ctx["analysis"].empty:
            from services.data_service import read_tables

            fresh = read_tables(ctx["engine"])
            st.download_button(
                "Download Power BI dataset (ZIP)",
                powerbi_zip(fresh, ctx["as_of"], ctx["demo"]),
                "fundlens-powerbi.zip",
                "application/zip",
            )
            st.download_button(
                "Download calculated analytics CSV",
                csv_bytes(ctx["analysis"]),
                "fundlens-analytics.csv",
                "text/csv",
            )
        else:
            st.info("Import data to generate analytical exports.")
