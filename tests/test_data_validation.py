import json
from datetime import date

import pytest
from sqlalchemy import func, select

from database.connection import ImportLog, Nav, connect
from ingestion.amfi_parser import parse_amfi
from ingestion.validation import date_windows
from services.data_service import import_file

HEADER = "Scheme Code;ISIN Growth;ISIN Reinvestment;Scheme Name;Net Asset Value;Date\n"
ROW = "123456;INF1;INF2;Example Fund;100.25;03-Jan-2025\n"


def test_amfi_header_variants():
    records, issues, total = parse_amfi((HEADER + ROW).encode())
    assert not issues and total == 1
    assert records[0].nav == 100.25
    alternate = "Scheme Code;Scheme Name;Net Asset Value;Repurchase Price;Sale Price;Date\n123456;Example Fund;12;N.A.;N.A.;03-Jan-2025"
    assert parse_amfi(alternate.encode())[0][0].nav == 12


def test_duplicate_and_conflicting_nav_is_audited(tmp_path):
    _, factory = connect(f"sqlite:///{tmp_path}/test.db")
    assert (
        import_file(factory, "AMFI NAV", (HEADER + ROW).encode(), "a.txt", "AMFI")["inserted"] == 1
    )
    assert (
        import_file(factory, "AMFI NAV", (HEADER + ROW).encode(), "a.txt", "AMFI")["duplicates"]
        == 1
    )
    result = import_file(
        factory, "AMFI NAV", (HEADER + ROW.replace("100.25", "200")).encode(), "a.txt", "AMFI"
    )
    assert result["rejected"] == 1
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Nav)) == 1
        assert session.scalar(select(Nav.nav)) == 100.25
        log = session.scalars(select(ImportLog).order_by(ImportLog.import_id.desc())).first()
        assert "Conflicting" in json.loads(log.error_summary)[0]["issue"]


@pytest.mark.parametrize("payload", [b"not an AMFI file", b"\x00bad", b"", b"hello,wrong\nx,y"])
def test_incorrect_upload_is_audited(tmp_path, payload):
    _, factory = connect(f"sqlite:///{tmp_path}/test.db")
    assert import_file(factory, "AMFI NAV", payload, "bad.txt", "AMFI")["status"] == "rejected"
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(ImportLog)) == 1


def test_missing_values_and_invalid_nav():
    bad = "123456;;;Example Fund;N.A.;03-Jan-2025\n;;;;0;03-Jan-2025"
    records, errors, total = parse_amfi((HEADER + bad).encode())
    assert not records and len(errors) == total == 2


def test_historical_windows():
    windows = date_windows(date(2020, 1, 1), date(2020, 12, 31))
    assert len(windows) == 5
    assert all((b - a).days + 1 <= 90 for a, b in windows)
    assert windows[0][0] == date(2020, 1, 1) and windows[-1][1] == date(2020, 12, 31)
