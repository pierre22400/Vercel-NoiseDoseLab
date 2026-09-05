from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
BASELINE = b"worker,task,leq_db,duration_h,protection_db\nalice,press,80,8,0\n"
SCENARIOS = b"scenario,leq_delta_db,duration_factor,protection_delta_db\nquiet,-3,1,0\n"


def test_baseline_upload_reaches_engine() -> None:
    response = client.post(
        "/analyze",
        files={"baseline_csv": ("mesures.csv", BASELINE, "text/csv")},
        data={"reference_db": "85", "alert_margin_db": "3"},
    )
    assert response.status_code == 200
    report = response.json()
    assert report["schema_version"] == "noisedoselab_level1_report.v1"
    assert report["workers"][0]["lex_8h"] == 80.0
    assert report["input"]["csv"] == "mesures.csv"
    assert report["input"]["scenario_csv"] is None
    assert "noisedoselab-" not in response.text


def test_optional_scenario_upload_reaches_engine() -> None:
    response = client.post(
        "/analyze",
        files={
            "baseline_csv": ("mesures.csv", BASELINE, "text/csv"),
            "scenario_csv": ("hypotheses.csv", SCENARIOS, "text/csv"),
        },
        data={"reference_db": "85", "alert_margin_db": "3"},
    )
    assert response.status_code == 200
    report = response.json()
    assert report["counts"]["scenarios"] == 1
    assert report["scenarios"][0]["scenario"] == "quiet"
    assert report["input"]["scenario_csv"] == "hypotheses.csv"
    assert "noisedoselab-" not in response.text


def test_transport_validation_is_clear() -> None:
    response = client.post(
        "/analyze",
        files={"baseline_csv": ("mesures.csv", BASELINE, "text/csv")},
        data={"reference_db": "0", "alert_margin_db": "3"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "La valeur de référence doit être strictement positive."}


def test_engine_validation_is_clear_and_does_not_leak_paths() -> None:
    response = client.post(
        "/analyze",
        files={"baseline_csv": ("invalide.csv", b"worker,task\na,b\n", "text/csv")},
        data={"reference_db": "85", "alert_margin_db": "3"},
    )
    assert response.status_code == 422
    assert "missing required column" in response.json()["detail"]
    assert "noisedoselab-" not in response.text
