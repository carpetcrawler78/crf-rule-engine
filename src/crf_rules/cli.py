"""Command line interface.

    crf-rules lint      rules.xlsx                      check the rules sheet only
    crf-rules check     rules.xlsx raw.csv -c log.xlsx -o out/
                                                        apply correction log, run checks,
                                                        write report, audit trail, query files
    crf-rules gen-sas   rules.xlsx -o checks.sas        write the SAS cleaning program
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import compile_rules, load_corrections, load_specs, read_raw, run, write_outputs
from .sas_codegen import generate_sas


def _lint(args: argparse.Namespace) -> int:
    specs = load_specs(args.rules, args.sheet)
    compiled, issues = compile_rules(specs)
    print(f"{len(specs)} fields, {len(compiled)} rules translated, {len(issues)} problems")
    for i in issues:
        print(f"  {i.variable:<24} {i.problem}\n  {'':<24} rule: {i.rule}")
    return 1 if issues else 0


def _check(args: argparse.Namespace) -> int:
    specs = load_specs(args.rules, args.sheet)
    result = run(read_raw(args.raw, sep=args.sep), specs, id_var=args.id,
                 corrections=load_corrections(args.corrections))
    paths = write_outputs(result, args.out)
    print(result.summary.to_string(index=False))
    for name, p in paths.items():
        print(f"{name:>14}: {p}")
    return 0


def _gen_sas(args: argparse.Namespace) -> int:
    specs = load_specs(args.rules, args.sheet)
    code = generate_sas(specs, id_var=args.id, source=Path(args.rules).name)
    if args.out:
        Path(args.out).write_text(code, encoding="utf-8")
        print(f"written: {args.out}")
    else:
        sys.stdout.write(code)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="crf-rules", description="Excel-driven plausibility checks for CRF data")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("rules", help="Excel file with one row per CRF field")
        sp.add_argument("--sheet", default=0, help="sheet name or index (default: first sheet)")
        sp.add_argument("--id", default=None, help="ID variable (default: first field in the sheet)")

    sp = sub.add_parser("lint", help="check the rules sheet for typos and unknown variables")
    common(sp)
    sp.set_defaults(func=_lint)

    sp = sub.add_parser("check", help="run format and rule checks on a raw export")
    common(sp)
    sp.add_argument("raw", help="pipe-delimited raw export")
    sp.add_argument("-c", "--corrections", default=None, help="correction log (.xlsx), optional")
    sp.add_argument("-o", "--out", default="output", help="output folder")
    sp.add_argument("--sep", default="|", help="field separator (default: |)")
    sp.set_defaults(func=_check)

    sp = sub.add_parser("gen-sas", help="generate the SAS cleaning program")
    common(sp)
    sp.add_argument("-o", "--out", default=None, help="target .sas file (default: stdout)")
    sp.set_defaults(func=_gen_sas)

    args = p.parse_args(argv)
    if isinstance(args.sheet, str) and args.sheet.isdigit():
        args.sheet = int(args.sheet)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
