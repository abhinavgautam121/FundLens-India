# FundLens India — one-page business case

**Problem.** Investors and research teams see historical mutual fund returns, but a high return
can hide volatile outcomes, deep drawdowns, weak benchmark-relative consistency or poor data
coverage. A single unexplained rating makes it difficult to distinguish performance evidence
from the assumptions used to summarise it.

**Proposed solution.** An independent educational analytics platform turns imported AMFI NAV
files, verified benchmark TRI data and supplied scheme metadata into reproducible research.
Users explore funds, compare common historical dates, inspect rolling outcomes and risk,
and trace each experimental research score to normalised peer inputs and explicit weights.
Historical changes are described using measured differences, with unavailable data withheld.

**Target users.** Mutual fund product analysts, research/data teams and learners evaluating
how an analytics pipeline can support transparent research. This portfolio prototype is
intended to demonstrate Python, SQL, financial analysis, BI and product engineering skills.
It has no affiliation with PowerUp Money, AMFI, SEBI or any AMC.

**User value.** Evidence and caveats are available in one workflow: source and import audit,
coverage diagnostics, benchmark alignment, consistent peer groups, score contributions,
and portable CSV/Power BI exports. Manual uploads keep the research workflow usable when
an external website is unavailable.

**Demonstrated scope.** Seven connected Streamlit views; SQLAlchemy/SQLite persistence;
validated ingestion; return/rolling/risk/tracking calculations; configurable category weights;
deterministic change explanations; parameter-versioned snapshots; automated tests and real
application screenshots. Fictional fixed-seed data provides a reproducible first-launch demo.

**Success measures for a pilot.** Time to identify a data-quality issue; proportion of analysed
funds with complete traceable metadata and benchmarks; reconciliation rate against independent
calculations; research-report preparation time; users' ability to explain score contributions.
These are proposed measures, not claimed measured outcomes or commercial results.

**Constraints and next step.** Research scores are experimental, not investment advice.
Before production, add official trading calendars, historical metadata revisions, stronger
peer classification, independently reconciled data sources, larger cohorts and access-controlled
persistent deployment. Validate the product with research users and measure the proposed pilot
outcomes before claiming investor or business impact.
