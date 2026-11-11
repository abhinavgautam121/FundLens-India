# User guide

## First launch

Start with `streamlit run app.py` from the repository root. The sidebar defaults to **Demo data**,
which generates 24 fictional funds in Equity, Hybrid and Debt, three synthetic TRI benchmarks,
and deliberate missing/short-history examples. All screens visibly label this as DEMO DATA.

Choose an analysis date in the sidebar. The default is the latest NAV date (the demo has a fixed
end date of 30 Oct 2026). In **Research settings**, choose the annual risk-free assumption.
For a session weight override, enable the checkbox and enter four percentages summing to 100.
Incomplete or invalid inputs are visible and prevent an invalid composite calculation.

## Explore research

1. **Executive Overview**: category filters, availability counts, category medians and profiles.
2. **Fund Explorer**: search/filter by AMC, category, subcategory, type, benchmark or availability;
   choose a historical period, sort table headings and export CSV.
3. **Fund Deep Dive**: select a fund, inspect performance/rolling/risk/peer tabs and download a
   Markdown analytical report. Growth charts start at 100 on exact common observation dates.
4. **Fund Comparison**: select at most four funds. Returns and risk are recalculated on the
   common date range. Scores retain their 3Y peer definition; cross-category/type selections
   display a warning.
5. **Explainability Lab**: inspect percentile-to-point contributions, select two historical
   dates, and review measured changes and a score-change waterfall. Missing historical inputs
   remain unavailable. Snapshots are saved automatically with their parameter version.
6. **Data Quality Centre**: import data, review errors and audit logs, plan historical downloads,
   and export validation reports, analytics or a Power BI ZIP.
7. **Methodology & Assumptions**: read formulas, current weights, sources and limitations.

## Import real data

Choose **Uploaded data**. It is a separate, initially empty database.

1. Download an official AMFI NAV text file from
   https://www.amfiindia.com/net-asset-value/nav-download. Preserve its semicolon header.
   The request planner divides a chosen historical range into inclusive ≤90-day windows;
   download them manually and upload each. One recent NAV file is not historical coverage.
2. Prepare benchmark CSV with `date,benchmark_code,benchmark_name,tri_value`. Dates must be ISO
   `YYYY-MM-DD`. In the import form, choose Benchmark CSV, enter a traceable source, and mark
   TRI only after verifying its total-return status. A price/unverified index is stored but
   excluded from scores and relative comparisons. A code's name/type cannot silently change.
3. Import Scheme metadata CSV. The download template includes required classification,
   benchmark mapping, inception date, data_source and metadata_as_of, plus optional expense
   ratio and AUM. The benchmark code must already exist. Do not invent missing metadata.
4. Import the AMFI NAV files with their official source URL. NAV-only import is also supported;
   until matching metadata and benchmark history are supplied, a score may remain withheld.
5. Read the status message and audit details. Conflicting duplicate observations keep the
   original stored value. Rejected rows are listed; valid rows in a partial import are retained.

CSV and AMFI text uploads are limited to 20 MB. Large history can be divided into smaller
files. Imports are transactions and retain source/upload timestamps. Missing values, stale
data, short history, unobserved weekdays and benchmark failures appear in the quality centre.

## Export and refresh

Exports use the selected analysis date. Metrics are saved at dates you actually analyse;
historical snapshots are computed on demand in the lab. Power BI ZIP includes a manifest and
full configuration JSON with facts. Imported data is refreshed manually by importing additional
files. Local database files and raw uploads are excluded from Git.

See `docs/DEPLOYMENT.md` for deployment and data persistence details. The educational prototype
does not issue investment recommendations.
