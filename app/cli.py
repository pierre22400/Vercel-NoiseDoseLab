import argparse
import math
import sys
from pathlib import Path

from app.engine import analyze
from app.errors import UserInputError
from app.renderers import render_json, render_text


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UserInputError(message)


def _finite_float(option_name: str):
    def parse(value: str) -> float:
        try:
            number = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{option_name} must be numeric") from None
        if not math.isfinite(number):
            raise argparse.ArgumentTypeError(f"{option_name} must be numeric")
        return number

    return parse


def _build_parser() -> _Parser:
    parser = _Parser(prog="NoiseDoseLab", description="Deterministic noise exposure screening")
    subparsers = parser.add_subparsers(dest="command")
    analyze_parser = subparsers.add_parser("analyze", help="analyze a local exposure CSV")
    analyze_parser.add_argument("--csv", required=True, type=Path)
    analyze_parser.add_argument(
        "--reference-db", required=True, type=_finite_float("reference-db")
    )
    analyze_parser.add_argument("--scenario-csv", type=Path)
    analyze_parser.add_argument("--format", choices=("text", "json"), default="text")
    analyze_parser.add_argument(
        "--alert-margin-db", type=_finite_float("alert-margin-db"), default=3.0
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        parser.print_help()
        return 0

    try:
        args = parser.parse_args(arguments)
        if args.command != "analyze":
            parser.print_help()
            return 0
        payload = analyze(
            csv_path=args.csv,
            reference_db=args.reference_db,
            scenario_csv_path=args.scenario_csv,
            alert_margin_db=args.alert_margin_db,
        )
        renderer = render_json if args.format == "json" else render_text
        print(renderer(payload))
        return 0
    except UserInputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
