"""Real Streamlit execution tests, including each navigation route."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_DATABASE_URL", f"sqlite:///{tmp_path}/demo.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/uploaded.db")
    return AppTest.from_file(
        Path(__file__).resolve().parents[1] / "app.py", default_timeout=60
    ).run()


def test_demo_all_seven_pages(app):
    assert not app.exception
    routes = list(app.sidebar.radio[0].options)
    assert len(routes) == 7
    for route in routes:
        app.sidebar.radio[0].set_value(route).run()
        assert not app.exception, f"Failed route: {route}"
    assert "Methodology" in app.title[0].value


def test_uploaded_empty_state_and_import_page(app):
    app.sidebar.selectbox[0].set_value("Uploaded data").run()
    assert not app.exception
    assert any("No funds" in x.value for x in app.info)
    app.sidebar.radio[0].set_value("Data Quality Centre").run()
    assert not app.exception
    assert any("Validate and import" == x.label and not x.disabled for x in app.button)


def test_invalid_weights_are_visible(app):
    app.sidebar.checkbox[0].set_value(True).run()
    app.sidebar.number_input[1].set_value(90.0).run()
    assert not app.exception
    assert any("sum to 100%" in x.value for x in app.error)


def test_analysis_before_first_observation_is_an_empty_state(app):
    from datetime import date

    app.sidebar.date_input[0].set_value(date(2018, 1, 1)).run()
    assert not app.exception
    app.sidebar.radio[0].set_value("Fund Deep Dive").run()
    assert not app.exception
    assert any("No NAV observations" in item.value for item in app.info)
