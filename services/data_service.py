"""Transactional imports. Conflicting observations are reported, never overwritten."""

import json
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import select

from database.connection import Benchmark, BenchmarkValue, ImportLog, Nav, Scheme
from ingestion.amfi_parser import parse_amfi
from ingestion.benchmark_loader import parse_benchmark
from ingestion.scheme_loader import parse_schemes

logger = logging.getLogger(__name__)


def import_file(
    factory,
    kind: str,
    content: bytes,
    filename: str,
    source: str,
    benchmark_type: str = "Unverified",
) -> dict:
    if kind not in {"AMFI NAV", "Benchmark CSV", "Scheme metadata CSV"}:
        raise ValueError("Unknown import type.")
    if not source.strip() or len(source) > 300:
        raise ValueError("A traceable data source of at most 300 characters is required.")
    if benchmark_type not in {"TRI", "Price", "Unverified"}:
        raise ValueError("Unknown benchmark type.")
    parsers = {
        "AMFI NAV": parse_amfi,
        "Benchmark CSV": parse_benchmark,
        "Scheme metadata CSV": parse_schemes,
    }
    try:
        rows, issues, total = parsers[kind](content)
    except ValueError as exc:
        issues, rows, total = [{"row": 0, "issue": str(exc)}], [], 1
    inserted, duplicates = 0, 0
    with factory.begin() as session:
        schemes = {s.scheme_code: s for s in session.scalars(select(Scheme))}
        benchmarks = {b.benchmark_code: b for b in session.scalars(select(Benchmark))}
        navs = {(n.scheme_id, n.nav_date): n.nav for n in session.scalars(select(Nav))}
        values = {
            (b.benchmark_code, b.benchmark_date): b.tri_value
            for b in session.scalars(select(BenchmarkValue))
        }
        metadata_seen = set()
        for i, row in enumerate(rows, 2):
            if kind == "AMFI NAV":
                scheme = schemes.get(row.scheme_code)
                if scheme is None:
                    scheme = Scheme(scheme_code=row.scheme_code, scheme_name=row.scheme_name)
                    session.add(scheme)
                    session.flush()
                    schemes[row.scheme_code] = scheme
                if scheme.scheme_name != row.scheme_name:
                    issues.append(
                        {
                            "row": i,
                            "issue": "Scheme name differs from stored metadata; review metadata before importing.",
                        }
                    )
                    continue
                key = (scheme.scheme_id, row.nav_date)
                if key in navs:
                    duplicates += 1
                    if navs[key] != row.nav:
                        issues.append(
                            {
                                "row": i,
                                "issue": "Conflicting duplicate NAV; stored observation preserved.",
                            }
                        )
                    continue
                session.add(
                    Nav(
                        scheme_id=scheme.scheme_id,
                        nav_date=row.nav_date,
                        nav=row.nav,
                        source=source,
                    )
                )
                navs[key] = row.nav
            elif kind == "Benchmark CSV":
                if row.benchmark_code not in benchmarks:
                    benchmark = Benchmark(
                        benchmark_code=row.benchmark_code,
                        benchmark_name=row.benchmark_name,
                        benchmark_type=benchmark_type,
                    )
                    session.add(benchmark)
                    session.flush()
                    benchmarks[row.benchmark_code] = benchmark
                existing = benchmarks[row.benchmark_code]
                if (
                    existing.benchmark_name != row.benchmark_name
                    or existing.benchmark_type != benchmark_type
                ):
                    issues.append(
                        {
                            "row": i,
                            "issue": "Benchmark name/type conflicts with stored definition; use a distinct code.",
                        }
                    )
                    continue
                key = (row.benchmark_code, row.date)
                if key in values:
                    duplicates += 1
                    if values[key] != row.tri_value:
                        issues.append(
                            {
                                "row": i,
                                "issue": "Conflicting duplicate benchmark value; stored observation preserved.",
                            }
                        )
                    continue
                session.add(
                    BenchmarkValue(
                        benchmark_code=row.benchmark_code,
                        benchmark_date=row.date,
                        tri_value=row.tri_value,
                        source=source,
                    )
                )
                values[key] = row.tri_value
            else:
                if row.scheme_code in metadata_seen:
                    duplicates += 1
                    issues.append({"row": i, "issue": "Duplicate metadata scheme code in file."})
                    continue
                metadata_seen.add(row.scheme_code)
                if row.benchmark_code not in benchmarks:
                    issues.append(
                        {"row": i, "issue": "Benchmark code not found. Import benchmark CSV first."}
                    )
                    continue
                scheme = schemes.get(row.scheme_code)
                if scheme is not None and scheme.metadata_as_of is not None:
                    if row.metadata_as_of < scheme.metadata_as_of:
                        issues.append(
                            {"row": i, "issue": "Older metadata cannot replace newer metadata."}
                        )
                        continue
                fields = row.model_dump(exclude={"data_source"})
                fields["metadata_source"] = row.data_source
                if scheme is None:
                    scheme = Scheme(**fields)
                    session.add(scheme)
                    schemes[row.scheme_code] = scheme
                else:
                    for key, value in fields.items():
                        setattr(scheme, key, value)
            inserted += 1
        status = "success" if not issues else ("partial" if inserted else "rejected")
        session.add(
            ImportLog(
                filename=Path(filename).name[:300],
                data_source=source,
                records_processed=total,
                records_rejected=len(issues),
                duplicates=duplicates,
                import_status=status,
                error_summary=json.dumps(issues),
            )
        )
    logger.info(
        "Import completed: kind=%s status=%s inserted=%d rejected=%d duplicates=%d",
        kind,
        status,
        inserted,
        len(issues),
        duplicates,
    )
    return {
        "status": status,
        "processed": total,
        "inserted": inserted,
        "rejected": len(issues),
        "duplicates": duplicates,
        "issues": issues,
    }


def read_tables(engine) -> dict[str, pd.DataFrame]:
    tables = [
        "schemes",
        "nav_history",
        "benchmarks",
        "benchmark_history",
        "calculated_metrics",
        "rating_snapshots",
        "data_import_logs",
    ]
    return {name: pd.read_sql_table(name, engine) for name in tables}
