"""Create the fictional demo study: rules sheet + synthetic scanner export.

Everything here is invented. "ACTIVE-65" is a fictional trial of an exercise
programme for adults aged 65+; the 12-month follow-up questionnaire below only
mimics the *structure* of real paper CRFs (date fields split into day/month/
year, yes/no questions with dependent dates, tick boxes where a scanner codes
"several boxes ticked" as 8, free-text fields with dependent flags).

Run:  python scripts/make_demo_data.py
Writes rules/demo_fu12_rules.xlsx, data/demo_fu12_raw.csv and
data/demo_fu12_injected_errors.csv (the ground truth used by the tests).
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
SEED = 65
N_RECORDS = 300

# variable, question, coding, format code, rule (SAS syntax, # = this field), message
FIELDS = [
    ("id", "Participant ID", "4 digits", '+"0"N(4)',
     "# >= 1001 and # <= 1999", "ID outside the assigned range 1001-1999"),
    ("fu12_day", "Q0 Date of completion: day", "1-31", '+"0"N(0-2)',
     "# >= 1 and ((fu12_month in (1,3,5,7,8,10,12) and # <= 31) or (fu12_month in (4,6,9,11) and # <= 30) "
     "or (fu12_month = 2 and # <= 29))", "Day does not exist in this month"),
    ("fu12_month", "Q0 Date of completion: month", "1-12", '+"0"N(0-2)',
     "# >= 1 and # <= 12", "Month missing or not between 1 and 12"),
    ("fu12_year", "Q0 Date of completion: year", "4 digits", '+"0"N(0-4)',
     "# >= 2024 and # <= year(today())", "Year outside the study period"),
    ("fu12_age", "Q1 Age in years", "years", '+"0"N(0-3)',
     "# >= 65 and # <= 110", "Age outside the inclusion range (65+)"),
    ("fu12_health", "Q2 Overall health today", "1=very poor ... 7=excellent", '+"0"N(1)',
     "# in (1 2 3 4 5 6 7)", "Health rating missing, out of range or several boxes ticked (8)"),
    ("fu12_sym_a", "Q3a Tiredness last week", "1=not at all 2=a little 3=moderately 4=very", '+"0"N(1)',
     "# NOT IN (8 88)", "Several boxes ticked"),
    ("fu12_sym_b", "Q3b Pain last week", "1-4", '+"0"N(1)',
     "# NOT IN (8 88)", "Several boxes ticked"),
    ("fu12_sym_c", "Q3c Shortness of breath last week", "1-4", '+"0"N(1)',
     "missing(#) or # in (1,2,3,4)", "Value outside 1-4 or several boxes ticked"),
    ("fu12_sym_d", "Q3d Trouble sleeping last week", "1-4", '+"0"N(1)',
     "missing(#) or # in (1,2,3,4)", "Value outside 1-4 or several boxes ticked"),
    ("fu12_hosp", "Q4 Hospital stay since last visit", "0=no 1=yes", '+"0"N(1)',
     "(# = 0 and fu12_hosp_m = . and fu12_hosp_y = .) or # = 1",
     "Hospital stay missing, or 'no' although a date is given"),
    ("fu12_hosp_m", "Q4a Hospital stay: month", "1-12", '+"0"N(0-2)',
     "missing(#) or (# >= 1 and # <= 12 and fu12_hosp_y ~= .)", "Month invalid or year missing"),
    ("fu12_hosp_y", "Q4b Hospital stay: year", "4 digits", '+"0"N(0-4)',
     "(missing(#) and fu12_hosp in (0 .)) or (fu12_hosp = 1 and # >= 2024 and # <= fu12_year)",
     "Year missing although stay = yes, or later than the questionnaire"),
    ("fu12_fall", "Q5 Fall in the last 12 months", "0=no 1=yes 2=don't know", '+"0"N(1)',
     "# in (0 1 2)", "Fall question missing or several boxes ticked"),
    ("fu12_falls_n", "Q5a Number of falls", "count", '+"0"N(0-2)',
     "(fu12_fall = 1 and # >= 1) or (fu12_fall in (0 2 .) and missing(#))",
     "Number of falls does not match the fall question"),
    ("fu12_newdx", "Q6 New diagnosis since last visit", "0=no 1=yes", '+"0"N(1)',
     "# in (0 1)", "New-diagnosis question missing or several boxes ticked"),
    ("fu12_newdx_txt", "Q6a Which diagnosis", "free text", '-" "X(0-50)',
     "(fu12_newdx = 1 and not missing(#)) or (fu12_newdx in (0 .) and missing(#))",
     "Diagnosis text does not match the yes/no answer"),
    ("fu12_med1", "Q7 Medication 1: name", "free text", '-" "X(0-50)', "", ""),
    ("fu12_med1_daily", "Q7 Medication 1: taken daily", "0=no 1=yes", '+"0"N(1)',
     "# in (0 1 .) and (# ~= 1 or not missing(fu12_med1))", "Daily intake ticked but no medication name"),
    ("fu12_med2", "Q7 Medication 2: name", "free text", '-" "X(0-50)', "", ""),
    ("fu12_med2_daily", "Q7 Medication 2: taken daily", "0=no 1=yes", '+"0"N(1)',
     "# in (0 1 .) and (# ~= 1 or not missing(fu12_med2))", "Daily intake ticked but no medication name"),
    ("fu12_weight", "Q8 Body weight (kg)", "kg", '+"0"N(0-3)',
     "missing(#) or (# >= 35 and # <= 200)", "Implausible body weight"),
    ("fu12_steps", "Q9 Average steps per day", "count", '+"0"N(0-5)',
     "missing(#) or # <= 40000", "Implausible number of daily steps"),
    ("scan_date", "Scanner: date of scan", "", "YYMMDD",
     "not missing(#) and # >= mdy(fu12_month, fu12_day, fu12_year)",
     "Scan date missing or before the date of completion"),
    ("scan_user", "Scanner: operator", "", '-" "X(12)',
     "not missing(#)", "Scanner operator missing"),
]

DIAGNOSES = ["Type 2 diabetes", "Atrial fibrillation", "Osteoporosis", "Cataract", "Hypertension",
             "Hip fracture", "Depression", "COPD"]
MEDS = ["Metformin", "Ramipril", "Bisoprolol", "Atorvastatin", "Levothyroxine", "Pantoprazole",
        "Vitamin D", "Apixaban", "Ibuprofen as needed"]
USERS = ["scan_ab", "scan_cd", "scan_ef"]


def write_rules(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "fu12_rules"
    ws.append(["variable", "question", "coding", "format", "rule", "message"])
    for row in FIELDS:
        ws.append(list(row))
    head = PatternFill("solid", fgColor="DCE6F1")
    for c in ws[1]:
        c.font, c.fill = Font(bold=True), head
    for col, width in zip("ABCDEF", (18, 38, 30, 14, 70, 55)):
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "A2"

    help_ws = wb.create_sheet("how_to")
    lines = [
        "How to write rules",
        "",
        "One row per CRF field. The rule must be TRUE for a plausible value.",
        "Write rules in SAS syntax; '#' stands for the field of that row.",
        "A missing number is written as '.', an empty text as \"\".",
        "",
        "Examples",
        "# >= 1 and # <= 12                      range check",
        "# NOT IN (8 88)                          scanner code 8 = several boxes ticked",
        "(# = 0 and fu12_hosp_y = .) or # = 1     'no' must not come with a date",
        "missing(#) or # in (1,2,3,4)             optional field with allowed values",
        "# <= year(today())                       no dates in the future",
        "",
        "Format codes (column 'format')",
        "+\"0\"N(4)    number, exactly 4 digits",
        "+\"0\"N(0-2)  number, up to 2 digits",
        "-\" \"X(0-50) text, up to 50 characters",
        "YYMMDD      date written as YYYYMMDD",
        "",
        "Check the sheet before use:  crf-rules lint rules/demo_fu12_rules.xlsx",
    ]
    for line in lines:
        help_ws.append([line])
    help_ws.column_dimensions["A"].width = 90
    help_ws["A1"].font = Font(bold=True, size=12)
    help_ws["A7"].font = Font(bold=True)
    help_ws["A14"].font = Font(bold=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def plausible_record(rng: random.Random, pid: int) -> dict[str, str]:
    d = date(2025, 1, 1) + timedelta(days=rng.randint(0, 600))
    r: dict[str, str] = {name: "" for name, *_ in FIELDS}
    r.update(id=f"{pid:04d}", fu12_day=str(d.day), fu12_month=str(d.month), fu12_year=str(d.year),
             fu12_age=str(rng.randint(65, 92)), fu12_health=str(rng.randint(1, 7)))
    for s in "abcd":
        r[f"fu12_sym_{s}"] = str(rng.randint(1, 4)) if rng.random() > 0.05 else ""
    if rng.random() < 0.18:
        hd = d - timedelta(days=rng.randint(20, 330))
        r.update(fu12_hosp="1", fu12_hosp_m=str(hd.month), fu12_hosp_y=str(max(hd.year, 2024)))
    else:
        r["fu12_hosp"] = "0"
    fall = rng.choices([0, 1, 2], weights=[70, 25, 5])[0]
    r["fu12_fall"] = str(fall)
    if fall == 1:
        r["fu12_falls_n"] = str(rng.randint(1, 4))
    if rng.random() < 0.15:
        r.update(fu12_newdx="1", fu12_newdx_txt=rng.choice(DIAGNOSES))
    else:
        r["fu12_newdx"] = "0"
    for k in (1, 2):
        if rng.random() < (0.8 if k == 1 else 0.5):
            r[f"fu12_med{k}"] = rng.choice(MEDS)
            r[f"fu12_med{k}_daily"] = rng.choice(["0", "1", "1"])
    r["fu12_weight"] = str(rng.randint(48, 105)) if rng.random() > 0.08 else ""
    r["fu12_steps"] = str(rng.randint(1200, 11000)) if rng.random() > 0.2 else ""
    r["scan_date"] = (d + timedelta(days=rng.randint(3, 40))).strftime("%Y%m%d")
    r["scan_user"] = rng.choice(USERS)
    return r


# Each injector breaks one record in a way a data manager sees in real CRFs.
def _inj_multi_tick(r, rng):
    v = rng.choice(["fu12_health", "fu12_sym_a", "fu12_sym_b", "fu12_fall"])
    r[v] = "8"
    return [v]


def _inj_bad_day(r, rng):
    r["fu12_month"], r["fu12_day"] = rng.choice([("4", "31"), ("2", "30"), ("11", "31")])
    return ["fu12_day"]


def _inj_age(r, rng):
    r["fu12_age"] = rng.choice(["58", "6", "121"])
    return ["fu12_age"]


def _inj_hosp_no_with_date(r, rng):
    r.update(fu12_hosp="0", fu12_hosp_m="5", fu12_hosp_y="2025")
    return ["fu12_hosp", "fu12_hosp_y"]  # both rules see the contradiction


def _inj_falls_without_fall(r, rng):
    r.update(fu12_fall="0", fu12_falls_n="2")
    return ["fu12_falls_n"]


def _inj_dx_text_without_yes(r, rng):
    r.update(fu12_newdx="0", fu12_newdx_txt=rng.choice(DIAGNOSES))
    return ["fu12_newdx_txt"]


def _inj_daily_without_name(r, rng):
    r.update(fu12_med2="", fu12_med2_daily="1")
    return ["fu12_med2_daily"]


def _inj_weight(r, rng):
    r["fu12_weight"] = rng.choice(["7", "270", "18"])
    return ["fu12_weight"]


def _inj_not_numeric(r, rng):
    v = rng.choice(["fu12_steps", "fu12_weight"])
    r[v] = rng.choice(["ca. 5000", "7O", "n/a"])
    return [v]


def _inj_scan_before_form(r, rng):
    d = date(int(r["fu12_year"]), int(r["fu12_month"]), int(r["fu12_day"]))
    r["scan_date"] = (d - timedelta(days=rng.randint(1, 30))).strftime("%Y%m%d")
    return ["scan_date"]


def _inj_id(r, rng):
    r["id"] = str(int(r["id"]) + 1000)  # outside the assigned range, still unique
    return ["id"]


INJECTORS = [_inj_multi_tick, _inj_bad_day, _inj_age, _inj_hosp_no_with_date, _inj_falls_without_fall,
             _inj_dx_text_without_yes, _inj_daily_without_name, _inj_weight, _inj_not_numeric,
             _inj_scan_before_form, _inj_id]


def main() -> None:
    rng = random.Random(SEED)
    records, truth = [], []
    for pid in range(1001, 1001 + N_RECORDS):
        r = plausible_record(rng, pid)
        if rng.random() < 0.18:
            hits = []
            chosen = rng.sample(INJECTORS, k=rng.choice([1, 1, 2]))
            if _inj_bad_day in chosen and _inj_scan_before_form in chosen:
                chosen.remove(_inj_scan_before_form)  # an impossible date cannot be compared
            for inj in chosen:
                hits += [(var, inj.__name__[5:]) for var in inj(r, rng)]
            # record ground truth with the final ID (the ID itself may be broken)
            truth += [{"id": r["id"], "variable": v, "injected_by": how} for v, how in hits]
        records.append(r)

    names = [f[0] for f in FIELDS]
    raw = ROOT / "data" / "demo_fu12_raw.csv"
    raw.parent.mkdir(parents=True, exist_ok=True)
    with raw.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=names, delimiter="|")
        w.writeheader()
        w.writerows(records)
    with (ROOT / "data" / "demo_fu12_injected_errors.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "variable", "injected_by"])
        w.writeheader()
        w.writerows(truth)
    write_rules(ROOT / "rules" / "demo_fu12_rules.xlsx")
    print(f"{len(records)} records, {len(truth)} injected errors in "
          f"{len({t['id'] for t in truth})} records")


if __name__ == "__main__":
    main()
