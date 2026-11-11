# MASTER PROJECT BUILD PROMPT
# FundLens India – Explainable Mutual Fund Intelligence Platform

## 1. YOUR ROLE

Act as a Senior Fintech Product Engineer, Data Scientist, Quantitative Research Analyst, Python Developer, Database Architect, UI/UX Designer and QA Engineer.

Your responsibility is to design, develop, test, document and deploy a complete, professional-grade fintech analytics application called:

**FundLens India – Explainable Mutual Fund Intelligence Platform**

This is an independent portfolio project developed to demonstrate my capabilities in Data Analytics, Business Intelligence, Financial Data Analysis, Python, SQL and product development.

The product should be of sufficient quality to demonstrate to the product, analytics and engineering teams at PowerUp Money.

Do not create a basic college project. Build a polished, functional, data-driven application with a real analytical foundation.

---

## 2. BUSINESS PROBLEM

Indian mutual fund investors can see returns and performance figures, but interpreting those numbers is difficult.

A fund may have excellent historical returns but also experience high volatility, inconsistent performance or significant drawdowns.

Investors need a transparent way to understand:

1. Why a fund is performing well or poorly.
2. Whether its performance is consistent across different market periods.
3. How it performs compared with its benchmark.
4. How it compares with funds in the same category.
5. Whether its risk profile has changed.
6. What factors contributed to changes in its analytical score.
7. Whether the available data is sufficient to make a meaningful assessment.

The business opportunity is to improve the transparency, explainability and accessibility of mutual fund research.

### Core product proposition

Do not just show investors a score.

Explain the data behind the score, the calculations used, the comparison group, the historical evidence and the limitations of the analysis.

---

## 3. PRODUCT VISION

Build a web-based application that transforms raw mutual fund NAV data into understandable financial insights.

The platform should allow users to:

- Explore mutual funds.
- Analyse fund performance.
- Compare funds belonging to the same category.
- Evaluate rolling returns.
- Understand volatility and drawdowns.
- Compare funds against benchmarks.
- View historical analytical score changes.
- Understand why a score or metric changed.
- Download reports and structured datasets.

### Key differentiator

**Explainable Analytics over Black-Box Ratings.**

Every analytical score must have a visible explanation.

For example:

A fund receives an experimental Research Score of 78/100.

The user should be able to understand:

- Rolling return consistency contributed 31 points.
- Benchmark-relative performance contributed 24 points.
- Risk-adjusted performance contributed 15 points.
- Recent performance contributed 8 points.

All these numbers must be calculated dynamically from actual imported data.

Do not hardcode example scores into the production calculations.

---

## 4. TECHNOLOGY STACK

Use the following technologies.

### Backend and data processing
- Python 3.11+
- Pandas
- NumPy
- Scikit-learn where appropriate
- SQLAlchemy
- Pydantic for input validation

### Database
- SQLite for the initial local application.
- Design the database layer so PostgreSQL can be supported later.
- Use SQL for meaningful analytical queries.

### Frontend
- Streamlit
- Plotly
- Custom CSS for professional styling.

### Testing and development
- Pytest
- Ruff
- Git and GitHub
- Python logging
- Environment variables using .env

### Business intelligence
- Generate Power BI-ready analytical datasets.
- Include SQL scripts for important business questions.
- Provide a Power BI dashboard specification and data model.

Do not introduce unnecessary technologies just to make the architecture look complicated.

---

## 5. DATA SOURCES AND INGESTION

Data accuracy is extremely important.

Use official and traceable data sources wherever possible.

### Primary source: AMFI

Official website:
https://www.amfiindia.com/net-asset-value/nav-download

Use publicly accessible mutual fund NAV data.

The application should support:

1. Uploading downloaded AMFI NAV files.
2. Parsing NAV records.
3. Normalising scheme information.
4. Validating historical records.
5. Storing cleaned records in the database.
6. Detecting duplicates.
7. Handling missing and invalid values.

Support AMFI historical NAV imports in configurable date ranges. Handle the limitation of up to 90 days per historical download request.

Do not depend entirely on automatic website scraping. Manual upload must work even when the external website is unavailable.

