"""End-to-end tests on the fictional demo study.

The demo data contain errors that were injected on purpose and listed in
data/demo_fu12_injected_errors.csv. About 60 % of them were "answered" by the
sites; those answers are in the correction log. The engine must
* find exactly the injected errors when no corrections are applied,
* find exactly the unanswered ones once the correction log is applied,
* refuse the one correction in the log that does not match the data.
"""

import io
from pathlib import Path

import pandas as pd

from crf_rules import (compile_rules, generate_sas, load_corrections, load_specs, queries_by_site,
                       query_workbook, read_raw, run, write_outputs)

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules" / "demo_fu12_rules.xlsx"
RAW = ROOT / "data" / "demo_fu12_raw.csv"
LOG = ROOT / "corrections" / "demo_fu12_corrections_log.xlsx"
TRUTH = pd.read_csv(ROOT / "data" / "demo_fu12_injected_errors.csv", dtype=str, keep_default_na=False)


def pairs(df):
    return set(zip(df["id"], df["variable"]))


def test_rules_sheet_is_clean():
    _, issues = compile_rules(load_specs(RULES))
    assert issues == []


def test_without_corrections_finds_exactly_the_injected_errors():
    result = run(read_raw(RAW), load_specs(RULES))
    assert pairs(result.findings) == pairs(TRUTH)


def test_correction_log_closes_answered_queries_only():
    result = run(read_raw(RAW), load_specs(RULES), corrections=load_corrections(LOG))
    assert pairs(result.findings) == pairs(TRUTH[TRUTH["answered"] == "no"])
    flagged = set(result.cleaned.loc[result.cleaned["_n_findings"] > 0, "id"].astype(str))
    assert flagged == set(TRUTH.loc[TRUTH["answered"] == "no", "id"])


def test_mismatching_correction_is_a_conflict_and_not_applied():
    raw = read_raw(RAW)
    result = run(raw, load_specs(RULES), corrections=load_corrections(LOG))
    conflicts = result.audit[result.audit["status"] == "conflict"]
    assert len(conflicts) == 1
    c = conflicts.iloc[0]
    assert c["found_value"] != c["old_value"]
    row = result.cleaned[result.cleaned["id"].astype(str) == c["id"]].iloc[0]
    assert str(row[c["variable"]]) == c["found_value"]  # data unchanged
    assert (result.audit["status"] == "applied").sum() == len(result.audit) - 1


def test_raw_data_is_never_modified():
    raw = read_raw(RAW)
    before = raw.copy()
    run(raw, load_specs(RULES), corrections=load_corrections(LOG))
    pd.testing.assert_frame_equal(raw, before)


def test_query_files_per_site(tmp_path):
    result = run(read_raw(RAW), load_specs(RULES))
    tables = queries_by_site(result)
    assert set(tables) <= {"S01", "S02", "S03", "S04"}
    assert sum(len(t) for t in tables.values()) == len(result.findings)
    for site, table in tables.items():
        assert set(table["Site"]) == {site}  # a site only sees its own participants
        wb = pd.read_excel(io.BytesIO(query_workbook(table, site)), sheet_name=None)
        assert list(wb) == ["queries", "how_to_answer"]
        assert "Correct value (want) - filled in by site" in wb["queries"].columns
    paths = write_outputs(result, tmp_path)
    assert len([k for k in paths if k.startswith("queries_")]) == len(tables)
    assert pd.read_excel(paths["report"], sheet_name="findings").shape[0] == len(result.findings)


def test_query_ids_are_stable_between_runs():
    a = run(read_raw(RAW), load_specs(RULES)).findings["query_id"].tolist()
    b = run(read_raw(RAW), load_specs(RULES)).findings["query_id"].tolist()
    assert a == b and len(set(a)) == len(a)


def test_generated_sas_contains_every_rule_and_the_workflow():
    specs = load_specs(RULES)
    code = generate_sas(specs)
    for s in specs:
        if s.rule:
            assert f"if not ({s.rule.replace('#', s.variable)}) then do;" in code
    for step in ("Step 1", "Step 2", "Step 3", "Step 4", "Step 5"):
        assert step in code
    assert "declare hash corr" in code and "%macro query_files" in code


def test_original_german_layout_is_accepted(tmp_path):
    """The original scanner definition files use German column names."""
    df = pd.DataFrame({
        "Datensatzvariable": ["id", "bl_alt"],
        "Variablen-Typ": ['+"0"N(4)', '+"0"N(0-2)'],
        "Regel": ["# > 1000", "# >= 65"],
        "Fehlermeldung": ["ID falsch", "Alter < 65"],
    })
    path = tmp_path / "def.xlsx"
    df.to_excel(path, index=False)
    result = run(pd.DataFrame({"id": ["1001", "1002"], "bl_alt": ["70", "50"]}), load_specs(path))
    assert list(result.findings["message"]) == ["Alter < 65"]
