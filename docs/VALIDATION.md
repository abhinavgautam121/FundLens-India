# Executed validation

The following results come from the actual implementation and running application.

| Check | Result |
|---|---|
| Python 3.12.14, `pytest -q` | **41 passed in 73.94 seconds** |
| Python 3.11 in the built Docker image, `pytest -q` | **41 passed in 36.92 seconds** |
| `ruff check .` | All checks passed |
| Docker image build from the supplied Dockerfile | Successful |
| Non-root Docker application on port 8501 | HTTP health endpoint returned `ok`; Docker health status `healthy` |
| Deterministic demo export | 24 fictional funds, 3 synthetic benchmarks, 41,962 NAV observations; nine CSV tables plus ZIP manifest |
| Native Streamlit execution tests | All seven routes, empty uploaded dataset, invalid weights and date before first NAV |
| Chromium browser rendering | Overview, Deep Dive, Explainability Lab and Data Quality Centre rendered; no JavaScript page errors |
| Browser rolling-return tab | Chart and rolling distribution rendered |
| Browser AMFI upload | Synthetic semicolon-delimited AMFI-format fixture accepted through the real file-upload form |
| Browser export download | Power BI ZIP downloaded through the real application button |
| Mobile viewport | Overview rendered at 390 × 844; document width remained 390 pixels |

## Calculation and integration coverage

The tests cover calendar CAGR/daily/trailing/rolling returns, invalid prices and missing
history; independent volatility, drawdown, Sharpe/Sortino examples; exact benchmark alignment,
tracking error/difference and short benchmark coverage; tied/reversed peer percentiles;
component arithmetic, invalid weights and missing-score inputs; duplicate/conflicting NAVs;
incorrect uploads and missing values; benchmark/metadata/NAV ingestion; unavailable optional
metadata; price-index exclusion; future observations and future-dated metadata exclusion;
idempotent snapshots; stored parameter provenance; date-limited Power BI exports; spreadsheet
formula escaping; the schema creation script; and execution of all five SQL business queries.

The fixed demo includes a short-history fund and an incomplete-coverage fund whose scores
are correctly withheld. The other 22 funds have eligible experimental scores at 30 Oct 2026
with the default category weights and 6% annual risk-free assumption.

## Actual screenshots

- `docs/screenshots/overview.png`
- `docs/screenshots/deep-dive.png`
- `docs/screenshots/explainability.png`
- `docs/screenshots/data-quality.png`
- `docs/screenshots/mobile.png`

These were captured from the running Streamlit application in Chromium. The browser tests
use synthetic fixtures and fictional demo series; the images are not fabricated product mockups.

## Verification limits

This validates local SQLite execution, Python 3.11/3.12, the supplied Docker image and synthetic
test fixtures. It does not claim production deployment, a completed Power BI `.pbix`,
PostgreSQL runtime validation, live official-fund data reconciliation or a validated predictive
investment model. AMFI parser fixtures exercise the supported header layouts; users should
reconcile their actual official downloads and verified TRI provider data before relying on
real-data analytics. Further limitations are documented in `METHODOLOGY.md` and `README.md`.
