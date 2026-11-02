"""Translate plausibility rules written in SAS syntax into Python.

Rules live in an Excel sheet, one per CRF field, written as SAS expressions in
which ``#`` stands for the field itself, e.g.::

    # >= 1 and # <= 12
    # NOT IN (8 88)
    (# = 0 AND missing(fu_tx_text)) OR # = 1

The same rule text is used twice: pasted unchanged into generated SAS code,
and translated here so the checks also run without SAS.

Only a safe subset is accepted. Every identifier must be a known CRF variable
or a whitelisted function, so a rules sheet cannot execute arbitrary code.

SAS semantics that matter for plausibility checks are reproduced:
* a numeric missing value (``.``) is smaller than every number,
* arithmetic with a missing value stays missing,
* text missing is the empty string.
"""

from __future__ import annotations

import datetime as _dt
import math
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

MISSING = float("-inf")  # SAS: missing sorts below every number

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<str>"(?:[^"]|"")*"|'(?:[^']|'')*')
  | (?P<num>\d+\.\d*|\d*\.\d+|\d+)
  | (?P<dot>\.)
  | (?P<hash>\#)
  | (?P<ne>[~^¬]\s*=)
  | (?P<op><=|>=|=|<|>|\+|-|\*|/|\(|\)|,)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)

_KEYWORDS = {
    "and": "and",
    "or": "or",
    "not": "not",
    "in": "in",
    "eq": "==",
    "ne": "!=",
    "lt": "<",
    "gt": ">",
    "le": "<=",
    "ge": ">=",
}


class RuleError(ValueError):
    """Raised when a rule cannot be translated (typo, unknown variable, ...)."""


# --------------------------------------------------------------------------
# SAS functions available inside rules
# --------------------------------------------------------------------------
def _is_missing(x: Any) -> bool:
    if x is None:
        return True
    if isinstance(x, float) and (math.isnan(x) or x == MISSING):
        return True
    if isinstance(x, str) and x.strip() == "":
        return True
    return False


def _f_missing(x: Any) -> bool:
    return _is_missing(x)


def _f_coalesce(*args: Any) -> Any:
    for a in args:
        if not _is_missing(a):
            return a
    return MISSING


SAS_EPOCH = _dt.date(1960, 1, 1)


def to_sas_date(d: _dt.date) -> int:
    """Dates are kept as SAS date values (days since 1960-01-01), as in SAS."""
    return (d - SAS_EPOCH).days


def from_sas_date(n: float) -> _dt.date:
    return SAS_EPOCH + _dt.timedelta(days=int(n))


def _f_today() -> int:
    return to_sas_date(_dt.date.today())


def _f_year(d: Any) -> Any:
    return MISSING if _is_missing(d) else from_sas_date(d).year


def _f_month(d: Any) -> Any:
    return MISSING if _is_missing(d) else from_sas_date(d).month


def _f_day(d: Any) -> Any:
    return MISSING if _is_missing(d) else from_sas_date(d).day


def _f_mdy(m: Any, d: Any, y: Any) -> Any:
    if any(_is_missing(v) for v in (m, d, y)):
        return MISSING
    try:
        return to_sas_date(_dt.date(int(y), int(m), int(d)))
    except ValueError:
        return MISSING


def _f_prxmatch(pattern: str, text: Any) -> int:
    if _is_missing(text):
        return 0
    m = re.fullmatch(r"/(.*)/([a-z]*)", pattern)
    regex, flags = (m.group(1), m.group(2)) if m else (pattern, "")
    hit = re.search(regex, str(text), re.IGNORECASE if "i" in flags else 0)
    return hit.start() + 1 if hit else 0


def _f_length(x: Any) -> int:
    return 1 if _is_missing(x) else len(str(x).rstrip())


def _f_upcase(x: Any) -> Any:
    return x.upper() if isinstance(x, str) else x


def _f_lowcase(x: Any) -> Any:
    return x.lower() if isinstance(x, str) else x


def _f_strip(x: Any) -> Any:
    return x.strip() if isinstance(x, str) else x


FUNCTIONS: dict[str, Callable[..., Any]] = {
    "missing": _f_missing,
    "coalesce": _f_coalesce,
    "coalescec": _f_coalesce,
    "today": _f_today,
    "year": _f_year,
    "month": _f_month,
    "day": _f_day,
    "mdy": _f_mdy,
    "prxmatch": _f_prxmatch,
    "length": _f_length,
    "upcase": _f_upcase,
    "lowcase": _f_lowcase,
    "strip": _f_strip,
}


