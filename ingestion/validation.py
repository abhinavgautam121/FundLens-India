"""Upload validation and audit-friendly row errors, without logging file contents."""

from datetime import date
from io import StringIO

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_BYTES = 20 * 1024 * 1024


def decode_file(content: bytes) -> str:
    if not content or len(content) > MAX_BYTES:
        raise ValueError("Upload a non-empty text file smaller than 20 MB.")
    if b"\x00" in content:
        raise ValueError("Binary files are not supported. Upload CSV or AMFI text.")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252")


def csv_rows(content: bytes, required: set[str]) -> list[dict]:
    try:
        df = pd.read_csv(StringIO(decode_file(content)), dtype=str, keep_default_na=False)
    except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ValueError("The file is not a readable comma-separated CSV.") from exc
    df.columns = df.columns.str.strip().str.lower()
    if not required.issubset(df.columns):
        raise ValueError(
            f"Required columns missing: {', '.join(sorted(required - set(df.columns)))}"
        )
    if df.empty:
        raise ValueError("The CSV contains no data rows.")
    return df.apply(lambda col: col.str.strip()).to_dict("records")


class NavRecord(BaseModel):
    scheme_code: str = Field(pattern=r"^\d+$", max_length=64)
    scheme_name: str = Field(min_length=1, max_length=300)
    nav_date: date
    nav: float = Field(gt=0, allow_inf_nan=False)

    @field_validator("nav_date")
    @classmethod
    def historical_date(cls, value):
        if value > date.today():
            raise ValueError("Future observations are not accepted.")
        return value


class BenchmarkRecord(BaseModel):
    date: date
    benchmark_code: str = Field(min_length=1, max_length=64)
    benchmark_name: str = Field(min_length=1, max_length=200)
    tri_value: float = Field(gt=0, allow_inf_nan=False)

    @field_validator("date")
    @classmethod
    def historical_date(cls, value):
        return NavRecord.historical_date(value)


class SchemeRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    scheme_code: str = Field(pattern=r"^\d+$", max_length=64)
    scheme_name: str = Field(min_length=1, max_length=300)
    amc_name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    subcategory: str = Field(min_length=1, max_length=100)
    fund_type: str
    benchmark_code: str = Field(min_length=1, max_length=64)
    inception_date: date
    expense_ratio: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    aum: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    data_source: str = Field(min_length=1, max_length=300)
    metadata_as_of: date

    @field_validator("fund_type")
    @classmethod
    def valid_type(cls, value):
        value = value.title()
        if value not in {"Active", "Passive"}:
            raise ValueError("Fund type must be Active or Passive.")
        return value

    @field_validator("metadata_as_of", "inception_date")
    @classmethod
    def historical_date(cls, value):
        return NavRecord.historical_date(value)


def date_windows(start: date, end: date, days: int = 90) -> list[tuple[date, date]]:
    """Inclusive historical request windows, each at most 90 calendar days."""
    from datetime import timedelta

    if start > end or not 1 <= days <= 90:
        raise ValueError("Choose an ordered date range and windows between 1 and 90 days.")
    result = []
    while start <= end:
        stop = min(start + timedelta(days=days - 1), end)
        result.append((start, stop))
        start = stop + timedelta(days=1)
    return result
