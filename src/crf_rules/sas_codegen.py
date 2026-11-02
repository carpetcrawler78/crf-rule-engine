"""Generate a self-contained SAS cleaning program from the rules sheet.

This is the core idea of the tool: data managers maintain the plausibility
logic in Excel, and the program writes the SAS code. The generated program

1. reads the pipe-delimited scanner export with every value as text,
2. converts each field according to its format code and records format findings,
3. applies every rule from the sheet and records rule findings,
4. writes a typed dataset with an error count per record plus a findings table.
"""

from __future__ import annotations

import datetime as _dt

from .engine import FieldSpec, compile_rules


def _sq(text: str) -> str:
    """SAS single-quoted literal (no macro resolution inside)."""
    return "'" + text.replace("'", "''") + "'"


def generate_sas(specs: list[FieldSpec], id_var: str | None = None, source: str = "rules.xlsx") -> str:
    id_var = id_var or specs[0].variable
    compiled, issues = compile_rules(specs)
    n = len(specs)
    stamp = _dt.date.today().isoformat()
    L: list[str] = []
    a = L.append

    a(f"/* ---------------------------------------------------------------------")
    a(f"   GENERATED CODE - do not edit by hand. Change {source} and regenerate.")
    a(f"   Generated {stamp} by crf-rule-engine. {n} fields, {len(compiled)} rules.")
    for i in issues:
        a(f"   SKIPPED: {i.variable}: {i.problem}")
    a(f"   ------------------------------------------------------------------ */")
    a("")
    a("%macro crf_clean(raw=, outlib=work, outdir=);")
    a("")
    a("/* 1. Read the export: every field as text, so nothing is lost silently */")
    a("data _crf_raw;")
    a(f'  infile "&raw." dlm="|" dsd truncover firstobs=2 lrecl=32767;')
    a(f"  length _r1-_r{n} $200;")
    a(f"  input _r1-_r{n};")
    a("run;")
    a("")
    a("/* 2. Convert according to the format codes, record format findings */")
    a("data _crf_typed(drop=_r: variable value type rule message)")
    a(f"     _crf_fmt(keep={id_var} variable value type rule message);")
    a("  set _crf_raw;")
    a("  length variable $32 value $200 type $6 rule $500 message $200;")
    a("  _n_fmt = 0;")
    for s in specs:
        if s.fmt.kind == "char":
            a(f"  length {s.variable} ${s.fmt.max_len};")
    for i, s in enumerate(specs, start=1):
        r = f"_r{i}"
        a(f"  /* {s.variable}: {s.fmt.code} */")
        if s.fmt.kind == "num":
            a(f"  {s.variable} = input(strip({r}), ?? best32.);")
            a(f"  if not missing({r}) and missing({s.variable}) then do;")
            a(f'    variable="{s.variable}"; value={r}; type="format"; rule={_sq(s.fmt.code)}; message="not numeric"; _n_fmt + 1; output _crf_fmt;')
            a("  end;")
            a(f"  else if length(scan(strip({r}), 1, '.')) > {s.fmt.max_len} then do;")
            a(f'    variable="{s.variable}"; value={r}; type="format"; rule={_sq(s.fmt.code)}; message="more than {s.fmt.max_len} digits"; _n_fmt + 1; output _crf_fmt;')
            a("  end;")
        elif s.fmt.kind == "date":
            a(f"  {s.variable} = input(strip({r}), ?? yymmdd8.);")
            a(f"  format {s.variable} yymmdd10.;")
            a(f"  if not missing({r}) and missing({s.variable}) then do;")
            a(f'    variable="{s.variable}"; value={r}; type="format"; rule={_sq(s.fmt.code)}; message="not a valid date (YYYYMMDD)"; _n_fmt + 1; output _crf_fmt;')
            a("  end;")
        else:
            a(f"  {s.variable} = strip({r});")
            a(f"  if length(strip({r})) > {s.fmt.max_len} then do;")
            a(f'    variable="{s.variable}"; value={r}; type="format"; rule={_sq(s.fmt.code)}; message="text longer than {s.fmt.max_len} characters"; _n_fmt + 1; output _crf_fmt;')
            a("  end;")
    a("  output _crf_typed;")
    a("run;")
    a("")
    a("/* 3. Plausibility rules from the Excel sheet */")
    a("data &outlib..cleaned(drop=variable value type rule message _n_fmt)")
    a(f"     _crf_rules(keep={id_var} variable value type rule message);")
    a("  set _crf_typed;")
    a("  length variable $32 value $200 type $6 rule $500 message $200;")
    a("  _n_errors = _n_fmt;")
    for s, cr in compiled:
        msg = s.message or "rule violated"
        a(f"  /* {s.variable}: {s.rule} */")
        a(f"  if not ({cr.sas}) then do;")
        a(f'    _n_errors = _n_errors + 1; variable="{s.variable}"; value=strip(vvalue({s.variable})); type="rule";')
        a(f"    rule={_sq(cr.sas)}; message={_sq(msg)}; output _crf_rules;")
        a("  end;")
    a("  output &outlib..cleaned;")
    a("run;")
    a("")
    a("/* 4. Findings table (format + rule) and summary */")
    a("data &outlib..findings;")
    a("  set _crf_fmt _crf_rules;")
    a("run;")
    a(f"proc sort data=&outlib..findings; by {id_var} type variable; run;")
    a("")
    a("proc sql;")
    a("  create table &outlib..summary as")
    a("  select count(*) as records,")
    a("         sum(_n_errors = 0) as records_without_findings,")
    a("         sum(_n_errors > 0) as records_with_findings,")
    a("         calculated records_with_findings / calculated records * 100")
    a("           as pct_with_findings format=5.1")
    a("  from &outlib..cleaned;")
    a("quit;")
    a("")
    a("%if %length(&outdir.) %then %do;")
    a('  ods excel file="&outdir./plausibility_report.xlsx" options(sheet_name="summary" frozen_headers="on");')
    a("  proc print data=&outlib..summary noobs; run;")
    a('  ods excel options(sheet_name="findings" autofilter="all" frozen_headers="on");')
    a("  proc print data=&outlib..findings noobs; run;")
    a("  ods excel close;")
    a('  proc export data=&outlib..cleaned outfile="&outdir./cleaned.csv" dbms=csv replace; run;')
    a("%end;")
    a("")
    a("proc datasets lib=work nolist; delete _crf_:; quit;")
    a("%mend crf_clean;")
    a("")
    return "\n".join(L)
