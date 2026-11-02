"""Read the rules sheet, type the raw export, run the checks, write reports."""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .formats import FieldFormat, parse_format
from .rules import MISSING, CompiledRule, RuleError, to_sas_date, translate

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
    errors: pd.DataFrame
    rule_issues: list[RuleIssue] = field(default_factory=list)

    @property
    def summary(self) -> pd.DataFrame:
        n = len(self.cleaned)
        n_bad = int((self.cleaned["_n_errors"] > 0).sum()) if n else 0
        rows = [
            ("records", n),
            ("records without findings", n - n_bad),
            ("records with findings", n_bad),
            ("share with findings (%)", round(100 * n_bad / n, 1) if n else 0.0),
            ("findings total", len(self.errors)),
            ("format findings", int((self.errors["type"] == "format").sum())),
            ("rule findings", int((self.errors["type"] == "rule").sum())),
            ("rules that could not be used", len(self.rule_issues)),
        ]
        return pd.DataFrame(rows, columns=["measure", "value"], dtype=object)


# --------------------------------------------------------------------------
# Rules sheet
# --------------------------------------------------------------------------
def load_specs(path: str | Path, sheet: str | int = 0) -> list[FieldSpec]:
    """Read the rules sheet. One row per CRF field."""
    df = pd.read_excel(path, sheet_name=sheet, dtype=str).fillna("")
    lookup = {c.strip().lower(): c for c in df.columns}
    cols: dict[str, str | None] = {}
    for key, names in _ALIASES.items():
        cols[key] = next((lookup[n] for n in names if n in lookup), None)
    if cols["variable"] is None or cols["format"] is None:
        raise ValueError(
            f"{path}: rules sheet needs a variable column and a format column "
            f"(found: {list(df.columns)})"
        )

    specs = []
    for _, row in df.iterrows():
        var = row[cols["variable"]].strip()
        if not var or var.startswith("#"):  # scanner metadata rows such as #Date
            continue
        specs.append(
            FieldSpec(
                variable=var,
                fmt=parse_format(row[cols["format"]]),
                rule=row[cols["rule"]].strip() if cols["rule"] else "",
                message=row[cols["message"]].strip() if cols["message"] else "",
                label=row[cols["label"]].strip() if cols["label"] else "",
                coding=row[cols["coding"]].strip() if cols["coding"] else "",
            )
        )
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
    for s in specs:
        if not s.fmt.known:
            issues.append(RuleIssue(s.variable, s.fmt.code, "unknown format code, read as text"))
    return compiled, issues


# --------------------------------------------------------------------------
# Raw data
# --------------------------------------------------------------------------
def read_raw(path: str | Path, sep: str = "|") -> pd.DataFrame:
    """Read a scanner export: one line per questionnaire, every value as text."""
    return pd.read_csv(path, sep=sep, dtype=str, keep_default_na=False)


def _convert(value: str, fmt: FieldFormat) -> tuple[Any, str | None]:
    """Return (typed value, format problem or None)."""
    v = value.strip()
    if v == "":
        return (MISSING if fmt.kind in ("num", "date") else ""), None
    if fmt.kind == "char":
        if len(v) > fmt.max_len:
            return v, f"text longer than {fmt.max_len} characters"
        return v, None
    if fmt.kind == "date":
        try:
            return to_sas_date(_dt.datetime.strptime(v, "%Y%m%d").date()), None
        except ValueError:
            return MISSING, "not a valid date (YYYYMMDD)"
    # numeric
    if not v.lstrip("-").replace(".", "", 1).isdigit():
        return MISSING, "not numeric"
    if len(v.lstrip("-").split(".")[0]) > fmt.max_len:
        return float(v), f"more than {fmt.max_len} digits"
    return float(v), None


def type_data(raw: pd.DataFrame, specs: list[FieldSpec], id_var: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    missing_cols = [s.variable for s in specs if s.variable not in raw.columns]
    if missing_cols:
        raise ValueError(f"raw data lacks columns defined in the rules sheet: {missing_cols}")
    rows, findings = [], []
    for _, rec in raw.iterrows():
        typed: dict[str, Any] = {}
        for s in specs:
            val, problem = _convert(rec[s.variable], s.fmt)
            typed[s.variable] = val
            if problem:
                findings.append(
                    {"id": rec[id_var], "variable": s.variable, "value": rec[s.variable],
                     "type": "format", "rule": s.fmt.code, "message": problem}
                )
        rows.append(typed)
    return rows, findings


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------
def _display(value: Any, fmt: FieldFormat) -> str:
    if value == MISSING or value is None:
        return "."
    if fmt.kind == "date":
        from .rules import from_sas_date

        return from_sas_date(value).isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def run(raw: pd.DataFrame, specs: list[FieldSpec], id_var: str | None = None) -> Result:
    id_var = id_var or specs[0].variable
    compiled, issues = compile_rules(specs)
    fmt_of = {s.variable: s.fmt for s in specs}
    rows, findings = type_data(raw, specs, id_var)

    for row in rows:
        rid = _display(row[id_var], fmt_of[id_var])
        for spec, rule in compiled:
            try:
                ok = rule.evaluate(row)
            except Exception as exc:  # type clash etc. - report per record
                ok, msg = False, f"rule could not be evaluated ({type(exc).__name__})"
            else:
                msg = spec.message or "rule violated"
            if not ok:
                findings.append(
                    {"id": rid, "variable": spec.variable,
                     "value": _display(row[spec.variable], spec.fmt),
                     "type": "rule", "rule": rule.sas, "message": msg}
                )

    errors = pd.DataFrame(findings, columns=["id", "variable", "value", "type", "rule", "message"])
    errors["id"] = errors["id"].astype(str).str.replace(r"\.0$", "", regex=True)

    cleaned = pd.DataFrame(
        [{s.variable: _clean_value(r[s.variable], s.fmt) for s in specs} for r in rows]
    )
    ids = cleaned[id_var].astype("Int64").astype(str) if fmt_of[id_var].kind == "num" else cleaned[id_var]
    counts = errors.groupby("id").size()
    texts = errors.groupby("id")["variable"].apply(lambda v: ", ".join(dict.fromkeys(v)))
    cleaned["_n_errors"] = ids.map(counts).fillna(0).astype(int).values
    cleaned["_error_vars"] = ids.map(texts).fillna("").values
    return Result(cleaned=cleaned, errors=errors.sort_values(["id", "type", "variable"], kind="stable"), rule_issues=issues)


def _clean_value(value: Any, fmt: FieldFormat) -> Any:
    if value == MISSING:
        return pd.NA
    if fmt.kind == "date":
        from .rules import from_sas_date

        return from_sas_date(value)
    if fmt.kind == "num" and isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def write_outputs(result: Result, outdir: str | Path) -> dict[str, Path]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "cleaned": out / "cleaned.csv",
        "report": out / "plausibility_report.xlsx",
    }
    result.cleaned.to_csv(paths["cleaned"], index=False)
    issues = pd.DataFrame([vars(i) for i in result.rule_issues], columns=["variable", "rule", "problem"])
    with pd.ExcelWriter(paths["report"], engine="openpyxl") as xl:
        result.summary.to_excel(xl, sheet_name="summary", index=False)
        result.errors.to_excel(xl, sheet_name="findings", index=False)
        issues.to_excel(xl, sheet_name="rule_problems", index=False)
        for ws in xl.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for col in ws.columns:
                width = max(len(str(c.value or "")) for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(width + 2, 10), 70)
    return paths