# --------------------------------------------------------------------------
# Translation
# --------------------------------------------------------------------------
@dataclass
class CompiledRule:
    variable: str
    text: str  # original rule as written in Excel
    sas: str  # rule with '#' replaced, ready for a SAS IF statement
    python: str  # translated expression
    code: Any  # compiled code object
    referenced: tuple[str, ...]

    def evaluate(self, row: dict[str, Any]) -> bool:
        env = {"_v": row, "_M": MISSING, **{f"_f_{k}": v for k, v in FUNCTIONS.items()}}
        return bool(eval(self.code, {"__builtins__": {}}, env))  # noqa: S307 - whitelisted tokens only


def _tokenize(rule: str) -> list[tuple[str, str]]:
    pos, out = 0, []
    while pos < len(rule):
        m = _TOKEN_RE.match(rule, pos)
        if not m:
            raise RuleError(f"unexpected character {rule[pos]!r} at position {pos + 1}")
        kind = m.lastgroup or ""
        if kind != "ws":
            out.append((kind, m.group()))
        pos = m.end()
    return out


def _sas_string_to_python(tok: str) -> str:
    quote = tok[0]
    inner = tok[1:-1].replace(quote * 2, quote)
    return repr(inner)


def translate(rule: str, variable: str, columns: Iterable[str]) -> CompiledRule:
    """Translate one SAS rule into a compiled Python expression.

    ``columns`` are the CRF variables that may be referenced.
    Raises :class:`RuleError` with a readable message if the rule is invalid.
    """
    col_lookup = {c.lower(): c for c in columns}
    if variable.lower() not in col_lookup:
        raise RuleError(f"rule belongs to unknown variable '{variable}'")
    tokens = _tokenize(rule)
    if not tokens:
        raise RuleError("rule is empty")

    parts: list[str] = []
    referenced: list[str] = []
    i = 0
    while i < len(tokens):
        kind, text = tokens[i]
        low = text.lower()
        nxt = tokens[i + 1] if i + 1 < len(tokens) else ("", "")

        if kind == "hash":
            parts.append(f'_v["{col_lookup[variable.lower()]}"]')
            referenced.append(col_lookup[variable.lower()])
        elif kind == "dot":
            parts.append("_M")
        elif kind == "num":
            parts.append(text)
        elif kind == "str":
            parts.append(_sas_string_to_python(text))
        elif kind == "ne":
            parts.append("!=")
        elif kind == "op":
            parts.append("==" if text == "=" else text)
        elif kind == "name":
            if low in _KEYWORDS:
                if low == "not" and nxt[1].lower() == "in":
                    parts.append("not in")
                    i += 1
                    low = "in"
                else:
                    parts.append(_KEYWORDS[low])
                if low == "in":
                    i = _translate_in_list(tokens, i + 1, parts)
                    continue
            elif low in FUNCTIONS and nxt[1] == "(":
                parts.append(f"_f_{low}")
                # SAS allows COALESCE(OF a, b) - drop the OF keyword
                if i + 2 < len(tokens) and tokens[i + 2][1].lower() == "of":
                    parts.append("(")
                    i += 3
                    continue
            elif low in col_lookup:
                parts.append(f'_v["{col_lookup[low]}"]')
                referenced.append(col_lookup[low])
            else:
                raise RuleError(f"unknown variable or function '{text}'")
        else:  # pragma: no cover - tokenizer only yields known kinds
            raise RuleError(f"cannot translate '{text}'")
        i += 1

    python = " ".join(parts)
    try:
        code = compile(python, f"<rule {variable}>", "eval")
    except SyntaxError as exc:
        raise RuleError(f"syntax error: {exc.msg}") from None

    sas = re.sub(r"#", variable, rule)
    return CompiledRule(variable, rule, sas, python, code, tuple(dict.fromkeys(referenced)))


def _translate_in_list(tokens: list[tuple[str, str]], i: int, parts: list[str]) -> int:
    """Translate ``IN (8 88)`` / ``IN (1,2,3)`` / ``IN (0 .)`` into a Python tuple."""
    if i >= len(tokens) or tokens[i][1] != "(":
        raise RuleError("IN must be followed by a list in parentheses")
    i += 1
    items: list[str] = []
    while i < len(tokens) and tokens[i][1] != ")":
        kind, text = tokens[i]
        if kind == "num":
            items.append(text)
        elif kind == "dot":
            items.append("_M")
        elif kind == "str":
            items.append(_sas_string_to_python(text))
        elif text == "-" and i + 1 < len(tokens) and tokens[i + 1][0] == "num":
            items.append("-" + tokens[i + 1][1])
            i += 1
        elif text != ",":
            raise RuleError(f"unexpected '{text}' inside IN list")
        i += 1
    if i >= len(tokens):
        raise RuleError("IN list is not closed with ')'")
    parts.append("(" + ", ".join(items) + ",)")
    return i + 1
