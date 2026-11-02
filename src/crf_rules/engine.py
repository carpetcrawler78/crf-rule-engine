"""The data-cleaning cycle of a paper-CRF study.

    1. rules sheet  (data validation plan, fixed at study start, versioned)
    2. raw export   (scanner output, never edited by hand)
    3. correction log (every change: who, what, when, why)  -> audit trail
    4. checks       (format + plausibility rules) on raw + corrections
    5. outputs      cleaned dataset, findings, one query file per site
"""

from __future__ import annotations

import datetime as _dt
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .formats import FieldFormat, parse_format
from .rules import MISSING, CompiledRule, RuleError, from_sas_date, to_sas_date, translate

# Column names accepted in the rules sheet (English demo layout and the
# German layout of the original scanner definition files).
_ALIASES = {
    "variable": ["variable", "datensatzvariable", "endvariablenname"],
    "label": ["label", "question", "beschreibung", "fb_fragenummer"],
    "coding": ["coding", "kodierung"],
    "format": ["format", "variablen-typ", "variablen_typ", "formatcode"],
    "rule": ["rule", "regel", "logik_korrekt"],
    "message": ["message", "fehlermeldung"],
}

CORRECTION_COLUMNS = [
    "correction_id", "query_id", "id", "variable", "old_value", "new_value",
    "reason", "source", "date", "changed_by",
]
_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")
FINDING_COLUMNS = ["query_id", "site", "id", "variable", "question", "value", "type", "message", "rule"]


@dataclass
class FieldSpec:
    variable: str
    fmt: FieldFormat
    rule: str = ""
    message: str = ""
    label: str = ""
    coding: str = ""


@dataclass
class RuleIssue:
    variable: str
    rule: str
    problem: str


@dataclass
class Result:
    cleaned: pd.DataFrame
    findings: pd.DataFrame
    audit: pd.DataFrame
    rule_issues: list[RuleIssue] = field(default_factory=list)

    @property
    def errors(self) -> pd.DataFrame:  # backwards compatible name
        return self.findings

    @property
    def summary(self) -> pd.DataFrame:
        n = len(self.cleaned)
        n_bad = int((self.cleaned["_n_findings"] > 0).sum()) if n else 0
        st = self.audit["status"] if len(self.audit) else pd.Series(dtype=str)
        rows = [
            ("records", n),
            ("records without findings", n - n_bad),
            ("records with findings (open queries)", n_bad),
            ("share with findings (%)", round(100 * n_bad / n, 1) if n else 0.0),
            ("findings total", len(self.findings)),
            ("  format findings", int((self.findings["type"] == "format").sum())),
            ("  rule findings", int((self.findings["type"] == "rule").sum())),
            ("corrections applied", int((st == "applied").sum())),
            ("corrections NOT applied (conflict)", int((st != "applied").sum())),
            ("rules that could not be used", len(self.rule_issues)),
        ]
        return pd.DataFrame(rows, columns=["measure", "value"], dtype=object)


# --------------------------------------------------------------------------
# 1. Rules sheet (data validation plan)
# --------------------------------------------------------------------------
def load_specs(path: str | Path | io.BytesIO, sheet: str | int = 0) -> list[FieldSpec]:
    """Read the rules sheet. One row per CRF field."""
    df = pd.read_excel(path, sheet_name=sheet, dtype=str, keep_default_na=False).fillna("")
    lookup = {c.strip().lower(): c for c in df.columns}
    cols = {key: next((lookup[n] for n in names if n in lookup), None) for key, names in _ALIASES.items()}
    if cols["variable"] is None or cols["format"] is None:
        raise ValueError(f"rules sheet needs a variable and a format column (found: {list(df.columns)})")

    specs = []
    for _, row in df.iterrows():
        var = row[cols["variable"]].strip()
        if not var or var.startswith("#"):  # scanner metadata rows such as #Date
            continue

        def get(key: str) -> str:
            return row[cols[key]].strip() if cols[key] else ""

        specs.append(FieldSpec(var, parse_format(get("format")), get("rule"), get("message"),
                               get("label"), get("coding")))
    return specs


def compile_rules(specs: list[FieldSpec]) -> tuple[list[tuple[FieldSpec, CompiledRule]], list[RuleIssue]]:
    """Translate every rule. Broken rules are reported, not raised."""
    columns = [s.variable for s in specs]
    compiled, issues = [], []
    for s in specs:
        if not s.rule:
            continue
        try:
            compiled.append((s, translate(s.rule, s.variable, columns)))
        except RuleError as exc:
            issues.append(RuleIssue(s.variable, s.rule, str(exc)))
    issues += [RuleIssue(s.variable, s.fmt.code, "unknown format code, read as text")
               for s in specs if not s.fmt.known]
    return compiled, issues


