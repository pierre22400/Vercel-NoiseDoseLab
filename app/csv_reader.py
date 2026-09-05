import csv
import math
from pathlib import Path

from app.errors import UserInputError
from app.models import BaselineRow, ScenarioDefinition

BASELINE_COLUMNS = ("worker", "task", "leq_db", "duration_h", "protection_db")
SCENARIO_COLUMNS = (
    "scenario",
    "leq_delta_db",
    "duration_factor",
    "protection_delta_db",
)


def _open_csv(path: Path, kind: str):
    if not path.exists() or not path.is_file():
        raise UserInputError(f"{kind} csv file not found")
    try:
        return path.open("r", encoding="utf-8-sig", newline="")
    except (OSError, UnicodeError):
        raise UserInputError(f"{kind} csv file is not readable") from None


def _reader(path: Path, required_columns: tuple[str, ...], kind: str):
    stream = _open_csv(path, kind)
    try:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        for column in required_columns:
            if column not in headers:
                stream.close()
                raise UserInputError(f"{kind} missing required column: {column}")
        return stream, reader
    except (csv.Error, UnicodeError):
        stream.close()
        raise UserInputError(f"invalid {kind} csv") from None


def _finite_number(value: object) -> float:
    if value is None or str(value).strip() == "":
        raise ValueError
    number = float(str(value).strip())
    if not math.isfinite(number):
        raise ValueError
    return number


def _parse_baseline_row(raw: dict[str, str], row_index: int) -> BaselineRow:
    worker = (raw.get("worker") or "").strip()
    task = (raw.get("task") or "").strip()
    if not worker or not task:
        raise ValueError

    leq_db = _finite_number(raw.get("leq_db"))
    duration_h = _finite_number(raw.get("duration_h"))
    protection_db = _finite_number(raw.get("protection_db"))
    if leq_db < 0.0 or not 0.0 <= duration_h <= 24.0 or protection_db < 0.0:
        raise ValueError

    return BaselineRow(
        row_index=row_index,
        worker=worker,
        task=task,
        leq_db=leq_db,
        duration_h=duration_h,
        protection_db=protection_db,
    )


def read_baseline_csv(path: Path) -> tuple[list[BaselineRow], int, int]:
    stream, reader = _reader(path, BASELINE_COLUMNS, "baseline")
    rows: list[BaselineRow] = []
    total_rows = 0
    try:
        for row_index, raw in enumerate(reader, start=1):
            total_rows += 1
            try:
                rows.append(_parse_baseline_row(raw, row_index))
            except (TypeError, ValueError):
                continue
    except (csv.Error, UnicodeError):
        raise UserInputError("invalid baseline csv") from None
    finally:
        stream.close()
    return rows, total_rows, total_rows - len(rows)


def _parse_scenario_row(raw: dict[str, str]) -> ScenarioDefinition:
    name = (raw.get("scenario") or "").strip()
    if not name:
        raise ValueError
    leq_delta_db = _finite_number(raw.get("leq_delta_db"))
    duration_factor = _finite_number(raw.get("duration_factor"))
    protection_delta_db = _finite_number(raw.get("protection_delta_db"))
    if duration_factor < 0.0:
        raise ValueError
    return ScenarioDefinition(
        scenario=name,
        leq_delta_db=leq_delta_db,
        duration_factor=duration_factor,
        protection_delta_db=protection_delta_db,
    )


def read_scenario_csv(path: Path) -> list[ScenarioDefinition]:
    stream, reader = _reader(path, SCENARIO_COLUMNS, "scenario")
    definitions: list[ScenarioDefinition] = []
    names: set[str] = set()
    try:
        for raw in reader:
            try:
                definition = _parse_scenario_row(raw)
            except (TypeError, ValueError):
                raise UserInputError("invalid scenario row") from None
            if definition.scenario in names:
                raise UserInputError("duplicate scenario name")
            names.add(definition.scenario)
            definitions.append(definition)
    except (csv.Error, UnicodeError):
        raise UserInputError("invalid scenario csv") from None
    finally:
        stream.close()
    return sorted(definitions, key=lambda item: item.scenario)
