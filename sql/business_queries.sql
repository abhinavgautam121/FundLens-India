-- SQLite queries. Bind :analysis_date ('YYYY-MM-DD') and :parameters from calculated_metrics.
-- Parameters identify the full risk-free/weight/eligibility configuration; never mix versions.

-- 1. Categories with the highest median of per-fund median 1Y rolling returns.
-- This is a two-stage descriptive median, not the median of every pooled daily window.
WITH ranked AS (
    SELECT s.category, m.rolling_median,
           ROW_NUMBER() OVER (PARTITION BY s.category ORDER BY m.rolling_median) AS rn,
           COUNT(*) OVER (PARTITION BY s.category) AS n
    FROM calculated_metrics m JOIN schemes s ON s.scheme_id = m.scheme_id
    WHERE m.calculation_date = :analysis_date AND m.parameters = :parameters
      AND m.period = '3Y' AND m.rolling_median IS NOT NULL AND s.category IS NOT NULL
)
SELECT category, AVG(rolling_median) AS median_rolling_return
FROM ranked WHERE rn IN ((n+1)/2, (n+2)/2)
GROUP BY category ORDER BY median_rolling_return DESC;

-- 2. Volatility extremes, with peer group and coverage for interpretation.
SELECT s.scheme_name, s.category, s.subcategory, s.fund_type,
       m.annualised_volatility, m.data_coverage
FROM calculated_metrics m JOIN schemes s ON m.scheme_id = s.scheme_id
WHERE m.calculation_date = :analysis_date AND m.parameters = :parameters
  AND m.period = '3Y' AND m.annualised_volatility IS NOT NULL
ORDER BY s.category, m.annualised_volatility DESC;

-- 3. Consistent benchmark outperformance (descriptive threshold, not a recommendation).
SELECT s.scheme_name, s.category, s.benchmark_code,
       m.benchmark_win_rate, m.benchmark_excess_return, m.data_coverage
FROM calculated_metrics m JOIN schemes s ON m.scheme_id = s.scheme_id
WHERE m.calculation_date = :analysis_date AND m.parameters = :parameters
  AND m.period = '3Y' AND m.benchmark_win_rate >= 0.60 AND m.data_coverage >= 0.90
ORDER BY s.category, m.benchmark_win_rate DESC;

-- 4. Drawdowns of at least 20% within the 3Y horizon (negative sign convention).
SELECT s.scheme_name, s.category, m.maximum_drawdown, m.data_coverage
FROM calculated_metrics m JOIN schemes s ON m.scheme_id = s.scheme_id
WHERE m.calculation_date = :analysis_date AND m.parameters = :parameters
  AND m.period = '3Y' AND m.maximum_drawdown <= -0.20
ORDER BY m.maximum_drawdown;

-- 5. Percentile improvements between :earlier_date and :later_date.
-- Bind :methodology_version; values and peers can both change.
SELECT s.scheme_name, s.category, a.category_percentile AS earlier_percentile,
       b.category_percentile AS later_percentile,
       b.category_percentile-a.category_percentile AS change_points
FROM rating_snapshots a
JOIN rating_snapshots b ON a.scheme_id = b.scheme_id
                       AND a.methodology_version = b.methodology_version
JOIN schemes s ON s.scheme_id = a.scheme_id
WHERE a.snapshot_date = :earlier_date AND b.snapshot_date = :later_date
  AND a.methodology_version = :methodology_version
  AND b.category_percentile > a.category_percentile
ORDER BY change_points DESC;
