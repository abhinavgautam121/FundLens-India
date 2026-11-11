# Data dictionary

| Table | Key and grain | Main fields / units |
|---|---|---|
| schemes | scheme_id; unique text scheme_code | Current name, AMC, category, subcategory, Active/Passive, benchmark FK, inception date, optional annual expense ratio (% points), optional AUM (INR crore), metadata source/as-of |
| nav_history | Unique scheme_id + nav_date | Positive NAV in INR/unit, source, UTC imported_at |
| benchmarks | benchmark_code | Name, TRI/Price/Unverified type |
| benchmark_history | Unique benchmark_code + benchmark_date | Positive index level, source |
| calculated_metrics | Unique scheme/date/period/parameters | 3Y total return, CAGR, volatility, drawdown, Sharpe, Sortino, excess CAGR, tracking error/difference, weekday coverage, median 1Y rolling return, benchmark rolling win rate |
| rating_snapshots | Unique scheme/date/methodology_version | Research score 0–100, 3Y return peer percentile 0–100, four **weighted contribution points**, full parameters_json |
| data_import_logs | One file import attempt | Basename, source, UTC upload timestamp, processed/rejected/duplicate counts, status, row/error report JSON |

Returns, volatility, drawdown, data coverage and win rates are decimal fractions: 0.10 = 10%.
Drawdowns are negative. Sharpe/Sortino are unitless. Missing values remain SQL NULL / CSV blank.
Metrics `parameters` and snapshot `methodology_version` include the v1.0.0 methodology prefix
and a hash of the full configuration; `parameters_json` retains weights, risk-free assumption
and settings for audit. Snapshot components store points, while the live analytics CSV also
includes raw component percentiles and raw inputs.

Metadata source and as-of dates are required for imported classification. Optional expense
ratio and AUM are not inferred. Metadata is a current-record model; historical versions are
not retained. Schemes imported through NAV alone have missing metadata until supplied.

Audit duplicates include identical and conflicting existing/in-file observation keys. A
conflicting duplicate is also rejected, so duplicate and rejection counts can overlap.
Accepted metadata updates count as imported records. Invalid binary/empty/header uploads
are recorded as one failed validation event when row counts cannot be determined.

NAV/benchmark provenance is row-level; metadata provenance is scheme-level; upload errors are
file-level. The app does not persist raw uploaded bytes. `data/raw/` is an optional local folder
excluded from version control. Fictional data sources explicitly begin with DEMO DATA.
