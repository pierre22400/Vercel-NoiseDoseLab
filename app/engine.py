import math
from pathlib import Path

from app.aggregation import aggregate_workers, build_summary
from app.calculations import calculate_segment
from app.csv_reader import read_baseline_csv, read_scenario_csv
from app.errors import UserInputError
from app.scenarios import analyze_scenarios
from app.verdict import evaluate_quality

SCHEMA_VERSION = "noisedoselab_level1_report.v1"


def _public_number(value: float) -> float:
    rounded = round(value, 6)
    return 0.0 if rounded == 0.0 else rounded


def _public_value(value: object) -> object:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise UserInputError("numeric result is out of range")
        return _public_number(value)
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _public_value(item) for key, item in value.items()}
    return value


def analyze(
    csv_path: Path,
    reference_db: float,
    scenario_csv_path: Path | None = None,
    alert_margin_db: float = 3.0,
) -> dict[str, object]:
    try:
        rows, total_rows, invalid_rows = read_baseline_csv(csv_path)
        segments = [
            calculate_segment(row, reference_db, alert_margin_db) for row in rows
        ]
        segments.sort(
            key=lambda item: (str(item["worker"]), str(item["task"]), int(item["row_index"]))
        )
        workers = aggregate_workers(segments, reference_db, alert_margin_db)
        summary = build_summary(segments, workers, reference_db)

        definitions = (
            read_scenario_csv(scenario_csv_path)
            if scenario_csv_path is not None
            else []
        )
        scenarios = analyze_scenarios(
            rows,
            definitions,
            reference_db,
            alert_margin_db,
            summary["max_worker_lex_8h"],
        )
        verdict, reasons = evaluate_quality(
            len(rows), invalid_rows, workers, reference_db, alert_margin_db
        )
    except OverflowError:
        raise UserInputError("numeric input is out of range") from None

    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "ok",
        "input": {
            "csv": csv_path.name,
            "scenario_csv": scenario_csv_path.name if scenario_csv_path else None,
            "reference_db": reference_db,
            "alert_margin_db": alert_margin_db,
        },
        "counts": {
            "total_rows": total_rows,
            "valid_rows": len(rows),
            "invalid_rows": invalid_rows,
            "workers": len(workers),
            "tasks": len({row.task for row in rows}),
            "scenarios": len(scenarios),
        },
        "segments": segments,
        "workers": workers,
        "summary": summary,
        "scenarios": scenarios,
        "verdict": verdict,
        "reasons": reasons,
    }
    return _public_value(payload)
