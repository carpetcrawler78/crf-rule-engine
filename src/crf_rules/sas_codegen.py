"""Write the edit-check program in plain SAS.

The program is generated from the rules sheet and is meant to be READ by
people who are not SAS experts: one short block per rule, plain comments,
three paths to set at the top, no macros except one small loop at the end.
"""

from __future__ import annotations

import datetime as _dt
import textwrap

from .engine import FieldSpec, compile_rules


def _sq(text: str) -> str:
    """SAS text in single quotes (nothing inside is resolved)."""
    return "'" + text.replace("'", "''") + "'"


def _wrap(words: list[str], indent: str = "    ") -> str:
    return textwrap.fill(" ".join(words), width=88, initial_indent=indent, subsequent_indent=indent)


def generate_sas(specs: list[FieldSpec], id_var: str | None = None, site_var: str | None = "site",
                 source: str = "rules.xlsx") -> str:
    id_var = id_var or specs[0].variable
    names = [s.variable for s in specs]
    site = next((n for n in names if site_var and n.lower() == site_var.lower()), None)
    compiled, issues = compile_rules(specs)
    first, last = f"t_{names[0]}", f"t_{names[-1]}"
    out: list[str] = []
    a = out.append

    a("/* ============================================================================")
    a(f"   EDIT-CHECK PROGRAM  -  generated from {source} on {_dt.date.today().isoformat()}")
    a("   Do not edit by hand: change the rules sheet and generate the program again.")
    a("")
    a("   Step 1  read the raw scanner export (every field as text, file is never changed)")
    a("   Step 2  apply the correction log  -> audit trail (applied / conflict)")
    a("   Step 3  convert text to numbers and dates  -> format findings")
    a(f"   Step 4  check the {len(compiled)} plausibility rules  -> rule findings")
    a("   Step 5  save: cleaned data, findings, audit trail, one query file per site")
    for i in issues:
        a(f"   NOTE: rule for {i.variable} skipped - {i.problem}")
    a("   ============================================================================ */")
    a("")
    a("/* ---- set these three paths, then run the whole program ---------------------- */")
    a("%let raw_file        = C:/study/data/raw_export.csv;")
    a("%let correction_log  = C:/study/corrections/corrections_log.xlsx;")
    a("%let output_folder   = C:/study/output;")
    a("")

    # ---------------------------------------------------------------- step 1
    a("/* ---- Step 1: read the raw export. t_ = text exactly as scanned ------------- */")
    a("data raw;")
    a('  infile "&raw_file." dlm="|" dsd truncover firstobs=2 lrecl=32767;')
    a(_wrap(["length"] + [f"t_{n}" for n in names] + ["$200;"], "  "))
    a(_wrap(["input"] + [f"t_{n}" for n in names] + [";"], "  "))
    a("run;")
    a("")

    # ---------------------------------------------------------------- step 2
    a("/* ---- Step 2: apply the correction log ----------------------------------------")
    a("   Every change to the data is a row in the correction log (who, what, when, why).")
    a("   A change is applied only if the value in the data still equals old_value;")
    a("   otherwise it is marked as conflict and nothing is changed.                      */")
    a('proc import datafile="&correction_log." out=log_import dbms=xlsx replace;')
    a("  getnames=yes;")
    a("run;")
    a("")
    a("data corrections;   /* make every column text, whatever Excel stored */")
    a("  set log_import(rename=(id=_id old_value=_old new_value=_new));")
    a("  length id old_value new_value $200;")
    a("  id = cats(_id);  old_value = cats(_old);  new_value = cats(_new);")
    a('  if old_value = "." then old_value = "";')
    a('  if new_value = "." then new_value = "";')
    a("  variable = lowcase(strip(variable));")
    a("  drop _id _old _new;")
    a("run;")
    a("")
    a("data raw_corrected(drop=id correction_id variable old_value new_value found_value status rc i)")
    a("     audit_trail(keep=correction_id id variable old_value new_value found_value status);")
    a("  set raw;")
    a(f"  array field {{*}} $ {first}--{last};   /* all fields of the export */")
    a("  length correction_id $20 variable $32 old_value new_value found_value $200 status $10 id $200;")
    a("  if _n_ = 1 then do;   /* load the log into memory, looked up by participant ID */")
    a('    declare hash corr(dataset: "corrections", multidata: "yes");')
    a('    corr.defineKey("id");')
    a('    corr.defineData("correction_id", "variable", "old_value", "new_value");')
    a("    corr.defineDone();")
    a("  end;")
    a(f"  id = strip(t_{id_var});")
    a("  rc = corr.find();")
    a("  do while (rc = 0);   /* every correction for this participant */")
    a("    do i = 1 to dim(field);")
    a('      if lowcase(vname(field{i})) = cats("t_", variable) then do;')
    a("        found_value = field{i};")
    a('        if strip(found_value) = strip(old_value) then do; field{i} = new_value; status = "applied"; end;')
    a('        else status = "conflict";')
    a("        output audit_trail;")
    a("      end;")
    a("    end;")
    a("    rc = corr.find_next();")
    a("  end;")
    a("  output raw_corrected;")
    a("run;")
    a("")

    # ---------------------------------------------------------------- step 3+4
    a("/* ---- Steps 3 and 4: convert and check -------------------------------------- */")
    keep_find = ["query_id"] + ([site] if site else []) + [id_var, "variable", "value", "type", "message", "rule"]
    a("data checked(drop=t_: query_id variable value type message rule)")
    a(f"     findings(keep={' '.join(keep_find)});")
    a("  set raw_corrected;")
    a("  length query_id $60 variable $32 value $200 type $6 message $200 rule $500;")
    a("  n_findings = 0;")
    a("")
    a("  /* Step 3: text -> number / date. Anything that cannot be read is a finding. */")
    for s in specs:
        t = f"t_{s.variable}"
        if s.fmt.kind == "num":
            a(f"  {s.variable} = input({t}, ?? best32.);")
            a(f'  if {t} ne "" and {s.variable} = . then do; variable="{s.variable}"; value={t}; '
              f'type="format"; message="not a number"; rule={_sq(s.fmt.code)}; link add_finding; end;')
        elif s.fmt.kind == "date":
            a(f"  {s.variable} = input({t}, ?? yymmdd8.);  format {s.variable} yymmdd10.;")
            a(f'  if {t} ne "" and {s.variable} = . then do; variable="{s.variable}"; value={t}; '
              f'type="format"; message="not a valid date (YYYYMMDD)"; rule={_sq(s.fmt.code)}; link add_finding; end;')
        else:
            a(f"  length {s.variable} ${s.fmt.max_len};  {s.variable} = strip({t});")
            a(f'  if length(strip({t})) > {s.fmt.max_len} then do; variable="{s.variable}"; value={t}; '
              f'type="format"; message="text longer than {s.fmt.max_len} characters"; rule={_sq(s.fmt.code)}; '
              f"link add_finding; end;")
    a("")
    a("  /* Step 4: plausibility rules from the rules sheet. A rule describes a GOOD value. */")
    for s, cr in compiled:
        a("")
        a(f"  /* {s.variable}: {s.label} */" if s.label else f"  /* {s.variable} */")
        a(f"  if not ({cr.sas}) then do;")
        a(f'    variable="{s.variable}"; value=vvalue({s.variable}); type="rule";')
        a(f"    message={_sq(s.message or 'rule violated')};")
        a(f"    rule={_sq(cr.sas)};")
        a("    link add_finding;")
        a("  end;")
    a("")
    a("  output checked;")
    a("  return;")
    a("")
    a("add_finding:   /* one finding = one query to the site */")
    a(f'  query_id = cats("Q-", {id_var}, "-", variable);')
    a("  n_findings = n_findings + 1;")
    a("  output findings;")
    a("  return;")
    a("run;")
    a("")

    # ---------------------------------------------------------------- step 5
    a("/* ---- Step 5: save results ----------------------------------------------------- */")
    a(f"proc sort data=findings; by {site + ' ' if site else ''}{id_var} variable; run;")
    a("")
    a('proc export data=checked     outfile="&output_folder./cleaned.csv"     dbms=csv replace; run;')
    a('proc export data=findings    outfile="&output_folder./findings.csv"    dbms=csv replace; run;')
    a('proc export data=audit_trail outfile="&output_folder./audit_trail.csv" dbms=csv replace; run;')
    a("")
    a("title 'Summary';")
    a("proc sql;")
    a("  select count(*)              as records,")
    a("         sum(n_findings = 0)   as records_without_findings,")
    a("         sum(n_findings > 0)   as records_with_findings")
    a("  from checked;")
    a("  select status, count(*) as corrections from audit_trail group by status;")
    a("quit;")
    a("title;")
    if site:
        a("")
        a("/* One Excel file per site with its queries. Sites fill in the yellow columns. */")
        a("data queries;")
        a("  set findings;")
        a("  length correct_value site_comment answered_by $100;")
        a("  call missing(correct_value, site_comment, answered_by);")
        a("run;")
        a("")
        a("%macro query_files;")
        a(f"  proc sql noprint; select distinct {site} into :site_list separated by ' ' from queries; quit;")
        a("  %do i = 1 %to %sysfunc(countw(&site_list.));")
        a("    %let s = %scan(&site_list., &i.);")
        a('    ods excel file="&output_folder./queries_&s..xlsx"')
        a('              options(sheet_name="queries" autofilter="all" frozen_headers="on");')
        a(f'    proc print data=queries noobs label; where {site} = "&s.";')
        a(f"      var query_id {id_var} variable value message;")
        a('      var correct_value site_comment answered_by / style(data)=[background=lightyellow];')
        a(f"      label query_id='Query ID' {id_var}='Participant ID' variable='Field' value='Current value (have)'")
        a("            message='Problem (why)' correct_value='Correct value (want)' site_comment='Comment / source'")
        a("            answered_by='Answered by / date';")
        a("    run;")
        a("    ods excel close;")
        a("  %end;")
        a("%mend query_files;")
        a("%query_files")
    a("")
    return "\n".join(out)
