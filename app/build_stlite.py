"""Build docs/index.html: the Streamlit app running fully in the browser (stlite).

All Python sources and the demo files are embedded in the page, so it is a
single static file. Host it on GitHub Pages (Settings -> Pages -> branch main,
folder /docs) or open it through any static web server:

    python app/build_stlite.py
    python -m http.server -d docs 8000      # then open http://localhost:8000
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STLITE = "1.12.0"  # @stlite/browser, Pyodide 314 / Python 3.14, Streamlit 1.65

TEXT = {
    "streamlit_app.py": ROOT / "app" / "streamlit_app.py",
    **{f"crf_rules/{p.name}": p for p in sorted((ROOT / "src" / "crf_rules").glob("*.py"))},
    "demo/demo_fu12_raw.csv": ROOT / "data" / "demo_fu12_raw.csv",
}
BINARY = {
    "demo/demo_fu12_rules.xlsx": ROOT / "rules" / "demo_fu12_rules.xlsx",
    "demo/demo_fu12_corrections_log.xlsx": ROOT / "corrections" / "demo_fu12_corrections_log.xlsx",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CRF Rule Engine</title>
  <meta name="description" content="Excel-driven plausibility checks for paper-CRF studies, running entirely in the browser." />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@__V__/build/stlite.css" />
  <style>
    body { margin: 0; font-family: system-ui, sans-serif; }
    #boot { padding: 2rem; color: #444; }
  </style>
</head>
<body>
  <div id="root"><p id="boot">Starting Python in your browser (first load takes about 20-40 s)&hellip;</p></div>
  <script type="module">
    import { mount } from "https://cdn.jsdelivr.net/npm/@stlite/browser@__V__/build/stlite.js";
    const FILES = __FILES__;
    const b64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
    const files = {};
    for (const [path, v] of Object.entries(FILES)) files[path] = typeof v === "string" ? v : b64(v.b64);
    document.getElementById("root").innerHTML = "";
    mount(
      { requirements: ["openpyxl"], entrypoint: "streamlit_app.py", files },
      document.getElementById("root"),
    );
  </script>
</body>
</html>
"""


def build(out: Path = ROOT / "docs" / "index.html") -> Path:
    files: dict[str, object] = {k: p.read_text(encoding="utf-8") for k, p in TEXT.items()}
    files.update({k: {"b64": base64.b64encode(p.read_bytes()).decode()} for k, p in BINARY.items()})
    payload = json.dumps(files).replace("</", "<\\/")  # never close the <script> tag early
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(PAGE.replace("__V__", STLITE).replace("__FILES__", payload), encoding="utf-8")
    return out


if __name__ == "__main__":
    p = build()
    print(f"written {p} ({p.stat().st_size / 1024:.0f} KB)")
