from pydantic import ValidationError

from ingestion.validation import SchemeRecord, csv_rows


def parse_schemes(content: bytes):
    raw = csv_rows(
        content,
        {
            "scheme_code",
            "scheme_name",
            "amc_name",
            "category",
            "subcategory",
            "fund_type",
            "benchmark_code",
            "inception_date",
            "data_source",
            "metadata_as_of",
        },
    )
    rows, issues = [], []
    for line, row in enumerate(raw, 2):
        for key in ("expense_ratio", "aum"):
            if not row.get(key):
                row[key] = None
        try:
            record = SchemeRecord(**row)
            if record.inception_date > record.metadata_as_of:
                raise ValueError("Inception is after metadata date.")
            rows.append(record)
        except (ValidationError, ValueError):
            issues.append(
                {
                    "row": line,
                    "issue": "Invalid scheme metadata; check dates, required fields, and fund type.",
                }
            )
    return rows, issues, len(raw)
