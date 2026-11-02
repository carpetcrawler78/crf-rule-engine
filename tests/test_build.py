"""docs/index.html (the stlite page) must contain the current sources."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_stlite_page_is_up_to_date(tmp_path):
    spec = importlib.util.spec_from_file_location("build_stlite", ROOT / "app" / "build_stlite.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    fresh = mod.build(tmp_path / "index.html").read_text(encoding="utf-8")
    committed = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert fresh == committed, "run: python app/build_stlite.py"