### Benchmark data

Allow benchmark data to be imported through CSV.

Expected format:

date,benchmark_code,benchmark_name,tri_value

Use Total Return Index data wherever available.

Do not silently compare mutual fund returns against a price index while presenting the result as a total-return comparison.

### Scheme metadata

Support another CSV upload containing:

- Scheme code
- Scheme name
- AMC name
- Category
- Subcategory
- Fund type: Active / Passive
- Benchmark code
- Inception date
- Expense ratio (optional)
- AUM (optional)
- Data source
- Metadata as-of date

Do not invent missing scheme metadata.

Display unavailable metrics as unavailable rather than manufacturing values.

### Data quality

Detect and report:

- Missing NAV observations
- Duplicate records
- Invalid NAV values
- Missing scheme codes
- Inconsistent scheme names
- Stale NAV data
- Incomplete date coverage
- Benchmark alignment problems
- Insufficient historical records

Maintain an audit trail showing the source and import date of the data.

### Demo dataset

Generate deterministic synthetic data using a fixed random seed.

Include:
- Multiple demo fund categories.
- Multiple fictional mutual fund schemes.
- Benchmark series.
- Different performance patterns.
- High-volatility and low-volatility examples.
- Funds with inconsistent performance.
- Funds with strong and weak benchmark-relative performance.

Clearly label all synthetic information as DEMO DATA.

Never present synthetic returns as actual historical mutual fund performance.

---

## 6. DATABASE DESIGN

Create a well-structured relational database.

### Table 1: schemes

Fields:
- scheme_id
- scheme_code
- scheme_name
- amc_name
- category
- subcategory
- fund_type
- benchmark_code
- inception_date
- expense_ratio
- aum
- metadata_source
- metadata_as_of

### Table 2: nav_history

Fields:
- id
- scheme_id
- nav_date
- nav
- source
- imported_at

Use scheme_id and nav_date as a unique logical combination.

### Table 3: benchmarks

Fields:
- benchmark_code
- benchmark_name
- benchmark_type

### Table 4: benchmark_history

Fields:
- id
- benchmark_code
- benchmark_date
- tri_value
- source

### Table 5: calculated_metrics

Fields:
- id
- scheme_id
- calculation_date
- period
- total_return
- cagr
- annualised_volatility
- maximum_drawdown
- sharpe_ratio
- sortino_ratio
- benchmark_excess_return
- tracking_error
- tracking_difference
- data_coverage

### Table 6: rating_snapshots

Fields:
- id
- scheme_id
- snapshot_date
- research_score
- category_percentile
- consistency_component
- risk_component
- benchmark_component
- recency_component
- methodology_version

### Table 7: data_import_logs

Fields:
- import_id
- filename
- data_source
- uploaded_at
- records_processed
- records_rejected
- import_status
- error_summary

Create suitable indexes and foreign keys.

Store database creation scripts and explain the data model.

---

## 7. FINANCIAL ANALYTICS ENGINE

This is the most important part of the project.

Write calculations in separate, reusable Python modules.

Do not put all calculations inside Streamlit pages.

All formulas must be documented, tested and reproducible.

### A. Return analysis

Calculate:

1. 1-month return
2. 3-month return
3. 6-month return
4. 1-year return
5. 3-year CAGR
6. 5-year CAGR
7. Cumulative return

CAGR:

CAGR = (Ending NAV / Starting NAV) ^ (365.25 / Number of calendar days) - 1

Only calculate a metric when sufficient valid historical data exists.

### B. Rolling return analysis

Calculate:

- Rolling 1-year returns.
- Rolling 3-year returns.
- Rolling 5-year returns where data permits.
- Median rolling returns.
- Best rolling return.
- Worst rolling return.
- 25th and 75th percentile rolling returns.
- Percentage of eligible rolling periods outperforming the benchmark.

Display the distribution of rolling returns using Plotly.

Explain rolling returns in simple language.

### C. Risk analysis

Calculate:

**Annualised volatility**

Standard deviation of daily returns multiplied by square root of 252.

**Maximum drawdown**

