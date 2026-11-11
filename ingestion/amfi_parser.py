"""Parse official AMFI semicolon files using header names, not column positions."""

import csv
from datetime import datetime
from io import StringIO

from pydantic import ValidationError

from ingestion.validation import NavRecord, decode_file


def parse_amfi(content: bytes) -> tuple[list[NavRecord], list[dict], int]:
    rows, issues, header = [], [], None
    count = 0
    names = {}
    for line, fields in enumerate(csv.reader(StringIO(decode_file(content)), delimiter=";"), 1):
        fields = [v.strip() for v in fields]
        if len(fields) <= 1:
            continue  # AMFI AMC/category headings are not NAV records.
        canonical = [" ".join(v.lower().split()) for v in fields]
        if "scheme code" in canonical:
            header = {v: i for i, v in enumerate(canonical)}
            if not {"scheme code", "scheme name", "net asset value", "date"}.issubset(header):
                raise ValueError(
                    "AMFI header must contain Scheme Code, Scheme Name, Net Asset Value, Date."
                )
            continue
        count += 1
        if header is None:
            raise ValueError(
                "AMFI header not found. Download an AMFI semicolon-delimited NAV file."
            )
        try:

            def field(key):
                return fields[header[key]]

            raw_date = field("date")
            parsed = None
            for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
                try:
                    parsed = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue
            if parsed is None:
                raise ValueError("Invalid NAV date.")
            record = NavRecord(
                scheme_code=field("scheme code"),
                scheme_name=field("scheme name"),
                nav_date=parsed,
                nav=field("net asset value"),
            )
            if record.scheme_code in names and names[record.scheme_code] != record.scheme_name:
                raise ValueError("Inconsistent scheme name for this scheme code.")
            names[record.scheme_code] = record.scheme_name
            rows.append(record)
        except (ValueError, IndexError, ValidationError):
            issues.append(
                {
                    "row": line,
                    "issue": "Invalid/missing scheme code, NAV, date, or inconsistent name.",
                }
            )
    if header is None or count == 0:
        raise ValueError("No AMFI NAV records found in this file.")
    return rows, issues, count
