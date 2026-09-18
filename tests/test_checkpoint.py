import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/fable-mode/scripts/checkpoint.py"
SPEC = importlib.util.spec_from_file_location("fable_checkpoint", SCRIPT)
checkpoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checkpoint)


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-checkpoint-test-")
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        (self.project / "source.py").write_text("original\n")
        (self.project / "report.md").write_text("output\n")
        self.plan = {
            "version": 1, "id": "example", "goal": "Deliver the report",
            "constraints": ["Local files only"], "decisions": [], "blockers": [],
            "steps": [
                {"id": "build", "status": "complete", "inputs": ["source.py"],
                 "outputs": ["report.md"], "checks": [{"description": "fixture output", "outcome": "passed"}]},
                {"id": "review", "status": "complete", "depends_on": ["build"],
                 "inputs": ["report.md"], "checks": [{"description": "review", "outcome": "passed"}]},
            ],
        }

    def test_unchanged_record_can_move_to_another_project_directory(self):
        record = checkpoint.capture(self.project, self.plan)
        with tempfile.TemporaryDirectory() as other:
            copied = Path(other).resolve()
            shutil.copyfile(self.project / "source.py", copied / "source.py")
            shutil.copyfile(self.project / "report.md", copied / "report.md")
            report = checkpoint.inspect(copied, record)
            self.assertEqual(report["completed_steps_to_recheck"], [])
            self.assertTrue(all(step["evidence_state"] == "unchanged" for step in report["steps"]))

    def test_changed_input_invalidates_dependent_steps(self):
        record = checkpoint.capture(self.project, self.plan)
        (self.project / "source.py").write_text("changed\n")
        report = checkpoint.inspect(self.project, record)
        self.assertEqual(report["completed_steps_to_recheck"], ["build", "review"])
        self.assertEqual(report["steps"][0]["changed_files"], ["source.py"])
        self.assertEqual(report["steps"][1]["invalidated_by"], ["build"])

    def test_deleted_output_and_failed_check_require_recheck(self):
        record = checkpoint.capture(self.project, self.plan)
        (self.project / "report.md").unlink()
        self.assertEqual(checkpoint.inspect(self.project, record)["completed_steps_to_recheck"], ["build", "review"])
        self.plan["steps"][0]["checks"][0]["outcome"] = "failed"
        record = checkpoint.capture(self.project, self.plan)
        self.assertIn("fixture output", checkpoint.inspect(self.project, record)["steps"][0]["unresolved_checks"])

    def test_complete_without_evidence_and_incomplete_dependency_do_not_pass(self):
        self.plan["steps"][0].update({"inputs": [], "outputs": [], "checks": []})
        report = checkpoint.inspect(self.project, checkpoint.capture(self.project, self.plan))
        self.assertEqual(report["steps"][0]["evidence_state"], "needs_evidence")
        self.assertEqual(report["steps"][1]["evidence_state"], "stale")
        self.plan["steps"][0]["status"] = "blocked"
        report = checkpoint.inspect(self.project, checkpoint.capture(self.project, self.plan))
        self.assertEqual(report["remaining_steps"], ["build"])
        self.assertEqual(report["steps"][1]["evidence_state"], "stale")

    def test_cycles_missing_ids_and_escaping_paths_are_rejected(self):
        bad = copy.deepcopy(self.plan)
        bad["steps"][0]["depends_on"] = ["review"]
        with self.assertRaisesRegex(ValueError, "cycle"):
            checkpoint.capture(self.project, bad)
        bad["steps"][0]["depends_on"] = ["unknown"]
        with self.assertRaisesRegex(ValueError, "Unknown"):
            checkpoint.capture(self.project, bad)
        for path in ("../outside", "/tmp/outside", "folder\\file"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                checkpoint.local_path(self.project, path)

    def test_symlink_and_modified_manifest_are_rejected(self):
        (self.project / "linked").symlink_to(self.project / "source.py")
        with self.assertRaisesRegex(ValueError, "Symbolic"):
            checkpoint.fingerprint(self.project, "linked")
        record = checkpoint.capture(self.project, self.plan)
        del record["files"]["build"]["source.py"]
        with self.assertRaisesRegex(ValueError, "Tracked file set"):
            checkpoint.inspect(self.project, record)

    def test_cli_capture_inspect_no_execution_and_overwrite_protection(self):
        self.plan["steps"][0]["checks"][0]["argv"] = [sys.executable, "-c", "raise SystemExit('must not run')"]
        (self.project / "plan.json").write_text(json.dumps(self.plan))
        base = [sys.executable, str(SCRIPT), "--project", str(self.project)]
        result = subprocess.run(base + ["capture", "plan.json", "--out", ".fable/checkpoints/task.json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.project / ".fable/checkpoints/task.json"
        before = path.read_bytes()
        result = subprocess.run(base + ["inspect", ".fable/checkpoints/task.json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_bytes(), before)
        again = subprocess.run(base + ["capture", "plan.json", "--out", ".fable/checkpoints/task.json"], capture_output=True, text=True)
        self.assertNotEqual(again.returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        unsafe = subprocess.run(base + ["capture", "plan.json", "--out", "source.py", "--replace"], capture_output=True, text=True)
        self.assertNotEqual(unsafe.returncode, 0)
        self.assertEqual((self.project / "source.py").read_text(), "original\n")
        (self.project / "source.py").write_text("new\n")
        changed = subprocess.run(base + ["inspect", ".fable/checkpoints/task.json"], capture_output=True, text=True)
        self.assertEqual(changed.returncode, 2)

    def test_case_alias_cannot_replace_a_tracked_file_or_plan(self):
        source = self.project / "source.py"
        alias = self.project / "SOURCE.PY"
        if not alias.exists() or not alias.samefile(source):
            self.skipTest("Filesystem is case-sensitive")
        plan_path = self.project / "plan.json"
        plan_path.write_text(json.dumps(self.plan))
        source_before, plan_before = source.read_bytes(), plan_path.read_bytes()
        for output in ("SOURCE.PY", "PLAN.JSON"):
            with self.subTest(output=output):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--project", str(self.project), "capture", "plan.json", "--out", output, "--replace"],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("cannot overwrite", result.stderr)
                self.assertEqual(source.read_bytes(), source_before)
                self.assertEqual(plan_path.read_bytes(), plan_before)


if __name__ == "__main__":
    unittest.main()
