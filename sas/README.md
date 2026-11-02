# The SAS program in 2 minutes

`edit_checks_demo_fu12.sas` is generated from the rules sheet. You do not write
it. You set three paths at the top and run it.

```sas
%let raw_file        = C:/study/data/raw_export.csv;                    /* scanner export      */
%let correction_log  = C:/study/corrections/corrections_log.xlsx;       /* who changed what    */
%let output_folder   = C:/study/output;                                 /* results go here     */
```

What it does, in five steps:

| Step | What happens | Result |
|---|---|---|
| 1 | Reads the scanner export. Every field is kept as text (`t_…`), exactly as scanned. The file itself is never changed. | `raw` |
| 2 | Applies the correction log. A row is applied only if the data still holds `old_value`; otherwise it is marked **conflict**. | `raw_corrected`, `audit_trail` |
| 3 | Turns text into numbers and dates. Anything unreadable ("ca. 5000") becomes a *format finding*. | |
| 4 | Runs one `if not (rule)` block per rule from the sheet. A rule describes a **good** value. | `findings` |
| 5 | Saves `cleaned.csv`, `findings.csv`, `audit_trail.csv` and one `queries_<site>.xlsx` per site. | files |

A rule block looks like this, and reads almost like the Excel row it came from:

```sas
  /* fu12_hosp: Q4 Hospital stay since last visit */
  if not ((fu12_hosp = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or fu12_hosp = 1) then do;
    variable="fu12_hosp"; value=vvalue(fu12_hosp); type="rule";
    message='Hospital stay missing, or ''no'' although a date is given';
    link add_finding;
  end;
```

To add a check, add a row to the rules sheet and generate the program again:

```bash
crf-rules lint    rules/demo_fu12_rules.xlsx
crf-rules gen-sas rules/demo_fu12_rules.xlsx -o sas/edit_checks_demo_fu12.sas
```

Requirements: SAS 9.4M3 or later with SAS/ACCESS to PC Files (for `PROC IMPORT … DBMS=XLSX`).
SAS OnDemand for Academics has both. The Python engine in this repo runs the same
checks and is covered by tests. This SAS file is checked for content by the tests,
but it is not executed in CI.
