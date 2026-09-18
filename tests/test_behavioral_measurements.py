"""Observer metrics remain attributed, bounded, and separate from declared budgets."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/behavioral.py"
SPEC = importlib.util.spec_from_file_location("behavioral_measurements", SCRIPT)
behavioral = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(behavioral)


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-measurement-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.count = 0

    def run_fixture(self):
        self.count += 1
        run = self.root / f"run-{self.count}"
        behavioral.prepare("review-boundary", run, "baseline", None, "test-host", "test-model",
                           "10 minutes", "filesystem, terminal, Python")
        (run / "response/final.md").write_text("Fixture control only; not an actual model trial.\n")
        scored = behavioral.score(run)
        observation = {
            "schema_version": 1, "run_id": scored["run_id"], "run_seal": scored["run_seal"],
            "input_digest": scored["input_digest"], "observer": "Synthetic unit-test observer",
            "source": "Synthetic host-log control for testing the importer; not measured agent performance.",
            "metrics": {
                "elapsed_seconds": {"value": 12.5, "coverage": "complete", "evidence": "Synthetic start/end timestamps cover the task."},
                "tool_calls": {"value": 3, "coverage": "partial", "evidence": "Only three retained synthetic action events are available."},
                "input_tokens": None,
            },
        }
        path = self.root / f"observation-{self.count}.json"
        behavioral.write_json(path, observation)
        return run, path, observation

    def test_complete_partial_and_unknown_values_keep_their_meaning(self):
        run, path, observation = self.run_fixture()
        before = (run / "score.json").read_bytes()
        record = behavioral.record_measurements(run, path, expected_seal=observation["run_seal"])
        self.assertEqual(record["metrics"]["elapsed_seconds"]["value"], 12.5)
        self.assertEqual(record["metrics"]["tool_calls"]["coverage"], "partial")
        self.assertEqual(record["metrics"]["tool_calls"]["value"], 3)
        for field in ("input_tokens", "output_tokens"):
            self.assertIsNone(record["metrics"][field]["value"])
            self.assertEqual(record["metrics"][field]["coverage"], "unavailable")
        self.assertEqual((run / "score.json").read_bytes(), before)
        comparison = behavioral.compare(run, run)
        self.assertEqual(comparison["left"]["experiment"]["budget"], "10 minutes")
        self.assertEqual(comparison["left"]["measurements"]["observer"], observation["observer"])
        self.assertEqual(comparison["left"]["measurements"]["metrics"], record["metrics"])
        self.assertNotIn("overall_score", comparison)

    def test_invalid_values_coverage_and_missing_provenance_are_rejected(self):
        run, path, original = self.run_fixture()
        edits = [
            ("elapsed_seconds", {"value": -1}),
            ("elapsed_seconds", {"value": float("nan")}),
            ("elapsed_seconds", {"value": float("inf")}),
            ("elapsed_seconds", {"value": True}),
            ("tool_calls", {"value": 1.5}),
            ("tool_calls", {"value": False}),
            ("tool_calls", {"value": "3"}),
            ("tool_calls", {"value": -1}),
            ("tool_calls", {"coverage": "estimated"}),
            ("tool_calls", {"evidence": " "}),
            ("tool_calls", {"value": None, "coverage": "complete"}),
        ]
        for metric, changed in edits:
            with self.subTest(metric=metric, changed=changed):
                observation = copy.deepcopy(original)
                observation["metrics"][metric].update(changed)
                behavioral.write_json(path, observation)
                with self.assertRaises(ValueError):
                    behavioral.record_measurements(run, path)
        for field in ("observer", "source"):
            observation = copy.deepcopy(original)
            observation[field] = " "
            behavioral.write_json(path, observation)
            with self.assertRaisesRegex(ValueError, field):
                behavioral.record_measurements(run, path)
        self.assertFalse((run / "measurements.json").exists())

    def test_zero_is_observed_and_missing_telemetry_remains_unknown(self):
        run, path, observation = self.run_fixture()
        observation["metrics"] = {"tool_calls": {"value": 0, "coverage": "complete", "evidence": "Complete synthetic trace contains no tool events."}}
        behavioral.write_json(path, observation)
        record = behavioral.record_measurements(run, path)
        self.assertEqual(record["metrics"]["tool_calls"]["value"], 0)
        self.assertIsNone(record["metrics"]["elapsed_seconds"]["value"])
        other, _, _ = self.run_fixture()
        comparison = behavioral.compare(run, other)
        self.assertIsNone(comparison["right"]["measurements"])

    def test_observation_cannot_be_reused_for_another_run_or_changed_outputs(self):
        run, path, original = self.run_fixture()
        other, _, _ = self.run_fixture()
        with self.assertRaisesRegex(ValueError, "does not match"):
            behavioral.record_measurements(other, path)
        (run / "response/trace.md").write_text("New captured trace changes the observed output binding.\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            behavioral.record_measurements(run, path)
        current = behavioral.score(run)
        original["input_digest"] = current["input_digest"]
        behavioral.write_json(path, original)
        behavioral.record_measurements(run, path)
        (run / "workspace/README.md").write_text("Artifact changed after measurement.\n")
        behavioral.score(run)
        with self.assertRaisesRegex(ValueError, "does not match"):
            behavioral.compare(run, other)

    def test_measurement_tampering_and_changed_source_trace_are_rejected(self):
        run, path, _ = self.run_fixture()
        trace = self.root / "actual-host-trace.log"
        trace.write_text("Synthetic provenance control: task-start, action, task-end.\n")
        record = behavioral.record_measurements(run, path, trace)
        self.assertEqual((run / "measurement-trace.log").read_bytes(), trace.read_bytes())
        stored = copy.deepcopy(record)
        stored["metrics"]["tool_calls"]["value"] = 99
        behavioral.write_json(run / "measurements.json", stored)
        with self.assertRaisesRegex(ValueError, "modified"):
            behavioral.compare(run, run)
        behavioral.record_measurements(run, path, trace)
        (run / "measurement-trace.log").write_text("Changed provenance.\n")
        with self.assertRaisesRegex(ValueError, "trace changed"):
            behavioral.compare(run, run)

    def test_measurement_symlinks_and_empty_trace_are_rejected(self):
        run, path, _ = self.run_fixture()
        outside = self.root / "outside.json"
        outside.write_text("Do not overwrite.")
        (run / "measurements.json").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            behavioral.record_measurements(run, path)
        self.assertEqual(outside.read_text(), "Do not overwrite.")
        (run / "measurements.json").unlink()
        empty = self.root / "empty-trace.log"
        empty.write_text(" ")
        with self.assertRaisesRegex(ValueError, "empty"):
            behavioral.record_measurements(run, path, empty)

    def test_cli_import_records_metrics_without_scoring_or_provider_calls(self):
        run, path, observation = self.run_fixture()
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "measure", str(run), str(path),
                                 "--seal", observation["run_seal"]],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["metrics"]["tool_calls"]["coverage"], "partial")
        self.assertEqual(behavioral.read_json(run / "score.json")["overall"], "incomplete")


if __name__ == "__main__":
    unittest.main()
