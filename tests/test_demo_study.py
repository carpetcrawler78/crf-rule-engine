"""End-to-end test on the fictional demo study.

The demo data contain errors that were injected on purpose and listed in
data/demo_fu12_injected_errors.csv. The engine must find exactly those.
"""

from pathlib import Path

import pandas as pd

from crf_rules import compile_rules, generate_sas, load_specs, read_raw, run, write_outputs

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules" / "demo_fu12_rules.xlsx"
RAW = ROOT / "data" / "demo_fu12_raw.csv"
TRUTH = ROOT / "data" / "demo_fu12_injected_errors.csv"


def test_rules_sheet_is_clean():
    _, issues = compile_rules(load_specs(RULES))
    assert issues == []


def test_finds_exactly_the_injected_errors():
    result = run(read_raw(RAW), load_specs(RULES))
    truth = pd.read_csv(TRUTH, dtype=str)
    found = set(zip(result.errors["id"], result.errors["variable"]))
    expected = set(zip(truth["id"], truth["variable"]))
    assert found == expected


def test_cleaned_dataset_flags_records(tmp_path):
    result = run(read_raw(RAW), load_specs(RULES))
    truth = pd.read_csv(TRUTH, dtype=str)
    flagged = set(result.cleaned.loc[result.cleaned["_n_errors"] > 0, "id"].astype(str))
    assert flagged == set(truth["id"])
    paths = write_outputs(result, tmp_path)
    assert pd.read_excel(paths["report"], sheet_name="findings").shape[0] == len(result.errors)


def test_generated_sas_contains_every_rule():
    specs = load_specs(RULES)
    code = generate_sas(specs)
    for s in specs:
        if s.rule:
            assert s.rule.replace("#", s.variable) in code
    assert code.count("%macro crf_clean") == 1 and code.count("%mend crf_clean") == 1


def test_original_german_layout_is_accepted(tmp_path):
    """The original scanner definition files use German column names."""
    df = pd.DataFrame(
        {
            "Datensatzvariable": ["id", "bl_alt"],
            "Variablen-Typ": ['+"0"N(4)', '+"0"N(0-2)'],
            "Regel": ["# > 1000", "# >= 65"],
            "Fehlermeldung": ["ID falsch", "Alter < 65"],
        }
    )
    path = tmp_path / "def.xlsx"
    df.to_excel(path, index=False)
    specs = load_specs(path)
    raw = pd.DataFrame({"id": ["1001", "1002"], "bl_alt": ["70", "50"]})
    result = run(raw, specs)
    assert list(result.errors["message"]) == ["Alter < 65"]