The largest percentage decline from a previous running NAV peak.

**Downside deviation**

Measure the dispersion of returns below a specified target.

**Sharpe ratio**

Calculate from excess returns using a configurable annual risk-free rate.

**Sortino ratio**

Use downside deviation and the same documented return target convention.

Do not silently assume a live risk-free rate. Allow configuration and display the chosen assumption.

Show all metrics with appropriate units and explanations.

### D. Benchmark analysis

Compare mutual fund returns against the selected benchmark.

Calculate:

- Benchmark CAGR.
- Fund CAGR.
- Excess return.
- Rolling excess return.
- Tracking difference.
- Tracking error.
- Benchmark-relative consistency.

Tracking error should use the annualised standard deviation of daily fund-minus-benchmark returns.

Tracking difference should be clearly defined and calculated using aligned annualised return series.

For passive funds, emphasise tracking quality.

### E. Category-relative analysis

Compare funds only with comparable funds.

For every fund, calculate its percentile among its eligible category peers.

Show:

- Category rank.
- Peer count.
- Median category return.
- Category volatility distribution.
- Category-relative consistency.

Never compare unrelated categories directly.

Do not assign a meaningful percentile when the peer group is too small or data is incomplete.

### F. Historical changes

Allow the user to select two analysis dates.

Explain what changed between those dates.

Examples:
- Volatility increased.
- Rolling return consistency declined.
- Benchmark-relative performance improved.
- Maximum drawdown became more severe.
- Category percentile changed.

All explanations must be based on calculated historical differences.

Do not invent explanations for changes that the data cannot explain.

---

## 8. EXPLAINABLE RESEARCH SCORE

Develop an independent, configurable analytical scoring framework.

This is an educational research metric, NOT a PowerUp Money rating and NOT an investment recommendation.

Use category-specific scoring configurations.

Potential dimensions:

| Dimension | What it measures |
|---|---|
| Consistency | Stability of rolling return performance |
| Risk | Volatility and downside risk indicators |
| Benchmark | Performance relative to benchmark |
| Recency | Recent performance relative to peers |

Create configurable weights in a separate YAML configuration file.

A sample configuration for demo purposes can be:

- Consistency: 35%
- Risk-adjusted performance: 25%
- Benchmark-relative performance: 25%
- Recency: 15%

Do not represent these weights as scientifically optimal.

Users should be able to modify the weights.

Ensure the weights add up to 100%.

Normalise metrics within comparable peer groups using a documented method.

For metrics where lower values are preferable, reverse the percentile direction appropriately.

Do not assume lower volatility is universally better across all categories.

### Score calculation

Research Score = Sum of (Component Score × Component Weight)

Show a full breakdown of each component's contribution.

Provide a methodology explanation panel.

If important metrics are missing, flag the score as incomplete or withhold the composite score. Never silently redistribute missing weights.

### Profile labels

Use neutral, educational labels such as:

- Strong relative profile
- Above-median profile
- Mixed profile
- Below-median profile
- Insufficient data

These must describe the analytical result only.

Do not use Buy, Sell, Hold, Exit or Switch labels.

---

## 9. APPLICATION PAGES

Build a complete, navigable application with the following pages.

### Page 1: Executive Overview

Create a professional dashboard showing:

- Total funds analysed.
- Number of categories.
- Number of benchmark series.
- Latest data date.
- Number of funds with sufficient history.
- Data quality alerts.
- Category-level performance overview.
- Distribution of research profiles.
- Top and bottom funds by selected analytical metric, with data coverage clearly shown.

Include filter controls.

### Page 2: Fund Explorer

Build a searchable and filterable mutual fund table.

Filters:

- AMC
- Category
- Subcategory
- Active / Passive
- Benchmark
- Historical period
- Data availability

Table columns:

- Fund name
- Category
- Latest available NAV
- 1-year return
- 3-year CAGR
- Annualised volatility
- Maximum drawdown
- Category percentile
- Research score

Enable sorting and CSV export.

### Page 3: Fund Deep Dive

This is the main analytical page.

When a user selects a fund, show:

