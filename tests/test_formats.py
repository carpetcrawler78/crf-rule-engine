import pytest

from crf_rules.formats import parse_format


@pytest.mark.parametrize(
    "code, kind, lo, hi",
    [
        ('+"0"N(4)', "num", 4, 4),
        ('+"0"N(0-2)', "num", 0, 2),
        ('+ "0" N(0-5)', "num", 0, 5),
        ('-" "X(0-50)', "char", 0, 50),
        ('+" "X(12)', "char", 12, 12),
        ("YYMMDD", "date", 8, 8),
    ],
)
def test_known_codes(code, kind, lo, hi):
    f = parse_format(code)
    assert (f.kind, f.min_len, f.max_len, f.known) == (kind, lo, hi, True)


def test_unknown_code_falls_back_to_text():
    f = parse_format("whatever")
    assert f.kind == "char" and not f.known
