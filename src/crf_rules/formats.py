"""Parse scanner/CRF format codes into field types.

Scanner software for paper CRFs (e.g. TeleForm-style exports) describes every
field with a short format code. The codes used here:

    +"0"N(4)      numeric, exactly 4 digits (zero padded)
    +"0"N(0-2)    numeric, 0 to 2 digits
    -" "X(0-50)   text, up to 50 characters
    +" "X(12)     text, 12 characters
    YYMMDD        date, written as YYYYMMDD in the raw export

The parser is deliberately forgiving: an unknown code becomes a text field so
that reading the raw data never fails because of a typo in the rules sheet.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_CODE_RE = re.compile(
    r"""^[+-]?            # optional sign flag (padding direction)
        (?:"(?P<pad>.?)")?  # optional pad character in quotes
        (?P<kind>[NX])      # N = numeric, X = text
        \((?P<lo>\d+)(?:-(?P<hi>\d+))?\)$""",
    re.VERBOSE,
)


@dataclass(frozen=True)
class FieldFormat:
    kind: str  # "num", "char" or "date"
    min_len: int
    max_len: int
    code: str
    known: bool = True

    @property
    def sas_informat(self) -> str:
        if self.kind == "num":
            return "best32."
        if self.kind == "date":
            return "yymmdd8."
        return f"${self.max_len}."

    @property
    def sas_format(self) -> str:
        if self.kind == "num":
            return f"best{max(self.max_len, 1)}."
        if self.kind == "date":
            return "yymmdd10."
        return f"${self.max_len}."


def parse_format(code: str | None) -> FieldFormat:
    """Translate one format code into a :class:`FieldFormat`."""
    raw = (code or "").strip()
    # a space used as pad character must survive whitespace removal
    compact = re.sub(r"\s+", "", raw.replace('" "', '"_"'))
    if compact.upper() == "YYMMDD":
        return FieldFormat("date", 8, 8, raw)

    m = _CODE_RE.match(compact)
    if not m:
        return FieldFormat("char", 0, 200, raw, known=False)

    lo = int(m.group("lo"))
    hi = int(m.group("hi")) if m.group("hi") is not None else lo  # N(4) = fixed width
    kind = "num" if m.group("kind") == "N" else "char"
    return FieldFormat(kind, lo, max(hi, 1), raw)
