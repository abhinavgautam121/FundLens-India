-- Initial SQLite schema generated from SQLAlchemy metadata.
PRAGMA foreign_keys=ON;

CREATE TABLE benchmarks (
	benchmark_code VARCHAR(64) NOT NULL,
	benchmark_name VARCHAR(200) NOT NULL,
	benchmark_type VARCHAR(30) NOT NULL,
	PRIMARY KEY (benchmark_code)
);

CREATE TABLE data_import_logs (
	import_id INTEGER NOT NULL,
	filename VARCHAR(300) NOT NULL,
	data_source VARCHAR(300) NOT NULL,
	uploaded_at DATETIME NOT NULL,
	records_processed INTEGER NOT NULL,
	records_rejected INTEGER NOT NULL,
	import_status VARCHAR(30) NOT NULL,
	error_summary TEXT NOT NULL,
	duplicates INTEGER NOT NULL,
	PRIMARY KEY (import_id)
);

CREATE TABLE benchmark_history (
	id INTEGER NOT NULL,
	benchmark_code VARCHAR(64) NOT NULL,
	benchmark_date DATE NOT NULL,
	tri_value FLOAT NOT NULL,
	source VARCHAR(300) NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (benchmark_code, benchmark_date),
	FOREIGN KEY(benchmark_code) REFERENCES benchmarks (benchmark_code)
);

CREATE INDEX ix_benchmark_history_benchmark_code ON benchmark_history (benchmark_code);

CREATE INDEX ix_benchmark_history_benchmark_date ON benchmark_history (benchmark_date);

CREATE TABLE schemes (
	scheme_id INTEGER NOT NULL,
	scheme_code VARCHAR(64) NOT NULL,
	scheme_name VARCHAR(300) NOT NULL,
	amc_name VARCHAR(200),
	category VARCHAR(100),
	subcategory VARCHAR(100),
	fund_type VARCHAR(20),
	benchmark_code VARCHAR(64),
	inception_date DATE,
	expense_ratio FLOAT,
	aum FLOAT,
	metadata_source VARCHAR(300),
	metadata_as_of DATE,
	PRIMARY KEY (scheme_id),
	FOREIGN KEY(benchmark_code) REFERENCES benchmarks (benchmark_code)
);

CREATE INDEX idx_scheme_peer_group ON schemes (category, subcategory, fund_type);

CREATE INDEX ix_schemes_category ON schemes (category);

CREATE UNIQUE INDEX ix_schemes_scheme_code ON schemes (scheme_code);

CREATE TABLE calculated_metrics (
	id INTEGER NOT NULL,
	scheme_id INTEGER NOT NULL,
	calculation_date DATE NOT NULL,
	period VARCHAR(20) NOT NULL,
	parameters VARCHAR(100) NOT NULL,
	parameters_json TEXT NOT NULL,
	total_return FLOAT,
	cagr FLOAT,
	annualised_volatility FLOAT,
	maximum_drawdown FLOAT,
	sharpe_ratio FLOAT,
	sortino_ratio FLOAT,
	benchmark_excess_return FLOAT,
	tracking_error FLOAT,
	tracking_difference FLOAT,
	data_coverage FLOAT,
	rolling_median FLOAT,
	benchmark_win_rate FLOAT,
	PRIMARY KEY (id),
	UNIQUE (scheme_id, calculation_date, period, parameters),
	FOREIGN KEY(scheme_id) REFERENCES schemes (scheme_id)
);

CREATE INDEX ix_calculated_metrics_calculation_date ON calculated_metrics (calculation_date);

CREATE INDEX ix_calculated_metrics_scheme_id ON calculated_metrics (scheme_id);

CREATE TABLE nav_history (
	id INTEGER NOT NULL,
	scheme_id INTEGER NOT NULL,
	nav_date DATE NOT NULL,
	nav FLOAT NOT NULL,
	source VARCHAR(300) NOT NULL,
	imported_at DATETIME NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (scheme_id, nav_date),
	FOREIGN KEY(scheme_id) REFERENCES schemes (scheme_id)
);

CREATE INDEX ix_nav_history_nav_date ON nav_history (nav_date);

CREATE INDEX ix_nav_history_scheme_id ON nav_history (scheme_id);

CREATE TABLE rating_snapshots (
	id INTEGER NOT NULL,
	scheme_id INTEGER NOT NULL,
	snapshot_date DATE NOT NULL,
	research_score FLOAT,
	category_percentile FLOAT,
	consistency_component FLOAT,
	risk_component FLOAT,
	benchmark_component FLOAT,
	recency_component FLOAT,
	methodology_version VARCHAR(100) NOT NULL,
	parameters_json TEXT NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (scheme_id, snapshot_date, methodology_version),
	FOREIGN KEY(scheme_id) REFERENCES schemes (scheme_id)
);

CREATE INDEX ix_rating_snapshots_scheme_id ON rating_snapshots (scheme_id);

CREATE INDEX ix_rating_snapshots_snapshot_date ON rating_snapshots (snapshot_date);
