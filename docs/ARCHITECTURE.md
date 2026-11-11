# Architecture

The app runs as one Python process with an embedded SQLite database. Streamlit renders views;
reusable analytics functions contain the formulas; services orchestrate validated ingestion,
point-in-time computation, persistence and exports. No LLM or private API is required.

```mermaid
flowchart LR
    U[Browser] --> UI[Streamlit views]
    UI --> S[Application services]
    AMFI[Manual AMFI files] --> V[Pydantic validation]
    CSV[Benchmark and metadata CSV] --> V
    V --> I[Transactional import service]
    I --> DB[(SQLAlchemy / SQLite)]
    D[Fixed-seed DEMO generator] --> DDB[(Separate DEMO database)]
    S --> DB
    S --> DDB
    S --> A[Pure Python analytics]
    A --> P[Comparable peer percentiles]
    P --> R[Explainable research scores]
    R --> UI
    S --> BI[CSV / ZIP / Power BI]
```

## Data flow

```mermaid
flowchart TD
    F[File <=20 MB] --> H[Decode and validate header]
    H --> R[Validate each row]
    R --> C[Detect duplicate and conflicting observations]
    C --> T[Transaction: accepted records + audit log]
    T --> A[Cut off NAV, benchmark and metadata by analysis date]
    A --> M[Calendar returns, rolling windows, risk and benchmark metrics]
    M --> E[History, freshness and coverage eligibility]
    E --> G[Group category/subcategory/type/benchmark peers]
    G --> N[Normalise complete cohort]
    N --> S[Score + contribution breakdown or withheld result]
    S --> X[Parameter-versioned snapshots and exports]
```

## Database ER diagram

```mermaid
erDiagram
    schemes ||--o{ nav_history : scheme_id
    schemes ||--o{ calculated_metrics : scheme_id
    schemes ||--o{ rating_snapshots : scheme_id
    benchmarks ||--o{ benchmark_history : benchmark_code
    benchmarks ||--o{ schemes : benchmark_code
    data_import_logs {
        int import_id PK
        string filename
        string data_source
        datetime uploaded_at
        int records_processed
        int records_rejected
        int duplicates
        string import_status
        text error_summary
    }
    schemes {
        int scheme_id PK
        string scheme_code UK
        string scheme_name
        string category
        string subcategory
        string fund_type
        string benchmark_code FK
        date metadata_as_of
    }
    nav_history {
        int id PK
        int scheme_id FK
        date nav_date
        float nav
        string source
        datetime imported_at
    }
    calculated_metrics {
        int id PK
        int scheme_id FK
        date calculation_date
        string period
        string parameters
        text parameters_json
    }
    rating_snapshots {
        int id PK
        int scheme_id FK
        date snapshot_date
        float research_score
        string methodology_version
        text parameters_json
    }
```

`database/schema.sql` is generated from SQLAlchemy metadata and includes the complete fields,
indexes and uniqueness constraints. Foreign keys are enabled for SQLite. Observation imports
do not overwrite conflicts. Data-import audit is file-grained with sanitised row error messages;
it does not retain raw uploaded payloads or personal financial details.

## Runtime and deployment boundaries

- Streamlit uses its native widget/websocket protocol. No separate API server is introduced.
- The demo and uploaded databases must have different URLs. No synthetic fallback contaminates
  uploaded-data analytics. Uploaded data starts empty and remains clearly labelled.
- SQLite is intended for a single-instance educational deployment. Multi-user/public uploads
  share that instance's dataset; this is not a private per-user storage product. Use access
  controls at the deployment host for an internal research workspace.
- SQLAlchemy is portable to PostgreSQL; install an appropriate driver, set `DATABASE_URL`,
  and validate deployment-specific concurrency/backups. PostgreSQL operation is prepared,
  but is not part of the locally verified SQLite runtime.
- Initial schema creation is automatic. See `database/migrations/README.md` for future upgrades.
- Streamlit Community Cloud requires only the repository and Python dependencies. Sites'
  Cloudflare Worker runtime does not host this Python/Streamlit application.