# --------------------------------------------------------------------------
# 2. Raw export  /  3. correction log
# --------------------------------------------------------------------------
def read_raw(path: str | Path | io.BytesIO, sep: str = "|") -> pd.DataFrame:
    """Read a scanner export: one line per questionnaire, every value as text."""
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def load_corrections(path: str | Path | io.BytesIO | None) -> pd.DataFrame:
    """Read the correction log (Excel). Every cell is treated as text."""
    if path is None:
        return pd.DataFrame(columns=CORRECTION_COLUMNS)
    df = pd.read_excel(path, dtype=str, keep_default_na=False).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in ("id", "variable", "old_value", "new_value") if c not in df.columns]
    if missing:
        raise ValueError(f"correction log lacks columns {missing}")
    for c in CORRECTION_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    return df[CORRECTION_COLUMNS].apply(lambda s: s.str.strip())


def apply_corrections(raw: pd.DataFrame, log: pd.DataFrame, id_var: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the correction log to a copy of the raw data.

    A correction is applied only if the value currently in the data equals
    ``old_value``. Otherwise it is reported as a conflict - this protects
    against corrections that were meant for an older version of the data.
    The raw export itself is never changed: cleaned = raw + log.
    """
    data = raw.copy()
    by_lower = {c.lower(): c for c in data.columns}
    rows = []
    # corrections of the ID itself last, so the other rows still find their record
    order = log.assign(_is_id=log["variable"].str.lower() == id_var.lower()).sort_values("_is_id", kind="stable")
    for _, c in order.iterrows():
        rec = c.to_dict()
        rec.pop("_is_id", None)
        col = by_lower.get(c["variable"].lower())
        hit = data.index[data[id_var].str.strip() == c["id"]]
        if col is None:
            rec.update(found_value="", status="unknown variable")
        elif len(hit) == 0:
            rec.update(found_value="", status="unknown id")
        else:
            found = data.at[hit[0], col].strip()
            rec["found_value"] = found
            if found == c["old_value"]:
                data.loc[hit, col] = c["new_value"]
                rec["status"] = "applied"
            else:
                rec["status"] = "conflict"
        rows.append(rec)
    audit = pd.DataFrame(rows, columns=CORRECTION_COLUMNS + ["found_value", "status"])
    return data, audit


# --------------------------------------------------------------------------
# 4. Checks
# --------------------------------------------------------------------------
def _convert(value: str, fmt: FieldFormat) -> tuple[Any, str | None]:
    """Return (typed value, format problem or None)."""
    v = value.strip()
    if v == "":
        return (MISSING if fmt.kind in ("num", "date") else ""), None
    if fmt.kind == "char":
        return v, (f"text longer than {fmt.max_len} characters" if len(v) > fmt.max_len else None)
    if fmt.kind == "date":
        try:
            return to_sas_date(_dt.datetime.strptime(v, "%Y%m%d").date()), None
        except ValueError:
            return MISSING, "not a valid date (YYYYMMDD)"
    if not _NUMBER.match(v):
        return MISSING, "not a number"
    return float(v), None


def _display(value: Any, fmt: FieldFormat) -> str:
    if value is None or value == MISSING:
        return ""
    if fmt.kind == "date":
        return from_sas_date(value).isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def run(raw: pd.DataFrame, specs: list[FieldSpec], id_var: str | None = None,
        site_var: str | None = None, corrections: pd.DataFrame | None = None) -> Result:
    id_var = id_var or specs[0].variable
    names = [s.variable for s in specs]
    if site_var is None:
        site_var = next((n for n in names if n.lower() == "site"), None)
    missing_cols = [n for n in names if n not in raw.columns]
    if missing_cols:
        raise ValueError(f"raw data lacks columns defined in the rules sheet: {missing_cols}")

    log = corrections if corrections is not None else load_corrections(None)
    data, audit = apply_corrections(raw, log, id_var)
    compiled, issues = compile_rules(specs)
    label = {s.variable: s.label for s in specs}

    findings, typed_rows = [], []
    for _, rec in data.iterrows():
        row, out = {}, []
        rid = rec[id_var].strip().lstrip("0") or rec[id_var].strip()
        site = rec[site_var].strip() if site_var else ""

        def add(var: str, value: str, kind: str, message: str, rule: str) -> None:
            out.append({"query_id": f"Q-{rid}-{var}", "site": site, "id": rid, "variable": var,
                        "question": label.get(var, ""), "value": value, "type": kind,
                        "message": message, "rule": rule})

        for s in specs:
            row[s.variable], problem = _convert(rec[s.variable], s.fmt)
            if problem:
                add(s.variable, rec[s.variable], "format", problem, s.fmt.code)
        for s, rule in compiled:
            try:
                ok, msg = rule.evaluate(row), s.message or "rule violated"
            except Exception as exc:  # type clash etc. - report per record
                ok, msg = False, f"rule could not be evaluated ({type(exc).__name__})"
            if not ok:
                add(s.variable, _display(row[s.variable], s.fmt), "rule", msg, rule.sas)
        typed = {s.variable: _clean_value(row[s.variable], s.fmt) for s in specs}
        typed["_n_findings"] = len(out)
        typed["_finding_vars"] = ", ".join(dict.fromkeys(f["variable"] for f in out))
        typed_rows.append(typed)
        findings += out

    fdf = pd.DataFrame(findings, columns=FINDING_COLUMNS)
    fdf = fdf.sort_values(["site", "id", "type", "variable"], kind="stable").reset_index(drop=True)
    return Result(cleaned=pd.DataFrame(typed_rows), findings=fdf, audit=audit, rule_issues=issues)


def _clean_value(value: Any, fmt: FieldFormat) -> Any:
    if value == MISSING:
        return pd.NA
    if fmt.kind == "date":
        return from_sas_date(value)
    if fmt.kind == "num" and isinstance(value, float) and value.is_integer():
        return int(value)
    return value


# --------------------------------------------------------------------------
# 5. Outputs
# --------------------------------------------------------------------------
QUERY_HEADERS = {
    "query_id": "Query ID",
    "site": "Site",
    "id": "Participant ID",
    "question": "Question",
    "variable": "Field",
    "value": "Current value (have)",
    "message": "Problem (why)",
    "correct_value": "Correct value (want) - filled in by site",
    "site_comment": "Comment / source document - site",
    "answered": "Answered by / date - site",
}


def queries_by_site(result: Result) -> dict[str, pd.DataFrame]:
    """One query table per site, in the layout sent to the clinics."""
    q = result.findings.assign(correct_value="", site_comment="", answered="")
    q = q[list(QUERY_HEADERS)].rename(columns=QUERY_HEADERS)
    if not len(q):
        return {}
    return {site or "no_site": part.reset_index(drop=True) for site, part in q.groupby("Site", sort=True)}


def _format_sheet(ws, wide: tuple[int, ...] = ()) -> None:
    from openpyxl.styles import Alignment, Font, PatternFill

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DCE6F1")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    for col in ws.columns:
        width = max(len(str(c.value or "")) for c in col[:300])
        ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 12), 60)
    for idx in wide:
        for c in list(ws.columns)[idx][1:]:
            c.fill = PatternFill("solid", fgColor="FFF2CC")  # fields the site fills in


def query_workbook(table: pd.DataFrame, site: str) -> bytes:
    """Excel file for one site: queries + short instructions."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        table.to_excel(xl, sheet_name="queries", index=False)
        _format_sheet(xl.book["queries"], wide=(7, 8, 9))
        pd.DataFrame({"How to answer": [
            f"Queries for site {site}. Please answer every row in the yellow columns.",
            "Correct value (want): the value from the source document, or 'confirmed' if the current value is right.",
            "Comment: where the value was checked (e.g. original questionnaire, page 2).",
            "Return the file to data management. Do not change the grey columns.",
        ]}).to_excel(xl, sheet_name="how_to_answer", index=False)
        xl.book["how_to_answer"].column_dimensions["A"].width = 110
    return buf.getvalue()


def report_workbook(result: Result) -> bytes:
    buf = io.BytesIO()
    issues = pd.DataFrame([vars(i) for i in result.rule_issues], columns=["variable", "rule", "problem"])
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        result.summary.to_excel(xl, sheet_name="summary", index=False)
        result.findings.to_excel(xl, sheet_name="findings", index=False)
        result.audit.to_excel(xl, sheet_name="audit_trail", index=False)
        issues.to_excel(xl, sheet_name="rule_problems", index=False)
        for ws in xl.book.worksheets:
            _format_sheet(ws)
    return buf.getvalue()


def write_outputs(result: Result, outdir: str | Path) -> dict[str, Path]:
    out = Path(outdir)
    (out / "queries").mkdir(parents=True, exist_ok=True)
    paths = {"cleaned": out / "cleaned.csv", "report": out / "plausibility_report.xlsx",
             "audit": out / "audit_trail.csv"}
    result.cleaned.to_csv(paths["cleaned"], index=False)
    result.audit.to_csv(paths["audit"], index=False)
    paths["report"].write_bytes(report_workbook(result))
    stamp = _dt.date.today().isoformat()
    for site, table in queries_by_site(result).items():
        p = out / "queries" / f"queries_{site}_{stamp}.xlsx"
        p.write_bytes(query_workbook(table, site))
        paths[f"queries_{site}"] = p
    return paths
