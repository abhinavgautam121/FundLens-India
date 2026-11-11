### Dates, observations and eligibility

All analytics exclude observations after the selected analysis date. Trailing periods use
calendar offsets, not fixed row counts. The starting observation is the last NAV on or before
the calendar anniversary, at most seven calendar days earlier. The ending observation must
be within seven calendar days of the analysis date. Missing history produces unavailable
metrics. No price interpolation or forward/backward filling is performed.

Risk, benchmark, peer and scoring inputs use a trailing **three-year horizon**. The detailed
NAV, cumulative and selectable rolling charts use all available history through the analysis
date. Comparisons explicitly recalculate risk/returns on common observation dates.

Weekday coverage = observed weekdays / expected Monday–Friday dates over the eligible
period. It is an approximation, not an exchange-calendar completeness measure. Indian exchange
holidays can lower coverage and are reported as unobserved weekdays rather than definitely
missing trading observations. Scores require coverage ≥90%, ≥500 three-year observations,
≥252 eligible one-year rolling windows, a current NAV, complete point-in-time metadata,
and ≥90% benchmark alignment. These are illustrative research eligibility rules.

### Return formulas

- Daily return: `NAV(t)/NAV(t-1) - 1`. Only pairs one business day apart qualify as daily
  observations. Multi-business-day gaps are excluded from daily risk and tracking estimates.
- Total return: `ending NAV/starting NAV - 1`.
- CAGR: `(ending NAV/starting NAV)^(365.25/actual calendar days) - 1`.
- Trailing 1M, 3M, 6M and 1Y figures are total returns; 3Y and 5Y are CAGRs.
- Rolling 1Y figures are total returns for calendar-year holding windows. Rolling 3Y and 5Y
  figures are CAGRs using actual elapsed days. Best, worst, median, P25 and P75 describe
  the eligible overlapping windows. These windows are correlated observations.

### Risk formulas and target convention

- Annualised volatility: sample standard deviation (`ddof=1`) of eligible daily returns × √252.
- Running drawdown: `NAV/running maximum NAV - 1`. Maximum drawdown is its minimum
  (a negative fraction). A decline from 120 to 90 is −25%.
- Configurable annual risk-free rate `rf` is a user assumption, not a live market quote.
  Daily target `q=(1+rf)^(1/252)-1`.
- Daily excess return `e=r-q`. Downside deviation is `sqrt(mean(min(e,0)^2))*sqrt(252)`;
  the denominator includes **all** eligible daily observations, not only downside days.
- Sharpe = `mean(e)/std(r,ddof=1)*sqrt(252)`.
- Sortino = `mean(e)/sqrt(mean(min(e,0)^2))*sqrt(252)`.
- At least 30 daily observations are required for dispersion metrics. A zero denominator
  produces unavailable ratios. Ratios are unitless; returns/volatility use decimal fractions.

### Benchmark comparison

CSV imports have `date,benchmark_code,benchmark_name,tri_value`. Users must explicitly mark
verified **TRI** data. Price and unverified indices remain stored but are excluded from
fund/benchmark charts, relative metrics and scores. NAV data itself does not verify a benchmark.

Comparisons join exact common level dates and exclude multi-business-day gaps from daily
return differences. CAGR and excess CAGR are computed on identical start/end dates.
Tracking difference = fund CAGR − benchmark CAGR on those dates. Tracking error = sample
standard deviation of aligned daily fund-minus-benchmark returns × √252. Benchmark alignment
coverage is common observations / fund observations within the selected horizon.

The rolling win rate is the fraction of aligned one-year rolling windows with fund return
strictly greater than benchmark return. At least 252 eligible rolling windows are required.
Passive funds use **negative tracking error** as their benchmark scoring input, so tighter
tracking earns a higher peer percentile. Tracking difference is also displayed; a small
tracking error alone does not guarantee a small tracking difference.

### Comparable peers and normalisation

