"""CRF Rule Engine - browser app.

Runs locally with `streamlit run app/streamlit_app.py` or fully in the browser
with stlite (see app/build_stlite.py). In the browser version nothing is
uploaded anywhere: Python runs inside the page.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
for candidate in (HERE, HERE.parent / "src"):  # stlite: package next to the app; local: repo/src
    if (candidate / "crf_rules").is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from crf_rules import (compile_rules, generate_sas, load_corrections, load_specs,  # noqa: E402
                       queries_by_site, query_workbook, read_raw, report_workbook, run)

DEMO_DIRS = [HERE / "demo", HERE.parent]
DEMO_FILES = {
    "rules": "demo_fu12_rules.xlsx",
    "raw": "demo_fu12_raw.csv",
    "log": "demo_fu12_corrections_log.xlsx",
}


def demo_bytes(key: str) -> bytes:
    name = DEMO_FILES[key]
    for base in DEMO_DIRS:
        for sub in ("", "rules", "data", "corrections"):
            p = base / sub / name
            if p.exists():
                return p.read_bytes()
    raise FileNotFoundError(name)


@st.cache_data(show_spinner=False)
def analyse(rules: bytes, raw: bytes, log: bytes | None, use_log: bool):
    specs = load_specs(io.BytesIO(rules))
    corrections = load_corrections(io.BytesIO(log)) if (log and use_log) else None
    result = run(read_raw(io.BytesIO(raw)), specs, corrections=corrections)
    _, issues = compile_rules(specs)
    return specs, result, issues


st.set_page_config(page_title="CRF Rule Engine", page_icon="🩺", layout="wide")

# Compact header, prominent tab bar that stays at the top while scrolling
st.markdown(
    """
<style>
  header[data-testid="stHeader"] { display: none; }
  .block-container { padding-top: 1.5rem; }
  /* tab bar: the prominent navigation row at the top */
  div[data-testid="stTabs"] > div:first-child { padding: 0.2rem 0 0.6rem 0; }
  div[data-testid="stTabs"] [role="tablist"] {
      gap: 0.35rem; padding: 0.35rem; border-radius: 0.6rem; background: #e8eef7;
  }
  div[data-testid="stTabs"] [role="tab"] {
      padding: 0.5rem 0.9rem; border-radius: 0.45rem;
  }
  div[data-testid="stTabs"] [role="tab"] p { font-size: 1.02rem; font-weight: 600; }
  div[data-testid="stTabs"] [role="tab"][aria-selected="true"],
  div[data-testid="stTabs"] [role="tab"][data-selected] {
      background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,.15);
  }
  div[data-testid="stTabs"] .react-aria-SelectionIndicator { display: none; }
</style>
""",
    unsafe_allow_html=True,
)
st.markdown("#### 🩺 CRF Rule Engine &nbsp;·&nbsp; <span style='font-weight:400;font-size:0.95rem;color:#555'>"
            "Excel-driven plausibility checks for paper-CRF studies · "
            "<b>runs in your browser, no file leaves this computer</b></span>",
            unsafe_allow_html=True)

tabs = st.tabs(["Overview", "Findings", "Site queries", "Corrections & audit trail",
                "Rules", "SAS program", "How it works"])

with tabs[6]:
    st.markdown(
        """
### The cleaning cycle

| | Artifact | Who maintains it | When |
|---|---|---|---|
| 1 | **Data validation plan** - rules sheet, one row per CRF field | data management, versioned | fixed at study start, changes documented |
| 2 | **Raw export** from the scanner | nobody - never edited | every scan run |
| 3 | **Edit-check program** (SAS / this app) generated from 1 | generated, not hand-written | whenever 1 changes |
| 4 | **Query files** - one per site: *have, why, where*, site fills in *want* | data management -> sites | after every check run |
| 5 | **Correction log** - every change with who, what, when, why | data management | continuously |
| 6 | **Audit trail** - which corrections were applied or rejected | generated | every run |

**Cleaned data = raw export + correction log.** The raw export is never overwritten,
so every number in the analysis can be traced back to the scanned form.
A correction is applied only if the data still hold its `old_value`; otherwise it is
rejected as a conflict.

