import pytest

from crf_rules.rules import MISSING, RuleError, to_sas_date, translate
import datetime as dt

COLS = ["x", "y", "txt", "d", "m", "j"]


def ok(rule, var="x", **row):
    base = {c: MISSING for c in COLS}
    base["txt"] = ""
    base.update(row)
    return translate(rule, var, COLS).evaluate(base)


def test_range():
    assert ok("# >= 1 and # <= 12", x=5)
    assert not ok("# >= 1 and # <= 12", x=13)


def test_missing_is_smaller_than_any_number_like_in_sas():
    assert not ok("# >= 1", x=MISSING)
    assert ok("# < 1", x=MISSING)
    assert ok("# = .", x=MISSING)


def test_not_in_with_space_separated_list():
    assert ok("# NOT IN (8 88)", x=3)
    assert not ok("# NOT IN (8 88)", x=8)
    assert ok("# NOT IN (8 88)", x=MISSING)


def test_in_list_with_missing():
    assert ok("y in (0 .)", y=MISSING)
    assert not ok("y in (0 .)", y=1)


def test_dependency_rule():
    rule = "(# = 0 and missing(txt)) or # = 1"
    assert ok(rule, x=0, txt="")
    assert not ok(rule, x=0, txt="Asthma")
    assert ok(rule, x=1, txt="Asthma")


def test_sas_not_equal_variants():
    for op in ("~=", "^=", "~ =", "ne"):
        assert ok(f"y {op} .", y=2), op


def test_functions():
    assert ok("# <= year(today())", x=2024)
    assert ok("coalesce(OF x, y) = 3", x=MISSING, y=3)
    sas_date = to_sas_date(dt.date(2025, 3, 10))
    assert ok("# >= mdy(m, d, j)", x=sas_date, m=3, d=10, j=2025)
    assert not ok("# >= mdy(m, d, j)", x=sas_date - 1, m=3, d=10, j=2025)


def test_case_insensitive_names():
    assert ok("# >= Y AND # <= 10", x=5, y=1)


def test_unknown_variable_is_reported():
    with pytest.raises(RuleError, match="unknown variable or function 'fooo'"):
        translate("# > fooo", "x", COLS)


def test_python_code_cannot_be_smuggled_in():
    with pytest.raises(RuleError):
        translate("__import__('os')", "x", COLS)
    with pytest.raises(RuleError):
        translate("# > 1; import os", "x", COLS)


def test_syntax_error_is_reported():
    with pytest.raises(RuleError, match="syntax"):
        translate("# >= and 3", "x", COLS)


def test_sas_text_keeps_rule_and_replaces_hash():
    r = translate("# NOT IN (8 88)", "fu12_health", ["fu12_health"])
    assert r.sas == "fu12_health NOT IN (8 88)"
