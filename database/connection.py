"""Relational persistence. Use DATABASE_URL to select SQLite or PostgreSQL."""

from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Scheme(Base):
    __tablename__ = "schemes"
    scheme_id: Mapped[int] = mapped_column(primary_key=True)
    scheme_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scheme_name: Mapped[str] = mapped_column(String(300))
    amc_name: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    subcategory: Mapped[str | None] = mapped_column(String(100))
    fund_type: Mapped[str | None] = mapped_column(String(20))
    benchmark_code: Mapped[str | None] = mapped_column(ForeignKey("benchmarks.benchmark_code"))
    inception_date: Mapped[date | None] = mapped_column(Date)
    expense_ratio: Mapped[float | None] = mapped_column(Float)
    aum: Mapped[float | None] = mapped_column(Float)
    metadata_source: Mapped[str | None] = mapped_column(String(300))
    metadata_as_of: Mapped[date | None] = mapped_column(Date)


class Nav(Base):
    __tablename__ = "nav_history"
    __table_args__ = (UniqueConstraint("scheme_id", "nav_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.scheme_id"), index=True)
    nav_date: Mapped[date] = mapped_column(Date, index=True)
    nav: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(300))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Benchmark(Base):
    __tablename__ = "benchmarks"
    benchmark_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    benchmark_name: Mapped[str] = mapped_column(String(200))
    benchmark_type: Mapped[str] = mapped_column(String(30), default="TRI")


class BenchmarkValue(Base):
    __tablename__ = "benchmark_history"
    __table_args__ = (UniqueConstraint("benchmark_code", "benchmark_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    benchmark_code: Mapped[str] = mapped_column(ForeignKey("benchmarks.benchmark_code"), index=True)
    benchmark_date: Mapped[date] = mapped_column(Date, index=True)
    tri_value: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(300))


class Metric(Base):
    __tablename__ = "calculated_metrics"
    __table_args__ = (UniqueConstraint("scheme_id", "calculation_date", "period", "parameters"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.scheme_id"), index=True)
    calculation_date: Mapped[date] = mapped_column(Date, index=True)
    period: Mapped[str] = mapped_column(String(20))
    parameters: Mapped[str] = mapped_column(String(100))
    parameters_json: Mapped[str] = mapped_column(Text)
    total_return: Mapped[float | None] = mapped_column(Float)
    cagr: Mapped[float | None] = mapped_column(Float)
    annualised_volatility: Mapped[float | None] = mapped_column(Float)
    maximum_drawdown: Mapped[float | None] = mapped_column(Float)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float)
    sortino_ratio: Mapped[float | None] = mapped_column(Float)
    benchmark_excess_return: Mapped[float | None] = mapped_column(Float)
    tracking_error: Mapped[float | None] = mapped_column(Float)
    tracking_difference: Mapped[float | None] = mapped_column(Float)
    data_coverage: Mapped[float | None] = mapped_column(Float)
    rolling_median: Mapped[float | None] = mapped_column(Float)
    benchmark_win_rate: Mapped[float | None] = mapped_column(Float)


class Snapshot(Base):
    __tablename__ = "rating_snapshots"
    __table_args__ = (UniqueConstraint("scheme_id", "snapshot_date", "methodology_version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.scheme_id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    research_score: Mapped[float | None] = mapped_column(Float)
    category_percentile: Mapped[float | None] = mapped_column(Float)
    consistency_component: Mapped[float | None] = mapped_column(Float)
    risk_component: Mapped[float | None] = mapped_column(Float)
    benchmark_component: Mapped[float | None] = mapped_column(Float)
    recency_component: Mapped[float | None] = mapped_column(Float)
    methodology_version: Mapped[str] = mapped_column(String(100))
    parameters_json: Mapped[str] = mapped_column(Text)


class ImportLog(Base):
    __tablename__ = "data_import_logs"
    import_id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    data_source: Mapped[str] = mapped_column(String(300))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    records_processed: Mapped[int] = mapped_column(Integer)
    records_rejected: Mapped[int] = mapped_column(Integer)
    import_status: Mapped[str] = mapped_column(String(30))
    error_summary: Mapped[str] = mapped_column(Text, default="[]")
    duplicates: Mapped[int] = mapped_column(Integer, default=0)


Index("idx_scheme_peer_group", Scheme.category, Scheme.subcategory, Scheme.fund_type)


def connect(url: str):
    """Initialise tables; foreign keys are enforced for SQLite as well as PostgreSQL."""
    if url.startswith("sqlite:///") and ":memory:" not in url:
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url, **({"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {})
    )
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, sessionmaker(engine, expire_on_commit=False)