1. NAV history chart.
2. Normalised growth chart with a common starting value of 100.
3. Cumulative returns.
4. Rolling return distribution.
5. Benchmark comparison.
6. Volatility history.
7. Maximum drawdown chart.
8. Risk metric cards.
9. Category-relative comparison.
10. Research score breakdown.

Every chart needs a meaningful title, axis label, legend and tooltip.

### Page 4: Fund Comparison

Allow users to compare up to four mutual funds.

Show:

- Historical returns.
- Rolling returns.
- Volatility.
- Drawdown.
- Sharpe ratio.
- Sortino ratio.
- Benchmark-relative returns.
- Research score.
- Category percentile.

Use a common comparison date range where possible.

Clearly flag comparisons across different categories.

### Page 5: Explainability Lab

Make this a standout feature.

Display the research score and its component breakdown.

Create an interactive visualisation explaining:

- Which metrics contributed positively.
- Which metrics contributed negatively.
- How much each metric contributed.
- How the fund compares with peers.
- How its analytical profile changed across snapshots.

Add a section called:

**Why did this score change?**

Compare two selected snapshots and display actual metric differences.

Include a plain-English explanation generated using deterministic templates from calculated facts.

Do not require an LLM API for the core application.

### Page 6: Data Quality Centre

Build a professional data-quality monitoring page.

Display:

- Records imported.
- Duplicate records.
- Missing values.
- Invalid observations.
- Stale data.
- Incomplete history.
- Benchmark matching failures.
- Unrated funds due to inadequate data.

Provide clear error messages and downloadable validation reports.

### Page 7: Methodology and Assumptions

Document:

- Calculation formulas.
- Data sources.
- Peer-group selection.
- Scoring weights.
- Normalisation approach.
- Benchmark selection.
- Annualisation assumptions.
- Missing-data policy.
- Data refresh dates.
- Known limitations.

A user must be able to understand how every important metric is calculated.

---

## 10. USER EXPERIENCE AND DESIGN

Build a premium fintech interface.

Design should look like a genuine financial analytics SaaS product.

### Visual direction

- Clean modern interface.
- Professional typography.
- Dark navy or slate navigation.
- White or subtle neutral content backgrounds.
- Consistent spacing.
- Restrained use of green, amber and red.
- Rounded analytical cards.
- Professional Plotly charts.
- Mobile-responsive layout.

Avoid:
- Excessive gradients.
- Too many decorative elements.
- Emoji-heavy interfaces.
- Unnecessary animations.
- Generic Streamlit-looking default screens.

Add:

- Sidebar navigation.
- Clear page titles.
- Loading states.
- Empty states.
- Error handling.
- Informative tooltips.
- Consistent number formatting.
- INR formatting where relevant.
- Date formatting suitable for Indian users.

Make the interface polished enough to record a professional product demonstration.

---

## 11. POWER BI INTEGRATION

Prepare a separate `powerbi/` directory.

Generate clean CSV exports for:

- Fund dimensions.
- Category dimensions.
- Date dimensions.
- Daily NAV fact table.
- Fund performance metrics.
- Benchmark metrics.
- Research score snapshots.

Create a star schema recommendation.

Include SQL queries answering business questions such as:

1. Which fund categories have the highest median rolling returns?
2. Which funds show the greatest volatility?
3. Which funds consistently outperform their benchmark?
4. Which funds have experienced significant drawdowns?
5. Which funds have improved their category percentile over time?

Provide a `POWER_BI_GUIDE.md` explaining how to import the exported data and build executive dashboards.

---

## 12. SECURITY, COMPLIANCE AND RESPONSIBLE USE

This project is an independent educational analytics prototype.

Important requirements:

- Do not use PowerUp Money's logo, branding or proprietary source code.
- Do not claim affiliation, partnership or endorsement.
- Do not copy its exact proprietary rating formula or thresholds.
- Do not imply that this application replicates PowerUp's internal system.
- Do not issue personalised financial recommendations.
- Do not generate buy/sell/switch decisions.
- Do not guarantee future returns.
- Clearly disclose that historical performance does not guarantee future results.
- Do not collect unnecessary personal financial information.
- Validate uploaded files.
- Do not expose API keys or secrets.
- Do not log sensitive user data.

