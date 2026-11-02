"""Excel-driven plausibility checks for clinical study questionnaires (CRFs)."""

from .engine import FieldSpec, Result, compile_rules, load_specs, read_raw, run, write_outputs
from .formats import FieldFormat, parse_format
from .rules import RuleError, translate
from .sas_codegen import generate_sas

__all__ = [
    "FieldFormat",
    "FieldSpec",
    "Result",
    "RuleError",
    "compile_rules",
    "generate_sas",
    "load_specs",
    "parse_format",
    "read_raw",
    "run",
    "translate",
    "write_outputs",
]
__version__ = "0.1.0"
