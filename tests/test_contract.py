import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app.calculations import calculate_segment
from app.engine import analyze
from app.models import BaselineRow
from app.renderers import render_json, render_text

ROOT = Path(__file__).resolve().parents[1]
BASELINE_HEADER = "worker,task,leq_db,duration_h,protection_db\n"
SCENARIO_HEADER = "scenario,leq_delta_db,duration_factor,protection_delta_db\n"
TOP_LEVEL_KEYS = [
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


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "app.cli", *arguments],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class NoiseDoseLabContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, name: str, content: str) -> Path:
        """Write one UTF-8 fixture and create its explicit parent directory when needed."""
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def baseline(self, rows: str) -> Path:
        return self.write("noise.csv", BASELINE_HEADER + rows)

    def test_help_and_no_arguments_succeed(self) -> None:
        no_arguments = run_cli()
        help_result = run_cli("--help")
        self.assertEqual(no_arguments.returncode, 0)
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("analyze", no_arguments.stdout)
        self.assertIn("NoiseDoseLab", help_result.stdout)

    def test_required_and_invalid_arguments_return_two(self) -> None:
        cases = [
            (("analyze", "--reference-db", "85"), "--csv"),
            (("analyze", "--csv", "noise.csv"), "--reference-db"),
            (("analyze", "--csv", "noise.csv", "--reference-db", "bad"), "reference-db"),
            (("analyze", "--csv", "noise.csv", "--reference-db", "85", "--format", "xml"), "invalid choice"),
            (("analyze", "--csv", "noise.csv", "--reference-db", "85", "--alert-margin-db", "bad"), "alert-margin-db"),
        ]
        for arguments, diagnostic in cases:
            with self.subTest(arguments=arguments):
                result = run_cli(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertIn(diagnostic, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_reference_db_must_be_strictly_positive(self) -> None:
        """Reject zero and negative reference values through the public CLI error path."""
        baseline = self.baseline("alice,press,80,8,0\n")
        for value in ("0", "-85"):
            with self.subTest(value=value):
                result = run_cli(
                    "analyze", "--csv", str(baseline), "--reference-db", value
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("reference-db", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_missing_file_and_column_are_stable_user_errors(self) -> None:
        missing = run_cli(
            "analyze", "--csv", str(self.directory / "missing.csv"), "--reference-db", "85"
        )
        malformed = self.write("bad.csv", "worker,task\na,t\n")
        missing_column = run_cli(
            "analyze", "--csv", str(malformed), "--reference-db", "85"
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("csv", missing.stderr)
        self.assertNotIn(str(self.directory), missing.stderr)
        self.assertEqual(missing_column.returncode, 2)
        self.assertIn("missing required column", missing_column.stderr)

    def test_single_row_energy_calculation_and_numeric_json(self) -> None:
        path = self.baseline("alice,press,80,8,0\n")
        result = run_cli(
            "analyze", "--csv", str(path), "--reference-db", "85", "--format", "json"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        segment = payload["segments"][0]
        self.assertEqual(segment["effective_db"], 80.0)
        self.assertEqual(segment["normalized_8h_energy"], 100000000.0)
        self.assertEqual(segment["segment_lex_8h"], 80.0)
        self.assertEqual(segment["energy_ratio"], 0.316228)
        self.assertIsInstance(segment["energy_ratio"], float)
        self.assertEqual(payload["workers"][0]["lex_8h"], 80.0)
        self.assertEqual(payload["verdict"], "pass")

    def test_input_paths_are_preserved_as_supplied(self) -> None:
        """Keep caller-supplied baseline and scenario paths in the public JSON payload."""
        baseline = self.baseline("alice,press,80,8,0\n")
        scenario = self.write(
            "nested/scenarios.csv", SCENARIO_HEADER + "quiet,-3,1,0\n"
        )
        result = run_cli(
            "analyze",
            "--csv",
            str(baseline),
            "--reference-db",
            "85",
            "--scenario-csv",
            str(scenario),
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["input"]["csv"], str(baseline))
        self.assertEqual(payload["input"]["scenario_csv"], str(scenario))

    def test_invalid_rows_are_ignored_counted_and_warn(self) -> None:
        path = self.baseline(
            "zoe,task-z,70,1,0\n"
            ",missing-worker,70,1,0\n"
            "bob,bad-level,no,1,0\n"
            "amy,task-a,70,25,0\n"
        )
        payload = analyze(path, 85.0)
        self.assertEqual(
            payload["counts"],
            {
                "total_rows": 4,
                "valid_rows": 1,
                "invalid_rows": 3,
                "workers": 1,
                "tasks": 1,
                "scenarios": 0,
            },
        )
        self.assertEqual(payload["verdict"], "warn")
        self.assertEqual(payload["reasons"], ["invalid_rows_ignored"])

    def test_zero_duration_has_null_level_and_positive_zero(self) -> None:
        path = self.baseline("alice,silence,80,0,0\n")
        payload = analyze(path, 85.0)
        segment = payload["segments"][0]
        self.assertIsNone(segment["segment_lex_8h"])
        self.assertEqual(segment["sound_energy"], 0.0)
        self.assertEqual(str(segment["sound_energy"]), "0.0")
        self.assertEqual(segment["status"], "below_alert")

    def test_status_boundaries_are_deterministic(self) -> None:
        rows = [
            BaselineRow(1, "a", "below", 81.999, 8.0, 0.0),
            BaselineRow(2, "a", "alert", 82.0, 8.0, 0.0),
            BaselineRow(3, "a", "reference", 85.0, 8.0, 0.0),
            BaselineRow(4, "a", "above", 85.001, 8.0, 0.0),
        ]
        statuses = [calculate_segment(row, 85.0, 3.0)["status"] for row in rows]
        self.assertEqual(statuses, ["below_alert", "alert", "alert", "above_reference"])

    def test_ordering_is_stable(self) -> None:
        path = self.baseline(
            "zoe,b,70,1,0\n"
            "amy,z,70,1,0\n"
            "amy,a,70,1,0\n"
            "amy,a,71,1,0\n"
        )
        payload = analyze(path, 85.0)
        self.assertEqual(
            [(item["worker"], item["task"], item["row_index"]) for item in payload["segments"]],
            [("amy", "a", 3), ("amy", "a", 4), ("amy", "z", 2), ("zoe", "b", 1)],
        )
        self.assertEqual([item["worker"] for item in payload["workers"]], ["amy", "zoe"])
        self.assertEqual(payload["workers"][0]["tasks"], ["a", "z"])

    def test_fail_reasons_follow_required_order(self) -> None:
        path = self.baseline("alice,loud,100,13,0\nalice,loud-again,100,13,0\n")
        payload = analyze(path, 85.0)
        self.assertEqual(payload["verdict"], "fail")
        self.assertEqual(
            payload["reasons"],
            ["worker_duration_over_24h", "noise_above_reference"],
        )

    def test_no_valid_rows_fails(self) -> None:
        path = self.baseline("alice,bad,not-a-number,1,0\n")
        payload = analyze(path, 85.0)
        self.assertEqual(payload["verdict"], "fail")
        self.assertEqual(payload["reasons"], ["no_valid_rows"])
        self.assertIsNone(payload["summary"]["max_worker_lex_8h"])

    def test_scenarios_use_valid_rows_and_are_sorted(self) -> None:
        path = self.baseline("alice,press,80,8,0\nbob,bad,no,8,0\n")
        scenarios = self.write(
            "scenarios.csv",
            SCENARIO_HEADER + "quiet,-3,1,0\nzero,0,0,0\n",
        )
        payload = analyze(path, 85.0, scenarios)
        self.assertEqual(payload["counts"]["scenarios"], 2)
        self.assertEqual([item["scenario"] for item in payload["scenarios"]], ["quiet", "zero"])
        self.assertEqual(payload["scenarios"][0]["max_worker_lex_8h"], 77.0)
        self.assertEqual(payload["scenarios"][0]["reduction_db_vs_baseline_max"], 3.0)
        self.assertIsNone(payload["scenarios"][1]["max_worker_lex_8h"])
        self.assertIsNone(payload["scenarios"][1]["reduction_db_vs_baseline_max"])

    def test_invalid_scenarios_return_two(self) -> None:
        baseline = self.baseline("alice,press,80,8,0\n")
        scenario_files = [
            self.write("missing-column.csv", "scenario,duration_factor\na,1\n"),
            self.write("invalid-row.csv", SCENARIO_HEADER + "a,0,-1,0\n"),
            self.write("duplicate.csv", SCENARIO_HEADER + "a,0,1,0\na,0,1,0\n"),
        ]
        for scenario in scenario_files:
            with self.subTest(scenario=scenario.name):
                result = run_cli(
                    "analyze",
                    "--csv",
                    str(baseline),
                    "--reference-db",
                    "85",
                    "--scenario-csv",
                    str(scenario),
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("scenario", result.stderr)

    def test_json_structure_rounding_and_text_coherence(self) -> None:
        path = self.baseline("alice,press,81.123456789,1,81.123456789\n")
        payload = analyze(path, 85.0)
        self.assertEqual(list(payload), TOP_LEVEL_KEYS)
        encoded = render_json(payload)
        decoded = json.loads(encoded)
        self.assertEqual(decoded, payload)
        self.assertNotIn("-0.0", encoded)
        text = render_text(payload)
        for fragment in ("NoiseDoseLab", "valid_rows:", "workers:", "reference_db:", "verdict:"):
            self.assertIn(fragment, text)
        self.assertIn(str(payload["verdict"]), text)
        for reason in payload["reasons"]:
            self.assertIn(reason, text)

    def test_imports_have_no_side_effects(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            __import__("app.cli")
            __import__("app.engine")
            __import__("app.renderers")
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
