"""Smoke test of the Streamlit app with the demo study (skipped without streamlit)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"


def test_app_runs_with_demo_study():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("demo study" in b.label for b in at.sidebar.button)
    at.sidebar.button[0].click().run()
    assert not at.exception
    labels = {m.label: m.value for m in at.metric}
    assert labels["Questionnaires"] == "300"
    assert int(labels["Corrections rejected"]) == 1


def test_app_without_correction_log():
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    at.sidebar.button[0].click().run()
    at.sidebar.checkbox[0].uncheck().run()
    assert not at.exception
    labels = {m.label: m.value for m in at.metric}
    assert labels["Corrections applied"] == "0"
