from __future__ import annotations

import math
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.engine import analyze
from app.errors import UserInputError

app = FastAPI(title="NoiseDoseLab", docs_url=None, redoc_url=None)


def _number(value: str, label: str, *, positive: bool = False) -> float:
    try:
        number = float(value)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"{label} doit être un nombre.") from None
    if not math.isfinite(number):
        raise HTTPException(status_code=422, detail=f"{label} doit être un nombre fini.")
    if positive and number <= 0:
        raise HTTPException(status_code=422, detail=f"{label} doit être strictement positive.")
    return number


async def _save_upload(upload: UploadFile, destination: Path) -> None:
    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            output.write(chunk)
    await upload.close()


@app.post("/analyze")
async def analyze_upload(
    baseline_csv: UploadFile = File(...),
    scenario_csv: UploadFile | None = File(default=None),
    reference_db: str = Form(...),
    alert_margin_db: str = Form("3.0"),
) -> dict[str, object]:
    reference = _number(reference_db, "La valeur de référence", positive=True)
    margin = _number(alert_margin_db, "La marge d’alerte")
    baseline_name = Path(baseline_csv.filename or "mesures.csv").name
    scenario_name = Path(scenario_csv.filename or "scenarios.csv").name if scenario_csv else None

    with tempfile.TemporaryDirectory(prefix="noisedoselab-") as directory:
        baseline_path = Path(directory) / "baseline.csv"
        scenario_path = Path(directory) / "scenario.csv" if scenario_csv else None
        await _save_upload(baseline_csv, baseline_path)
        if scenario_csv is not None and scenario_path is not None:
            await _save_upload(scenario_csv, scenario_path)
        try:
            report = analyze(baseline_path, reference, scenario_path, margin)
        except UserInputError as error:
            raise HTTPException(status_code=422, detail=str(error)) from None

    report_input = report["input"]
    assert isinstance(report_input, dict)
    report_input["csv"] = baseline_name
    report_input["scenario_csv"] = scenario_name
    return report
