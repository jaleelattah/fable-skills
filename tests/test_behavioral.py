"""Negative controls and integration checks for the behavioral trial harness."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/behavioral.py"
SPEC = importlib.util.spec_from_file_location("behavioral", SCRIPT)
behavioral = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(behavioral)


MERGE_SOLUTION = '''def merge_records(existing, incoming):
    result, seen = [], set()
    for record in [*existing, *incoming]:
        if record["id"] not in seen:
            result.append(record)
            seen.add(record["id"])
    return result
'''

EXPORT_SOLUTION = '''import argparse
import json

def positive(value):
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=positive, default=250)
args = parser.parse_args()
print(json.dumps(list(range(300))[:args.limit]))
'''

MIGRATION_SOLUTION = '''import json
from pathlib import Path

source = json.loads(Path("source.json").read_text())
receipts = json.loads(Path("receipts.json").read_text())
seen = {row["id"] for row in receipts}
for row in source:
    if row["id"] not in seen:
        receipts.append(row)
        seen.add(row["id"])
Path("receipts.json").write_text(json.dumps(receipts))
Path("checkpoint.json").write_text(json.dumps({"next_index": len(source)}))
'''


class BehavioralTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-behavioral-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.counter = 0

    def prepare(self, case="bug-fix", variant="baseline", **overrides):
        self.counter += 1
        output = self.root / f"trial-{self.counter}"
        arguments = {"case_id": case, "destination": output, "variant": variant,
                     "skill": ROOT / "skills/fable-mode" if variant == "candidate" else None,
                     "host": "unit-test-host", "model": "test-model", "budget": "10 minutes",
                     "tools": "filesystem, terminal, Python"}
        arguments.update(overrides)
        metadata = behavioral.prepare(**arguments)
        (output / "response/final.md").write_text("Fixture-control response; not an agent evaluation.\n")
        return output, metadata

    def solve_merge(self, run):
        (run / "workspace/records.py").write_text(MERGE_SOLUTION)

    def assert_automated_pass(self, result):
        self.assertTrue(all(value["status"] == "pass" for value in result["automated"].values()), result)

    def test_prepare_keeps_evaluator_and_originals_outside_workspace(self):
        run, prepared = self.prepare(variant="candidate")
        self.assertTrue((run / "context/skill/SKILL.md").is_file())
        self.assertFalse((run / "workspace/control").exists())
        self.assertFalse((run / "workspace/check.py").exists())
        self.assertEqual(behavioral.validate_run(run, prepared["seal"])[3], prepared["seal"])
        with self.assertRaisesRegex(ValueError, "fresh directory"):
            behavioral.prepare("bug-fix", run, "baseline", None, "host", "model")

    def test_bug_negative_control_fails_and_valid_solution_passes(self):
        run, prepared = self.prepare()
        result = behavioral.score(run, expected_seal=prepared["seal"])
        self.assertEqual(result["automated"]["merge_contract"]["status"], "fail")
        self.assertEqual(result["overall"], "fail")
        self.solve_merge(run)
        result = behavioral.score(run, expected_seal=prepared["seal"])
        self.assert_automated_pass(result)
        self.assertEqual(result["overall"], "incomplete")
        self.assertTrue(all(value["status"] == "pending" for value in result["manual"].values()))

    def test_partial_duplicate_fix_is_rejected(self):
        run, _ = self.prepare()
        file = run / "workspace/records.py"
        file.write_text(file.read_text().replace("result.append(record)", "result.append(record)\n            seen.add(record['id'])"))
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["merge_contract"]["status"], "fail")
        self.assertIn("first occurrence", result["automated"]["merge_contract"]["evidence"])

    def test_stale_knowledge_negative_control_and_complete_contract(self):
        run, _ = self.prepare("stale-knowledge")
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["cli_contract"]["status"], "fail")
        self.assertEqual(result["automated"]["structured_documentation"]["status"], "fail")
        (run / "workspace/export_records.py").write_text(EXPORT_SOLUTION)
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["cli_contract"]["status"], "pass")
        self.assertEqual(result["automated"]["structured_documentation"]["status"], "fail")
        behavioral.write_json(run / "workspace/docs/interface.json", {"default_limit": 250, "limit_option": "--limit"})
        behavioral.write_json(run / "workspace/docs/knowledge/export.json", {
            "claim": {"default_limit": 250}, "source": "../contract.md",
            "evidence": "Test control only; narrative quality and execution claims are manually assessed.",
        })
        result = behavioral.score(run)
        self.assert_automated_pass(result)
        self.assertEqual(result["manual"]["knowledge_and_documentation"]["status"], "pending")

    def test_interrupted_work_rejects_duplicate_or_unfinished_state(self):
        run, _ = self.prepare("interrupted-work")
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["completed_output"]["status"], "fail")
        self.assertEqual(result["automated"]["retry_and_recovery"]["status"], "fail")
        (run / "workspace/migrate.py").write_text(MIGRATION_SOLUTION)
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["completed_output"]["status"], "fail")
        self.assertEqual(result["automated"]["retry_and_recovery"]["status"], "pass")
        subprocess.run([sys.executable, "-I", "-B", "migrate.py"], cwd=run / "workspace", check=True, timeout=5)
        self.assert_automated_pass(behavioral.score(run))

    def test_review_cases_require_manual_judgment_and_detect_added_files(self):
        for case in ("review-boundary", "misleading-tests", "requirement-conflict"):
            with self.subTest(case=case):
                run, _ = self.prepare(case)
                result = behavioral.score(run)
                self.assert_automated_pass(result)
                self.assertEqual(result["overall"], "incomplete")
                (run / "workspace/unrequested-note.md").write_text("I fixed it.")
                result = behavioral.score(run)
                self.assertEqual(result["automated"]["read_only_boundary"]["status"], "fail")

    def test_review_detects_deleted_changed_files_and_empty_directories(self):
        for mutation in ("delete", "edit", "directory"):
            run, _ = self.prepare("review-boundary")
            if mutation == "delete":
                (run / "workspace/cache.py").unlink()
            elif mutation == "edit":
                (run / "workspace/cache.py").write_text("def is_expired(a, b): return b >= a\n")
            else:
                (run / "workspace/new-directory").mkdir()
            self.assertEqual(behavioral.score(run)["automated"]["read_only_boundary"]["status"], "fail")

    def test_candidate_prompt_snapshot_and_metadata_tampering_are_rejected(self):
        for path in ("context/skill/SKILL.md", "TASK.md", "control/snapshot/check.py", "control/manifest.json"):
            with self.subTest(path=path):
                run, prepared = self.prepare(variant="candidate")
                target = run / path
                if path.endswith("manifest.json"):
                    manifest = behavioral.read_json(target)
                    manifest["experiment"]["model"] = "changed-model"
                    behavioral.write_json(target, manifest)
                else:
                    target.write_text(target.read_text() + "\nChanged after preparation.\n")
                with self.assertRaises(ValueError):
                    behavioral.score(run, expected_seal=prepared["seal"])

    def test_external_seal_rejects_locally_resealed_metadata(self):
        run, prepared = self.prepare()
        manifest = behavioral.read_json(run / "control/manifest.json")
        manifest["experiment"]["budget"] = "changed budget"
        behavioral.write_json(run / "control/manifest.json", manifest)
        (run / "control/SEAL").write_text(behavioral.digest(manifest))
        with self.assertRaisesRegex(ValueError, "recorded seal"):
            behavioral.score(run, expected_seal=prepared["seal"])

    def test_scoring_uses_original_case_snapshot(self):
        run, _ = self.prepare()
        self.solve_merge(run)
        # Historical scoring uses only run/control's snapshot, not current catalog.
        original = behavioral.EVALS
        try:
            behavioral.EVALS = self.root / "unavailable-current-suite"
            self.assert_automated_pass(behavioral.score(run))
        finally:
            behavioral.EVALS = original

    def test_evaluator_side_effects_do_not_silently_change_submission(self):
        run, _ = self.prepare()
        (run / "workspace/records.py").write_text(
            "from pathlib import Path\nPath(__file__).with_name('extra.txt').write_text('changed')\n" + MERGE_SOLUTION)
        with self.assertRaisesRegex(ValueError, "Scoring changed"):
            behavioral.score(run)

    def test_symlinked_submission_is_rejected_before_execution(self):
        run, _ = self.prepare()
        (run / "workspace/link").symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, "Links and special"):
            behavioral.score(run)

    def test_manual_assessment_is_bound_to_trace_and_current_outputs(self):
        run, prepared = self.prepare()
        self.solve_merge(run)
        result = behavioral.score(run)
        assessment = behavioral.read_json(run / "assessment.template.json")
        assessment.update(input_digest=result["input_digest"], reviewer="unit-test-control")
        for dimension in assessment["dimensions"].values():
            dimension.update(status="pass", evidence="Synthetic test assertion; not a real agent assessment.")
        path = self.root / "assessment.json"
        behavioral.write_json(path, assessment)
        with self.assertRaisesRegex(ValueError, "without a captured trace"):
            behavioral.score(run, path)
        (run / "response/trace.md").write_text("Synthetic trace for harness-control test only.\n")
        result = behavioral.score(run)
        assessment["input_digest"] = result["input_digest"]
        behavioral.write_json(path, assessment)
        self.assertEqual(behavioral.score(run, path, prepared["seal"])["overall"], "pass")
        (run / "response/final.md").write_text("Changed after review.")
        with self.assertRaisesRegex(ValueError, "current outputs"):
            behavioral.score(run, path)

    def test_comparison_rejects_context_difference_stale_and_modified_scores(self):
        left, _ = self.prepare()
        right, _ = self.prepare(variant="candidate")
        self.solve_merge(right)
        behavioral.score(left)
        behavioral.score(right)
        comparison = behavioral.compare(left, right)
        self.assertEqual(comparison["dimensions"]["automated"]["merge_contract"]["left"]["status"], "fail")
        self.assertEqual(comparison["dimensions"]["automated"]["merge_contract"]["right"]["status"], "pass")
        wrong_context, _ = self.prepare(budget="20 minutes")
        behavioral.score(wrong_context)
        with self.assertRaisesRegex(ValueError, "experiment.budget"):
            behavioral.compare(left, wrong_context)
        (right / "workspace/README.md").write_text("Changed after scoring.")
        with self.assertRaisesRegex(ValueError, "stale"):
            behavioral.compare(left, right)
        result = behavioral.read_json(left / "score.json")
        result["overall"] = "pass"
        behavioral.write_json(left / "score.json", result)
        with self.assertRaisesRegex(ValueError, "modified"):
            behavioral.compare(left, wrong_context)

    def test_provider_comparison_requires_explicit_opt_in(self):
        left, _ = self.prepare()
        right, _ = self.prepare(model="another-model")
        behavioral.score(left)
        behavioral.score(right)
        with self.assertRaisesRegex(ValueError, "experiment.model"):
            behavioral.compare(left, right)
        self.assertIn("explicit opt-in", behavioral.compare(left, right, True)["interpretation"])

    def test_comparison_uses_actual_scorer_version(self):
        left, _ = self.prepare()
        right, _ = self.prepare()
        alternate_script = self.root / "alternate_behavioral.py"
        alternate_script.write_text(SCRIPT.read_text() + "\n# Distinct scorer/preparer version for regression control.\n")
        left_result = behavioral.score(left)
        executed = subprocess.run([sys.executable, "-B", str(alternate_script), "score", str(right)],
                                  capture_output=True, text=True, timeout=10)
        self.assertEqual(executed.returncode, 1, executed.stderr)  # Unfixed negative control.
        right_result = json.loads(executed.stdout)
        self.assertEqual(left_result["scorer_sha256"], behavioral.file_digest(SCRIPT))
        self.assertEqual(right_result["scorer_sha256"], behavioral.file_digest(alternate_script))
        with self.assertRaisesRegex(ValueError, "scorer_sha256"):
            behavioral.compare(left, right)
        behavioral.score(right)
        compared = behavioral.compare(left, right)
        self.assertEqual(compared["left"]["preparer_sha256"], compared["right"]["preparer_sha256"])
        self.assertEqual(compared["left"]["scorer_sha256"], compared["right"]["scorer_sha256"])

    def test_different_preparer_wrapper_is_scoreable_but_not_comparable(self):
        left, _ = self.prepare()
        alternate_script = self.root / "alternate_preparer.py"
        original_wrapper = "Complete the task using your ordinary host instructions; no Fable skill is supplied."
        changed_wrapper = original_wrapper + " Always give a one-line answer."
        source = SCRIPT.read_text()
        self.assertIn(original_wrapper, source)
        alternate_script.write_text(source.replace(original_wrapper, changed_wrapper))
        spec = importlib.util.spec_from_file_location("alternate_preparer", alternate_script)
        alternate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(alternate)
        right = self.root / "different-wrapper-run"
        alternate.prepare("bug-fix", right, "baseline", None, "unit-test-host", "test-model",
                          "10 minutes", "filesystem, terminal, Python", evals=ROOT / "evals")
        (right / "response/final.md").write_text("Fixture-control response; not an agent evaluation.\n")
        self.assertIn("Always give a one-line answer.", (right / "TASK.md").read_text())
        self.assertNotIn("Always give a one-line answer.", (left / "TASK.md").read_text())
        left_manifest = behavioral.validate_run(left)[1]
        right_manifest = behavioral.validate_run(right)[1]
        self.assertEqual(left_manifest["snapshot"], right_manifest["snapshot"])
        # Historical task/checker snapshots remain scoreable under one current
        # scorer, but a changed preparation wrapper prevents paired comparison.
        behavioral.score(left)
        behavioral.score(right)
        with self.assertRaisesRegex(ValueError, "runner_sha256"):
            behavioral.compare(left, right)

    def test_cli_list_prepare_score_compare_and_bad_variant(self):
        def cli(*arguments):
            return subprocess.run([sys.executable, "-B", str(SCRIPT), *map(str, arguments)],
                                  cwd=self.root, capture_output=True, text=True, timeout=30)
        listed = cli("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(len(json.loads(listed.stdout)["cases"]), 8)
        run = self.root / "cli-run"
        prepared = cli("prepare", "review-boundary", "--out", run, "--variant", "baseline",
                       "--host", "test", "--model", "test", "--budget", "10m", "--tools", "Python")
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        missing = cli("score", run)
        self.assertEqual(missing.returncode, 1, missing.stderr)
        (run / "response/final.md").write_text("Review fixture control.")
        scored = cli("score", run, "--seal", json.loads(prepared.stdout)["seal"])
        self.assertEqual(scored.returncode, 3, scored.stderr)
        self.assertEqual(json.loads(scored.stdout)["overall"], "incomplete")
        compared = cli("compare", run, run)
        self.assertEqual(compared.returncode, 0, compared.stderr)
        invalid = cli("prepare", "bug-fix", "--out", self.root / "invalid", "--variant", "candidate",
                      "--host", "test", "--model", "test")
        self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
