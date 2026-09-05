import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

"""
Pedagogical banner.
Run an independent, non-blocking black-box triage campaign against the public
NoiseDoseLab CLI.  Each observed case records a boolean result, return code,
stdout and stderr so qualification can distinguish public-contract failures
from internal implementation details without stopping at the first defect.
"""


ROOT = Path(__file__).resolve().parents[1]
BASELINE_HEADER = "worker,task,leq_db,duration_h,protection_db\n"
SCENARIO_HEADER = "scenario,leq_delta_db,duration_factor,protection_delta_db\n"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    """Invoke the public module entry point and capture its observable streams."""
    return subprocess.run(
        [sys.executable, "-m", "app.cli", *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_fixture(directory: Path, name: str, content: str) -> Path:
    """Create one UTF-8 CSV fixture at the explicit path used by a test case."""
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def parse_json(result: subprocess.CompletedProcess[str]) -> dict[str, object] | None:
    """Parse a successful JSON report while preserving a non-blocking triage flow."""
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def record(
    records: list[dict[str, object]],
    name: str,
    passed: bool,
    result: subprocess.CompletedProcess[str],
    observation: str,
) -> None:
    """Append and print one concise, reproducible black-box observation."""
    item = {
        "name": name,
        "passed": passed,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "observation": observation,
    }
    records.append(item)
    print(json.dumps(item, ensure_ascii=False, sort_keys=True))


def expected_lex(level_db: float, duration_h: float, protection_db: float) -> float | None:
    """Calculate one independent segment-level LEX,8h reference value."""
    energy = duration_h * (10.0 ** ((level_db - protection_db) / 10.0)) / 8.0
    return 10.0 * math.log10(energy) if energy > 0.0 else None


def main() -> int:
    """Run the progressive CLI, contract and scientific triage campaign."""
    records: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)
        baseline = write_fixture(
            directory,
            "nested/noise.csv",
            BASELINE_HEADER + "alice,press,80,8,0\n",
        )
        invalid_rows = write_fixture(
            directory,
            "invalid.csv",
            BASELINE_HEADER
            + "zoe,task-z,70,1,0\n"
            + ",missing-worker,70,1,0\n"
            + "bob,bad-level,no,1,0\n"
            + "amy,task-a,70,25,0\n",
        )
        aggregate = write_fixture(
            directory,
            "aggregate.csv",
            BASELINE_HEADER + "alice,press,80,4,0\nalice,press,80,4,0\n",
        )
        zero_duration = write_fixture(
            directory,
            "zero.csv",
            BASELINE_HEADER + "alice,silence,80,0,0\n",
        )
        scenarios = write_fixture(
            directory,
            "scenarios.csv",
            SCENARIO_HEADER + "quiet,-3,1,0\nzero,0,0,0\n",
        )
        malformed_scenario = write_fixture(
            directory,
            "malformed-scenario.csv",
            "scenario,duration_factor\nquiet,1\n",
        )
        duplicate_scenario = write_fixture(
            directory,
            "duplicate-scenario.csv",
            SCENARIO_HEADER + "quiet,0,1,0\nquiet,0,1,0\n",
        )
        no_valid_rows = write_fixture(
            directory,
            "no-valid.csv",
            BASELINE_HEADER + "alice,press,not-a-number,8,0\n",
        )
        over_duration = write_fixture(
            directory,
            "over-duration.csv",
            BASELINE_HEADER + "alice,first,70,13,0\nalice,second,70,13,0\n",
        )
        boundaries = write_fixture(
            directory,
            "boundaries.csv",
            BASELINE_HEADER
            + "below,task,81.999,8,0\n"
            + "alert,task,82,8,0\n"
            + "reference,task,85,8,0\n"
            + "above,task,85.001,8,0\n",
        )
        ordering = write_fixture(
            directory,
            "ordering.csv",
            BASELINE_HEADER
            + "zoe,b,70,1,0\n"
            + "amy,z,70,1,0\n"
            + "amy,a,70,1,0\n"
            + "amy,a,71,1,0\n",
        )

        no_arguments = run_cli()
        record(
            records,
            "CLI_01_no_arguments",
            no_arguments.returncode == 0
            and "analyze" in no_arguments.stdout
            and not no_arguments.stderr,
            no_arguments,
            "No-argument help must succeed without stderr.",
        )
        help_result = run_cli("--help")
        record(
            records,
            "CLI_02_help",
            help_result.returncode == 0
            and "NoiseDoseLab" in help_result.stdout
            and not help_result.stderr,
            help_result,
            "Global help must succeed without stderr.",
        )
        subcommand_help = run_cli("analyze", "--help")
        record(
            records,
            "CLI_03_analyze_help",
            subcommand_help.returncode == 0
            and "--csv" in subcommand_help.stdout
            and "--reference-db" in subcommand_help.stdout,
            subcommand_help,
            "Analyze help must expose the required options.",
        )
        unknown_command = run_cli("unknown")
        record(
            records,
            "CLI_04_unknown_command",
            unknown_command.returncode == 2
            and not unknown_command.stdout
            and bool(unknown_command.stderr),
            unknown_command,
            "Unknown commands must be stable user errors.",
        )
        missing_csv = run_cli("analyze", "--reference-db", "85")
        record(
            records,
            "CLI_05_missing_csv",
            missing_csv.returncode == 2
            and "--csv" in missing_csv.stderr
            and not missing_csv.stdout,
            missing_csv,
            "Missing --csv must return rc 2.",
        )
        missing_reference = run_cli("analyze", "--csv", str(baseline))
        record(
            records,
            "CLI_06_missing_reference",
            missing_reference.returncode == 2
            and "--reference-db" in missing_reference.stderr
            and not missing_reference.stdout,
            missing_reference,
            "Missing --reference-db must return rc 2.",
        )
        nonpositive_reference = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "0"
        )
        record(
            records,
            "CLI_07_zero_reference_rejected",
            nonpositive_reference.returncode == 2
            and "reference-db" in nonpositive_reference.stderr
            and not nonpositive_reference.stdout,
            nonpositive_reference,
            "The reference dB value is contractually strictly positive.",
        )
        negative_reference = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "-85"
        )
        record(
            records,
            "CLI_08_negative_reference_rejected",
            negative_reference.returncode == 2
            and "reference-db" in negative_reference.stderr
            and not negative_reference.stdout,
            negative_reference,
            "Negative reference dB values are contractually invalid.",
        )
        nonfinite_reference = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "nan"
        )
        record(
            records,
            "CLI_09_nonfinite_reference_rejected",
            nonfinite_reference.returncode == 2
            and "reference-db" in nonfinite_reference.stderr,
            nonfinite_reference,
            "Non-finite numeric input must be rejected.",
        )
        missing_file = run_cli(
            "analyze", "--csv", str(directory / "missing.csv"), "--reference-db", "85"
        )
        record(
            records,
            "CLI_10_missing_file",
            missing_file.returncode == 2
            and "csv" in missing_file.stderr.lower()
            and str(directory) not in missing_file.stderr,
            missing_file,
            "Missing files must not leak an absolute path.",
        )
        bad_format = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "85", "--format", "xml"
        )
        record(
            records,
            "CLI_11_invalid_format",
            bad_format.returncode == 2
            and "invalid choice" in bad_format.stderr
            and not bad_format.stdout,
            bad_format,
            "Unsupported output formats must be rejected.",
        )
        nominal = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "85", "--format", "json"
        )
        nominal_payload = parse_json(nominal)
        expected_keys = [
            "schema_version",
            "status",
            "input",
            "counts",
            "segments",
            "workers",
            "summary",
            "scenarios",
            "verdict",
            "reasons",
        ]
        record(
            records,
            "DATA_01_nominal_json_shape",
            nominal.returncode == 0
            and nominal_payload is not None
            and list(nominal_payload) == expected_keys,
            nominal,
            "Nominal JSON must expose the public top-level sections.",
        )
        if nominal_payload is None:
            nominal_payload = {}
        segment = (nominal_payload.get("segments") or [{}])[0]
        worker = (nominal_payload.get("workers") or [{}])[0]
        record(
            records,
            "SCIENCE_01_single_segment_energy",
            isinstance(segment, dict)
            and segment.get("effective_db") == 80.0
            and segment.get("normalized_8h_energy") == 100000000.0
            and segment.get("segment_lex_8h") == 80.0
            and segment.get("energy_ratio") == 0.316228,
            nominal,
            "Independent 80 dB for 8 h reference calculation.",
        )
        record(
            records,
            "CONTRACT_01_input_path_preserved",
            isinstance(nominal_payload.get("input"), dict)
            and nominal_payload["input"].get("csv") == str(baseline),
            nominal,
            "The JSON input csv value must preserve the path supplied by the caller.",
        )
        aggregate_result = run_cli(
            "analyze", "--csv", str(aggregate), "--reference-db", "85", "--format", "json"
        )
        aggregate_payload = parse_json(aggregate_result) or {}
        aggregate_worker = (aggregate_payload.get("workers") or [{}])[0]
        record(
            records,
            "SCIENCE_02_energy_aggregation",
            aggregate_result.returncode == 0
            and isinstance(aggregate_worker, dict)
            and aggregate_worker.get("lex_8h") == 80.0
            and aggregate_worker.get("total_duration_h") == 8.0,
            aggregate_result,
            "Two 80 dB four-hour segments must aggregate to 80 dB LEX,8h.",
        )
        record(
            records,
            "SCIENCE_03_worker_reference",
            isinstance(worker, dict)
            and worker.get("lex_8h") == expected_lex(80.0, 8.0, 0.0),
            nominal,
            "Worker LEX,8h must match an independent logarithmic calculation.",
        )
        invalid_result = run_cli(
            "analyze", "--csv", str(invalid_rows), "--reference-db", "85", "--format", "json"
        )
        invalid_payload = parse_json(invalid_result) or {}
        record(
            records,
            "DATA_02_invalid_rows_counted",
            invalid_result.returncode == 0
            and invalid_payload.get("counts", {}).get("invalid_rows") == 3
            and invalid_payload.get("verdict") == "warn"
            and invalid_payload.get("reasons") == ["invalid_rows_ignored"],
            invalid_result,
            "Invalid baseline rows must be ignored, counted and reflected in the verdict.",
        )
        zero_result = run_cli(
            "analyze", "--csv", str(zero_duration), "--reference-db", "85", "--format", "json"
        )
        zero_payload = parse_json(zero_result) or {}
        zero_segment = (zero_payload.get("segments") or [{}])[0]
        record(
            records,
            "SCIENCE_04_zero_duration",
            isinstance(zero_segment, dict)
            and zero_segment.get("segment_lex_8h") is None
            and zero_segment.get("sound_energy") == 0.0
            and "-0.0" not in zero_result.stdout,
            zero_result,
            "Zero energy must become JSON null for LEX,8h and never render -0.0.",
        )
        no_valid_result = run_cli(
            "analyze", "--csv", str(no_valid_rows), "--reference-db", "85", "--format", "json"
        )
        no_valid_payload = parse_json(no_valid_result) or {}
        record(
            records,
            "VERDICT_01_no_valid_rows_fail",
            no_valid_result.returncode == 0
            and no_valid_payload.get("verdict") == "fail"
            and no_valid_payload.get("reasons") == ["no_valid_rows"]
            and no_valid_payload.get("summary", {}).get("max_worker_lex_8h") is None,
            no_valid_result,
            "A readable file with no valid rows must produce a fail verdict, not a CLI error.",
        )
        over_duration_result = run_cli(
            "analyze", "--csv", str(over_duration), "--reference-db", "85", "--format", "json"
        )
        over_duration_payload = parse_json(over_duration_result) or {}
        record(
            records,
            "VERDICT_02_worker_duration_over_24h",
            over_duration_result.returncode == 0
            and over_duration_payload.get("verdict") == "fail"
            and over_duration_payload.get("reasons") == ["worker_duration_over_24h"],
            over_duration_result,
            "A valid worker total above 24 h must fail at aggregation level.",
        )
        boundary_result = run_cli(
            "analyze", "--csv", str(boundaries), "--reference-db", "85", "--format", "json"
        )
        boundary_payload = parse_json(boundary_result) or {}
        boundary_statuses = {
            item.get("worker"): item.get("status")
            for item in boundary_payload.get("workers", [])
            if isinstance(item, dict)
        }
        record(
            records,
            "SCIENCE_05_status_boundaries",
            boundary_result.returncode == 0
            and boundary_statuses
            == {
                "below": "below_alert",
                "alert": "alert",
                "reference": "alert",
                "above": "above_reference",
            },
            boundary_result,
            "Status boundaries must keep LEX equal to the reference in alert, not above_reference.",
        )
        ordering_result = run_cli(
            "analyze", "--csv", str(ordering), "--reference-db", "85", "--format", "json"
        )
        ordering_payload = parse_json(ordering_result) or {}
        segment_order = [
            (item.get("worker"), item.get("task"), item.get("row_index"))
            for item in ordering_payload.get("segments", [])
            if isinstance(item, dict)
        ]
        record(
            records,
            "CONTRACT_03_record_ordering",
            ordering_result.returncode == 0
            and segment_order
            == [("amy", "a", 3), ("amy", "a", 4), ("amy", "z", 2), ("zoe", "b", 1)],
            ordering_result,
            "Segments must be ordered by worker, task and row index.",
        )
        text_result = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "85", "--format", "text"
        )
        record(
            records,
            "OUTPUT_01_text_surface",
            text_result.returncode == 0
            and not text_result.stderr
            and all(
                fragment in text_result.stdout
                for fragment in ("NoiseDoseLab", "valid_rows:", "workers:", "reference_db:", "verdict:")
            ),
            text_result,
            "Text output must expose the required human-facing fragments.",
        )
        scenario_result = run_cli(
            "analyze",
            "--csv",
            str(baseline),
            "--reference-db",
            "85",
            "--scenario-csv",
            str(scenarios),
            "--format",
            "json",
        )
        scenario_payload = parse_json(scenario_result) or {}
        scenario_items = scenario_payload.get("scenarios") or []
        record(
            records,
            "SCENARIO_01_sorted_and_calculated",
            scenario_result.returncode == 0
            and isinstance(scenario_items, list)
            and [item.get("scenario") for item in scenario_items if isinstance(item, dict)]
            == ["quiet", "zero"]
            and scenario_items[0].get("max_worker_lex_8h") == 77.0
            and scenario_items[0].get("reduction_db_vs_baseline_max") == 3.0,
            scenario_result,
            "Scenario results must be alphabetic and preserve the energy model.",
        )
        invalid_scenario_result = run_cli(
            "analyze",
            "--csv",
            str(baseline),
            "--reference-db",
            "85",
            "--scenario-csv",
            str(malformed_scenario),
        )
        record(
            records,
            "SCENARIO_02_invalid_scenario_error",
            invalid_scenario_result.returncode == 2
            and "scenario" in invalid_scenario_result.stderr.lower()
            and not invalid_scenario_result.stdout,
            invalid_scenario_result,
            "Malformed scenario input must fail through the public error channel.",
        )
        duplicate_scenario_result = run_cli(
            "analyze",
            "--csv",
            str(baseline),
            "--reference-db",
            "85",
            "--scenario-csv",
            str(duplicate_scenario),
        )
        record(
            records,
            "SCENARIO_03_duplicate_name_error",
            duplicate_scenario_result.returncode == 2
            and "scenario" in duplicate_scenario_result.stderr.lower()
            and not duplicate_scenario_result.stdout,
            duplicate_scenario_result,
            "Duplicate scenario identifiers must be rejected at the public boundary.",
        )
        repeated = run_cli(
            "analyze", "--csv", str(baseline), "--reference-db", "85", "--format", "json"
        )
        record(
            records,
            "CONTRACT_02_determinism",
            nominal.returncode == 0 and repeated.returncode == 0 and nominal.stdout == repeated.stdout,
            repeated,
            "Repeated identical invocations must return identical public JSON.",
        )

    passed = sum(item["passed"] is True for item in records)
    print(json.dumps({"summary": {"passed": passed, "total": len(records)}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