Display this disclaimer:

"FundLens India is an independent educational mutual fund analytics prototype. It is not affiliated with or endorsed by PowerUp Money, AMFI, SEBI or any asset management company. Its analytical scores are experimental research indicators and do not constitute investment advice or recommendations. Past performance does not guarantee future results. Verify all data and consult a qualified, appropriately registered professional before making investment decisions."

---

## 13. PROJECT FOLDER STRUCTURE

Create an organised, production-style repository.

Use a structure similar to:

FundLens-India/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env.example
├── Dockerfile
│
├── config/
│   ├── settings.yaml
│   └── scoring_weights.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── demo/
│
├── database/
│   ├── schema.sql
│   ├── connection.py
│   └── migrations/
│
├── ingestion/
│   ├── amfi_parser.py
│   ├── benchmark_loader.py
│   ├── scheme_loader.py
│   └── validation.py
│
├── analytics/
│   ├── returns.py
│   ├── rolling_returns.py
│   ├── risk_metrics.py
│   ├── benchmark_analysis.py
│   ├── peer_analysis.py
│   ├── scoring.py
│   └── explainability.py
│
├── services/
│   ├── data_service.py
│   ├── fund_service.py
│   └── report_service.py
│
├── pages/
│   ├── overview.py
│   ├── fund_explorer.py
│   ├── fund_detail.py
│   ├── fund_comparison.py
│   ├── explainability.py
│   ├── data_quality.py
│   └── methodology.py
│
├── visualizations/
│   ├── performance_charts.py
│   ├── risk_charts.py
│   └── comparison_charts.py
│
├── sql/
│   └── business_queries.sql
│
├── powerbi/
│   └── POWER_BI_GUIDE.md
│
├── tests/
│   ├── test_returns.py
│   ├── test_risk_metrics.py
│   ├── test_benchmark.py
│   ├── test_scoring.py
│   ├── test_data_validation.py
│   └── test_no_lookahead.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── METHODOLOGY.md
│   ├── DATA_DICTIONARY.md
│   └── USER_GUIDE.md
│
└── .github/
    └── workflows/
        └── tests.yml

You may improve this structure if there is a clear technical reason.

---

## 14. TESTING AND VALIDATION

Write actual unit and integration tests.

At minimum, test:

1. CAGR calculations.
2. Daily returns.
3. Rolling returns.
4. Annualised volatility.
5. Maximum drawdown.
6. Sharpe and Sortino ratios.
7. Benchmark alignment.
8. Tracking error.
9. Category percentile.
10. Research score calculation.
11. Missing data handling.
12. Duplicate NAV handling.
13. Incorrect file uploads.
14. Insufficient historical data.
15. No-look-ahead-bias validation.

Include hand-calculated examples.

Example:

Starting NAV = 100
Ending NAV = 121
Period = 2 years

Expected CAGR = 10%.

Ensure that the application does not use observations after the selected analysis date when computing historical results.

Test that composite scores cannot be produced incorrectly when required metrics are missing.

Run all tests before considering the project complete.

---

## 15. DOCUMENTATION AND GITHUB PRESENTATION

Create an outstanding README.

It should contain:

1. Project introduction.
2. Business problem.
3. Proposed solution.
4. Product features.
5. System architecture.
6. Technology stack.
7. Data sources.
8. Database schema.
9. Analytical methodology.
10. Screenshots.
11. Installation instructions.
12. How to import AMFI data.
13. How to launch the application.
14. Test instructions.
15. Known limitations.
16. Compliance disclaimer.

Also generate:

- Architecture diagram using Mermaid.
- Data flow diagram.
- Database ER diagram.
- Sample analytical report.
- Example SQL queries.
- Project demonstration script.
- A one-page business case describing the problem and solution.

Use screenshots captured from the real working application. Never fabricate screenshots or claim features are working when they are not.

---

## 16. DEPLOYMENT

Prepare the project for deployment.

Preferred options:

