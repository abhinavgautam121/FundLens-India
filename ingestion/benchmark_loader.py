from pydantic import ValidationError

from ingestion.validation import BenchmarkRecord, csv_rows


def parse_benchmark(content: bytes):
    raw = csv_rows(content, {"date", "benchmark_code", "benchmark_name", "tri_value"})
    rows, issues = [], []
    for line, row in enumerate(raw, 2):
        try:
            rows.append(BenchmarkRecord(**row))
        except ValidationError:
            issues.append(
                {
                    "row": line,
                    "issue": "Invalid benchmark code, name, ISO date, or positive index value.",
                }
            )
    return rows, issues, len(raw)
