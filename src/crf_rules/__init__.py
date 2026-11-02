"""Excel-driven plausibility checks for clinical study questionnaires (CRFs)."""

from .engine import (
    FieldSpec,
    Result,
    apply_corrections,
    compile_rules,
    load_corrections,
    load_specs,
    queries_by_site,
    query_workbook,
    read_raw,
    report_workbook,
    run,
    write_outputs,
)
from .formats import FieldFormat, parse_format
from .rules import RuleError, translate
from .sas_codegen import generate_sas

__all__ = [
    "FieldFormat", "FieldSpec", "Result", "RuleError", "apply_corrections", "compile_rules",
    "generate_sas", "load_corrections", "load_specs", "parse_format", "queries_by_site",
    "query_workbook", "read_raw", "report_workbook", "run", "translate", "write_outputs",
]
__version__ = "0.2.0"