- Streamlit Community Cloud for an initial public demonstration.
- Docker for reproducible local execution.

Requirements:

- No hardcoded secrets.
- Demo data available on first launch.
- Database initialisation automated.
- Clear environment setup.
- Graceful handling of missing external data.
- No dependency on private APIs.

Provide exact deployment instructions.

If deployment credentials are unavailable, prepare and test the application locally rather than claiming that it has been deployed.

---

## 17. DEVELOPMENT EXECUTION PLAN

Work in the following phases.

Do not skip phases.

### Phase 1 – Project foundation
- Inspect the existing repository.
- Create the folder structure.
- Configure Python dependencies.
- Initialise the database.
- Create synthetic demo data.
- Verify that the basic application runs.

### Phase 2 – Data engineering
- Implement AMFI file ingestion.
- Build benchmark CSV ingestion.
- Create validation rules.
- Store clean records in SQLite.
- Test duplicate handling and data quality.

### Phase 3 – Analytics engine
- Implement return calculations.
- Implement rolling returns.
- Implement risk metrics.
- Implement benchmark analysis.
- Implement category comparisons.
- Implement scoring and explainability.

### Phase 4 – Application development
- Create all seven application pages.
- Implement interactive filters.
- Build charts and tables.
- Connect all analytics to the interface.
- Add exports and report generation.

### Phase 5 – Quality assurance
- Run unit tests.
- Run integration tests.
- Fix errors.
- Validate metrics with independent calculations.
- Test all pages using demo data.
- Verify that uploaded data works.

### Phase 6 – Professionalisation
- Improve UI/UX.
- Complete documentation.
- Generate architecture diagrams.
- Prepare Power BI exports.
- Write GitHub README.
- Prepare deployment configuration.

### Phase 7 – Demonstration
Create a 3–5 minute product demonstration covering:

1. Business problem.
2. Fund Explorer.
3. Deep Dive.
4. Benchmark comparison.
5. Explainability Lab.
6. Data Quality Centre.
7. Business impact and limitations.

---

## 18. IMPORTANT CODING INSTRUCTIONS

Follow these instructions throughout development:

1. First inspect the existing files and environment.
2. Do not destroy existing working code unnecessarily.
3. Build the project in small, verifiable phases.
4. Create actual files in the repository, not just code snippets in chat.
5. Do not leave important features as placeholder buttons.
6. Do not use fake hardcoded values in live analytical calculations.
7. Do not hide failed calculations or data-quality errors.
8. Do not silently substitute missing values.
9. Keep analytical calculations separate from UI code.
10. Write reusable functions with type hints and comments.
11. Use proper exception handling.
12. Execute tests after implementing each important module.
13. Fix errors rather than merely describing them.
14. Keep the application runnable at every major milestone.
15. Do not stop after generating the folder structure.

When you encounter an unavailable dataset, implement the manual-upload workflow and continue using clearly labelled demo data.

Make sensible technical decisions without repeatedly asking me for clarification.

If a feature cannot be implemented reliably, explain the limitation and provide the best working alternative.

---

## 19. FINAL ACCEPTANCE CRITERIA

The project is complete only when:

- The application starts successfully.
- Synthetic demo data loads on first launch.
- AMFI NAV files can be uploaded and parsed.
- Benchmark data can be uploaded.
- The database stores and retrieves records.
- All major performance and risk metrics work.
- Fund comparisons work.
- Category-relative analysis works.
- Research scores are explainable.
- Historical score changes can be examined.
- Data-quality errors are visible.
- CSV exports work.
- Power BI-ready data is generated.
- The main unit and integration tests pass.
- README and setup documentation are complete.
- The app has a professional interface.
- Compliance disclaimers are visible.

At the end, provide:

1. Complete project folder.
2. Working application.
3. Installation and execution commands.
4. Test results.
5. Screenshots of the real product.
6. GitHub-ready README.
7. Known limitations.
8. Suggestions for the next iteration.

**Final objective: Build a credible, working fintech analytics product that demonstrates my ability to identify a business problem, work with financial data, build an analytics pipeline, design meaningful metrics and convert analysis into a usable product.**
