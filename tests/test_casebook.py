"""Exercise replay semantics and freshness against isolated project fixtures."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/fable-mode/scripts/casebook.py"


class CasebookTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-casebook-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "project"
        self.root.mkdir()
        (self.root / "docs/knowledge").mkdir(parents=True)
        (self.root / "input.txt").write_text("good")
        (self.root / "probe.py").write_text(
            "from pathlib import Path\n"
            "print('PRIVATE_DIAGNOSTIC_SHOULD_NOT_BE_STORED')\n"
            "Path('ran.txt').write_text('yes')\n"
            "raise SystemExit(0 if Path('input.txt').read_text() == 'good' else 1)\n"
        )
        self.case = {
            "id": "example-check", "title": "Example invariant",
            "lesson": "A known good input satisfies the check.",
            "invariant": "The configured input is good.",
            "applicability": {"when": "Changing fixture input behavior.", "paths": ["input.txt"]},
            "tags": ["regression", "example"],
            "sources": [{"path": "probe.py", "note": "The executable regression."}],
            "dependencies": {"paths": ["input.txt", "probe.py"], "executables": []},
            "check": {"argv": ["{python}", "probe.py"], "cwd": ".", "timeout_seconds": 5},
        }
        self.definitions = self.root / "docs/knowledge/cases.json"
        self.save()

    def save(self):
        self.definitions.write_text(json.dumps({"version": 1, "cases": [self.case]}))

    def cli(self, *args, code=0, options=()):
        result = subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.root),
                                 *options, *args], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout if result.stdout else result.stderr)

    def test_retrieval_and_preview_never_run_or_write(self):
        self.assertEqual(len(self.cli("list")), 1)
        self.assertEqual(len(self.cli("search", "example regression")), 1)
        self.assertEqual(self.cli("search", "absent"), [])
        preview = self.cli("show", self.case["id"])
        self.assertEqual(preview["preview"]["argv"], [sys.executable, "probe.py"])
        self.assertEqual(preview["case"], self.case)
        self.assertEqual(self.cli("status")[0]["state"], "unrecorded")
        self.assertFalse((self.root / "ran.txt").exists())
        self.assertFalse((self.root / ".fable").exists())

    def test_pass_failure_and_stale_dependency_are_distinct(self):
        passed = self.cli("replay", self.case["id"])
        self.assertEqual(passed["outcome"], "check_passed")
        self.assertEqual(passed["returncode"], 0)
        self.assertEqual(self.cli("status")[0]["state"], "current")
        (self.root / "input.txt").write_text("bad")
        self.assertEqual(self.cli("status")[0]["state"], "stale")
        failed = self.cli("replay", self.case["id"], code=1)
        self.assertEqual(failed["outcome"], "check_failed")
        self.assertEqual(failed["returncode"], 1)
        self.assertNotIn("reproduced", failed["summary"])
        self.assertNotEqual(failed["record_path"], passed["record_path"])
        self.assertTrue(Path(passed["record_path"]).is_file())
        current = self.cli("status")[0]
        self.assertEqual(current["state"], "current")
        self.assertEqual(current["latest_outcome"], "check_failed")

    def test_case_ids_with_shared_delimiter_prefix_have_independent_records(self):
        first = dict(self.case, id="a")
        second = dict(self.case, id="a--b")
        self.definitions.write_text(json.dumps({"version": 1, "cases": [first, second]}))
        first_record = self.cli("replay", "a")
        second_record = self.cli("replay", "a--b")
        states = {item["case_id"]: item for item in self.cli("status")}
        self.assertEqual(states["a"]["record_path"], first_record["record_path"])
        self.assertEqual(states["a--b"]["record_path"], second_record["record_path"])
        for case_id in ("a", "a--b"):
            self.assertEqual(states[case_id]["state"], "current")
            self.assertEqual(self.cli("status", case_id)[0]["latest_outcome"], "check_passed")
        newest_first = self.cli("replay", "a")
        self.assertEqual(self.cli("status", "a")[0]["record_path"], newest_first["record_path"])
        self.assertEqual(self.cli("status", "a--b")[0]["record_path"], second_record["record_path"])

    def test_evidence_contains_fingerprints_and_no_output(self):
        result = self.cli("replay", self.case["id"])
        saved = Path(result["record_path"]).read_text()
        self.assertNotIn("PRIVATE_DIAGNOSTIC", saved)
        self.assertEqual(len(result["definition_sha256"]), 64)
        self.assertEqual(len(result["file_hashes"]["input.txt"]), 64)
        self.assertIn("recorded_at", result)
        self.assertEqual(result["argv"], [sys.executable, "probe.py"])

    def test_definition_change_makes_evidence_stale(self):
        self.cli("replay", self.case["id"])
        self.case["lesson"] = "A revised interpretation needs another replay."
        self.save()
        state = self.cli("status")[0]
        self.assertEqual(state["state"], "stale")
        self.assertIn("definition_sha256 changed", state["reasons"])

    def test_source_change_makes_evidence_stale(self):
        self.cli("replay", self.case["id"])
        (self.root / "probe.py").write_text("raise SystemExit(0)\n")
        self.assertEqual(self.cli("status")[0]["state"], "stale")

    def test_directory_membership_is_fingerprinted(self):
        (self.root / "component").mkdir()
        self.case["dependencies"]["paths"].append("component")
        self.save()
        self.cli("replay", self.case["id"])
        (self.root / "component/new.py").write_text("x = 1\n")
        self.assertEqual(self.cli("status")[0]["state"], "stale")

    def test_missing_file_and_executable_do_not_execute(self):
        self.case["dependencies"]["paths"].append("missing.txt")
        self.case["dependencies"]["executables"].append("fable-nonexistent-89fad0")
        self.save()
        result = self.cli("replay", self.case["id"], code=3)
        self.assertEqual(result["outcome"], "not_applicable")
        self.assertIsNone(result["returncode"])
        self.assertIn("path: missing.txt", result["missing"])
        self.assertFalse((self.root / "ran.txt").exists())
        self.assertEqual(self.cli("status")[0]["state"], "not_applicable")

    def test_lexical_path_escapes_are_rejected_before_execution(self):
        for value in ("../input.txt", str(self.root / "input.txt"), "C:\\input.txt"):
            with self.subTest(value=value):
                self.case["dependencies"]["paths"] = [value]
                self.save()
                self.assertIn("error", self.cli("replay", self.case["id"], code=2))
        self.assertFalse((self.root / "ran.txt").exists())

    def test_working_directory_and_runtime_escapes_are_rejected(self):
        self.case["check"]["cwd"] = ".."
        self.save()
        self.cli("replay", self.case["id"], code=2)
        self.case["check"]["cwd"] = "."
        self.save()
        self.cli("replay", self.case["id"], code=2, options=("--results-dir", "../records"))
        self.assertFalse((self.root / "ran.txt").exists())

    def test_symlink_dependency_is_rejected(self):
        (self.root / "linked.txt").symlink_to(self.root / "input.txt")
        self.case["dependencies"]["paths"].append("linked.txt")
        self.save()
        self.cli("replay", self.case["id"], code=2)
        self.assertFalse((self.root / "ran.txt").exists())

    def test_timeout_is_inconclusive(self):
        (self.root / "probe.py").write_text("import time\ntime.sleep(5)\n")
        self.case["check"]["timeout_seconds"] = 0.05
        self.save()
        result = self.cli("replay", self.case["id"], code=3)
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertIn("timeout", result["summary"])
        self.assertLess(result["duration_seconds"], 2)

    def test_changed_input_during_probe_invalidates_success(self):
        (self.root / "probe.py").write_text("from pathlib import Path\nPath('input.txt').write_text('changed')\n")
        result = self.cli("replay", self.case["id"], code=3)
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["outcome"], "inconclusive")
        self.assertIn("changed during", result["summary"])

    def test_changed_then_restored_input_invalidates_success(self):
        (self.root / "probe.py").write_text(
            "from pathlib import Path\nimport time\n"
            "p = Path('input.txt')\nbefore = p.read_text()\n"
            "p.write_text('changed')\ntime.sleep(0.01)\np.write_text(before)\n"
        )
        result = self.cli("replay", self.case["id"], code=3)
        self.assertEqual(result["outcome"], "inconclusive")

    def test_definition_changed_during_probe_invalidates_success(self):
        (self.root / "probe.py").write_text(
            "from pathlib import Path\nimport json\n"
            "p = Path('docs/knowledge/cases.json')\ndata = json.loads(p.read_text())\n"
            "data['cases'][0]['lesson'] = 'changed by another writer'\np.write_text(json.dumps(data))\n"
        )
        result = self.cli("replay", self.case["id"], code=3)
        self.assertEqual(result["outcome"], "inconclusive")

    def test_argv_is_literal_without_shell_expansion(self):
        literal = "$(touch forbidden.txt); *"
        self.case["check"]["argv"] = ["{python}", "-c", "import sys; assert sys.argv[1] == " + repr(literal), literal]
        self.save()
        self.cli("replay", self.case["id"])
        self.assertFalse((self.root / "forbidden.txt").exists())

    def test_invalid_timeout_and_unknown_case_are_errors(self):
        self.cli("replay", "not-present", code=2)
        self.case["check"]["timeout_seconds"] = 0
        self.save()
        self.cli("replay", self.case["id"], code=2)

    def test_custom_runtime_directory_is_supported(self):
        result = self.cli("replay", self.case["id"], options=("--results-dir", "runtime/cases"))
        self.assertTrue(Path(result["record_path"]).is_relative_to(self.root / "runtime/cases"))
        self.assertEqual(self.cli("status", options=("--results-dir", "runtime/cases"))[0]["state"], "current")

    def test_project_root_dependency_excludes_runtime_evidence(self):
        self.case["dependencies"]["paths"] = ["."]
        self.case["check"]["argv"] = ["{python}", "-c", "pass"]
        self.save()
        self.cli("replay", self.case["id"])
        self.cli("replay", self.case["id"])
        self.assertEqual(self.cli("status")[0]["state"], "current")

    def test_runtime_evidence_cannot_be_declared_as_a_case_input(self):
        self.case["dependencies"]["paths"] = [".fable/runtime/casebook"]
        self.save()
        self.cli("replay", self.case["id"], code=2)
        self.assertFalse((self.root / "ran.txt").exists())

    def test_runtime_ancestor_cannot_hide_observed_input_changes(self):
        (self.root / "component").mkdir()
        (self.root / "component/source.py").write_text("important = True\n")
        self.case["dependencies"]["paths"].append("component/source.py")
        self.save()
        self.cli("replay", self.case["id"])
        (self.root / "component/source.py").write_text("important = False\n")
        self.assertEqual(self.cli("status")[0]["state"], "stale")
        for command in ("show", "status", "replay"):
            with self.subTest(command=command):
                error = self.cli(command, self.case["id"], code=2,
                                 options=("--results-dir", "component"))
                self.assertIn("inputs cannot be inside", error["error"])
        self.assertFalse(list((self.root / "component").glob("*.json")))


if __name__ == "__main__":
    unittest.main()