The peer key is **category + subcategory + Active/Passive + benchmark code**, evaluated at
the same analysis date. Metadata with an as-of date after that date is ineligible. Unknown
metadata is never inferred from a scheme name. At least three complete eligible peers are
required (including the selected fund). This small minimum is for demonstration, not evidence
of statistical reliability. Different plans/options sharing metadata may need further manual
classification before real-world use.

For `n` comparable values, average-rank percentile is `(average ascending rank-1)/(n-1)*100`.
Higher values receive higher percentiles; ties share their average rank. Lower-is-better
inputs are negated first (tracking error), or ranked in reverse. All-equal values receive 50.
The category percentile/rank uses 3Y CAGR among eligible comparable peers. A separate complete
cohort for all four inputs is used consistently across scoring components, so score peers may
be fewer than return-ranking peers. The cohort definition is visible and no unrelated category
is used to fill a small peer group.

### Experimental research score

| Component | Raw input, higher is better |
|---|---|
| Consistency | Median 1Y rolling return / (rolling P75 − P25 + 0.01) |
| Risk | Sortino ratio, using the displayed return target |
| Benchmark, active | 1Y rolling benchmark win rate |
| Benchmark, passive | Negative annualised tracking error |
| Recency | Trailing 1Y total return |

The consistency denominator uses a fixed **one percentage point** stabiliser to limit
division by a near-zero interquartile range. This is a documented heuristic, not a validated
economic model. Risk scoring does not assume lower volatility is universally preferable.

Each input is normalised to a peer percentile in [0,100]. Score = sum(component percentile ×
component weight). Category-specific weights live in `config/scoring_weights.yaml`; the
sidebar can override weights for the session. Weights must be non-negative and sum to 100%.
They are illustrative and not scientifically optimal. **Missing components withhold the
composite, even if the corresponding weight is zero**; weights are never silently redistributed.

Neutral labels: ≥75 Strong relative profile; ≥50 Above-median profile; ≥25 Mixed profile;
otherwise Below-median profile. Missing composite: Insufficient data. Thresholds are illustrative.
Contribution points are non-negative. Positive/negative comparisons in the lab are relative
to a midpoint peer baseline, not claims about positive/negative future performance.

### Historical snapshots and audit

Both comparison dates recalculate the complete eligible peer universe using only data
available on or before each date, and the same weights and risk-free rate. Changes are
described by deterministic templates; no market cause is inferred. Cohort changes can change
percentiles even when a fund's raw metric improves. Snapshot components store **weighted
contribution points**, which sum to the composite when available.

Snapshot version = methodology version plus a hash of weights and risk-free assumption.
Snapshots at the same date and version are idempotently updated after imports. This is an
analytical history, **not** a bitemporal reconstruction of what an analyst knew at import time:
late-arriving historical NAV can revise a past result. Metadata has one current record per
scheme, so replacing metadata can make older historical cohorts unavailable; metadata revision
history is not yet implemented. No missing older metadata is backfilled from a future record.

### Sources and limitations

- Official AMFI NAV downloads: https://www.amfiindia.com/net-asset-value/nav-download
- Manual historical files can be planned in inclusive windows of at most 90 calendar days.
  Automatic scraping is not required and is not implemented.
- Benchmark and metadata provenance are supplied by the importer and retained. The software
  validates structure and arithmetic, not the provider's economic accuracy or TRI declaration.
- DEMO DATA consists only of fictional schemes, fictional indices and fixed-seed synthetic
  paths. It does not reconstruct actual historical mutual fund or market performance.
- Missing expense ratio and AUM remain unavailable. Expense ratio units are annual percentage
  points; AUM is INR crore. They are not used to manufacture scores.
- NAV-based metrics exclude investor-specific fees, loads, taxes and cash-flow timing.
  No personalised recommendation or return guarantee is made.
- Weekday calendars, small cohorts, selection/survivorship effects and overlapping windows
  limit inference. Production work needs official trading calendars, stronger classifications,
  revised metadata history, source reconciliation and independent quantitative review.