### Using this app
1. Click **Load fictional demo study** in the sidebar, or upload your own files.
2. *Overview* and *Findings* show what the rules found.
3. *Site queries* gives one Excel file per site to send out.
4. Answers go into the correction log; load it again and the answered queries disappear.
5. *SAS program* shows the same checks as a plain SAS program.
"""
    )

# ---------------------------------------------------------------- inputs
with st.sidebar:
    st.header("Input")
    if st.button("Load fictional demo study", width="stretch", type="primary"):
        st.session_state["demo"] = True
    up_rules = st.file_uploader("1  Data validation plan (rules .xlsx)", type=["xlsx"])
    up_raw = st.file_uploader("2  Raw scanner export (.csv, | separated)", type=["csv", "txt"])
    up_log = st.file_uploader("3  Correction log (.xlsx, optional)", type=["xlsx"])
    use_log = st.checkbox("Apply correction log", value=True,
                          help="Switch off to see the findings before any query was answered.")
    st.divider()
    st.caption("Demo study ACTIVE-65 is fictional; all data are synthetic.")

demo = st.session_state.get("demo", False)
rules_b = up_rules.getvalue() if up_rules else (demo_bytes("rules") if demo else None)
raw_b = up_raw.getvalue() if up_raw else (demo_bytes("raw") if demo else None)
log_b = up_log.getvalue() if up_log else (demo_bytes("log") if demo else None)

if not (rules_b and raw_b):
    for t in tabs[:6]:
        with t:
            st.info("Upload a rules sheet and a raw export in the sidebar, "
                    "or click **Load fictional demo study**. New here? See the tab **How it works**.")
    st.stop()

try:
    specs, result, issues = analyse(rules_b, raw_b, log_b, use_log)
except Exception as exc:  # show the problem instead of a stack trace
    with tabs[0]:
        st.error(f"Could not process the files: {exc}")
    st.stop()

f, cleaned, audit = result.findings, result.cleaned, result.audit
n = len(cleaned)
n_bad = int((cleaned["_n_findings"] > 0).sum())

# ---------------------------------------------------------------- overview
with tabs[0]:
    c = st.columns(5)
    c[0].metric("Questionnaires", n)
    c[1].metric("With open queries", n_bad, help=f"{100 * n_bad / n:.1f} % of all questionnaires" if n else None)
    c[2].metric("Findings", len(f))
    c[3].metric("Corrections applied", int((audit["status"] == "applied").sum()) if len(audit) else 0)
    c[4].metric("Corrections rejected", int((audit["status"] != "applied").sum()) if len(audit) else 0)
    if issues:
        st.warning(f"{len(issues)} rule(s) could not be used - see tab *Rules*.")
    if len(f):
        left, right = st.columns(2)
        with left:
            st.subheader("Findings per field")
            st.bar_chart(f["variable"].value_counts().sort_values())
        with right:
            st.subheader("Open queries per site")
            st.bar_chart(f.groupby("site")["id"].nunique().rename("participants"))
    else:
        st.success("No findings - the data meet every rule.")
    st.download_button("Download full report (.xlsx)", report_workbook(result),
                       file_name="plausibility_report.xlsx")

# ---------------------------------------------------------------- findings
with tabs[1]:
    c = st.columns(3)
    sites = c[0].multiselect("Site", sorted(f["site"].unique()))
    fields = c[1].multiselect("Field", sorted(f["variable"].unique()))
    kinds = c[2].multiselect("Type", ["format", "rule"])
    view = f
    if sites:
        view = view[view["site"].isin(sites)]
    if fields:
        view = view[view["variable"].isin(fields)]
    if kinds:
        view = view[view["type"].isin(kinds)]
    st.caption(f"{len(view)} of {len(f)} findings")
    st.dataframe(view.drop(columns=["rule"]), width="stretch", hide_index=True)
    with st.expander("Show the technical rule behind each finding"):
        st.dataframe(view[["query_id", "rule"]], width="stretch", hide_index=True)

# ---------------------------------------------------------------- queries
with tabs[2]:
    st.markdown("One Excel file per site, so every clinic sees **only its own participants**. "
                "Grey columns: *have* and *why*. Yellow columns: the site fills in *want* and the source.")
    tables = queries_by_site(result)
    if not tables:
        st.success("No open queries.")
    for site, table in tables.items():
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown(f"**Site {site}** - {len(table)} queries, {table['Participant ID'].nunique()} participants")
            b.download_button(f"queries_{site}.xlsx", query_workbook(table, site),
                              file_name=f"queries_{site}.xlsx", key=f"q_{site}")
            st.dataframe(table, width="stretch", hide_index=True, height=min(38 * (len(table) + 1), 300))

# ---------------------------------------------------------------- corrections
with tabs[3]:
    st.markdown("The correction log records every change: **who, what, when, why**. "
                "A correction is applied only if the data still contain `old_value`. "
                "Otherwise it is rejected as a *conflict*, so a stale answer can never overwrite newer data.")
    if not len(audit):
        st.info("No correction log loaded (or switched off in the sidebar).")
    else:
        conflicts = audit[audit["status"] != "applied"]
        if len(conflicts):
            st.error(f"{len(conflicts)} correction(s) not applied:")
            st.dataframe(conflicts, width="stretch", hide_index=True)
        st.dataframe(audit, width="stretch", hide_index=True)
        st.download_button("Download audit trail (.csv)", audit.to_csv(index=False).encode(),
                           file_name="audit_trail.csv")
    st.download_button("Download cleaned dataset (.csv)", cleaned.to_csv(index=False).encode(),
                       file_name="cleaned.csv")

# ---------------------------------------------------------------- rules
with tabs[4]:
    problems = {i.variable: i.problem for i in issues}
    table = pd.DataFrame([{
        "field": s.variable, "question": s.label, "format": s.fmt.code, "rule": s.rule,
        "message": s.message, "status": problems.get(s.variable, "ok" if s.rule else "no rule"),
    } for s in specs])
    st.markdown("Rules are written in SAS syntax; `#` stands for the field itself. "
                "A rule describes a **good** value.")
    st.dataframe(table, width="stretch", hide_index=True)

# ---------------------------------------------------------------- SAS
with tabs[5]:
    code = generate_sas(specs, source="rules sheet")
    st.markdown("The same checks as a plain SAS program. Set three paths at the top and run it.")
    st.download_button("Download edit_checks.sas", code.encode(), file_name="edit_checks.sas")
    st.code(code, language="sas")
