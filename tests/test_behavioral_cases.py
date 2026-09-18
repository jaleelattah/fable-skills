"""Accepted and failing artifact controls for restraint and staged learning.

These construct fixture artifacts; they are not fresh-context agent trials.
"""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("behavioral_cases_runner", ROOT / "scripts/behavioral.py")
behavioral = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(behavioral)
BATCH_INPUT = [9999, 10000, 10001, 19999, 20000, 20001]
POLICY_V2 = {"minimum_subtotal_cents": 20000, "discount_percent": 20}


class AddedBehavioralCasesTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="fable-added-cases-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.count = 0

    def prepare(self, case):
        self.count += 1
        run = self.root / str(self.count)
        metadata = behavioral.prepare(case, run, "baseline", None, "fixture-control", "none")
        (run / "response/final.md").write_text("Constructed artifact control; not an actor run.\n")
        return run, metadata

    def score(self, run):
        return behavioral.score(run)["automated"]

    def write_note(self, project, supersedes=None):
        policy = json.loads((project / "policy.json").read_text())
        directory = project / "docs/knowledge"
        directory.mkdir(parents=True, exist_ok=True)
        note = {
            "lesson": "The boundary is inclusive; numeric policy values are read from their source.",
            "claim": dict(policy, threshold_inclusive=True),
            "source": "policy.json",
            "source_sha256": hashlib.sha256((project / "policy.json").read_bytes()).hexdigest(),
            "evidence": "Constructed fixture control, not an execution claim: " + str(policy),
        }
        if supersedes:
            note["supersedes_source_sha256"] = supersedes
        (directory / "discount.json").write_text(json.dumps(note))
        (directory / "index.md").write_text("[Discount lesson](discount.json)\n")
        return note

    def snapshot(self, run, phase):
        target = run / "response/stages" / phase
        target.mkdir(parents=True)
        shutil.copytree(run / "workspace", target / "workspace")
        shutil.copyfile(run / "response/final.md", target / "final.md")

    def write_batch(self, project):
        policy = json.loads((project / "policy.json").read_text())
        expected = [value if value < policy["minimum_subtotal_cents"] else
                    value * (100 - policy["discount_percent"]) // 100 for value in BATCH_INPUT]
        (project / "batch-quotes.json").write_text(json.dumps(expected))

    def completed_cycle(self):
        run, metadata = self.prepare("learning-cycle")
        project = run / "workspace"
        pricing = project / "pricing.py"
        pricing.write_text(pricing.read_text().replace("subtotal_cents > ", "subtotal_cents >= "))
        note = self.write_note(project)
        self.snapshot(run, "01-capture")
        pricing.write_text(pricing.read_text() + "\n\ndef quote_many(subtotals):\n    return [quote(value) for value in subtotals]\n")
        self.write_batch(project)
        self.snapshot(run, "02-reuse")
        (project / "policy.json").write_text(json.dumps(POLICY_V2))
        self.write_note(project, supersedes=note["source_sha256"])
        self.write_batch(project)
        return run, metadata

    def test_routine_edit_control_requires_exact_typo_and_boundary(self):
        run, _ = self.prepare("routine-edit")
        self.assertEqual(self.score(run)["routine_edit_boundary"]["status"], "fail")
        readme = run / "workspace/README.md"
        readme.write_text(readme.read_text().replace("recieve", "receive"))
        result = behavioral.score(run)
        self.assertEqual(result["automated"]["routine_edit_boundary"]["status"], "pass")
        self.assertEqual(result["overall"], "incomplete")
        self.assertEqual(result["manual"]["routine_restraint"]["status"], "pending")
        (run / "workspace/workflow.md").write_text("An unnecessary plan\n")
        self.assertEqual(self.score(run)["routine_edit_boundary"]["status"], "fail")

    def test_routine_edit_rejects_unrelated_code_and_mode_changes(self):
        for mutation in ("code", "mode"):
            with self.subTest(mutation=mutation):
                run, _ = self.prepare("routine-edit")
                readme = run / "workspace/README.md"
                readme.write_text(readme.read_text().replace("recieve", "receive"))
                code = run / "workspace/greeting.py"
                if mutation == "code":
                    code.write_text(code.read_text() + "\n# unrelated change\n")
                else:
                    code.chmod(code.stat().st_mode ^ 0o100)
                self.assertEqual(self.score(run)["routine_edit_boundary"]["status"], "fail")

    def test_learning_cycle_metadata_seals_later_stage_tasks(self):
        run, metadata = self.prepare("learning-cycle")
        case = json.loads((run / "control/snapshot/case.json").read_text())
        self.assertEqual([stage["id"] for stage in case["stages"]], ["01-capture", "02-reuse", "03-source-change"])
        self.assertNotIn("Stage 2", (run / "TASK.md").read_text())
        self.assertFalse((run / "workspace/docs/knowledge").exists())
        behavioral.validate_run(run, metadata["seal"])

    def test_learning_cycle_missing_history_is_rejected(self):
        run, _ = self.prepare("learning-cycle")
        result = self.score(run)
        for dimension in ("capture_artifacts", "reuse_artifacts", "updated_policy_artifacts"):
            self.assertEqual(result[dimension]["status"], "fail")
            self.assertIn("missing operator snapshot", result[dimension]["evidence"])

    def test_complete_cycle_artifacts_pass_with_manual_process_pending(self):
        run, metadata = self.completed_cycle()
        result = behavioral.score(run, expected_seal=metadata["seal"])
        self.assertTrue(all(item["status"] == "pass" for item in result["automated"].values()), result)
        self.assertEqual(result["overall"], "incomplete")
        self.assertEqual(result["manual"]["learning_process"]["status"], "pending")

    def test_final_solution_cannot_hide_bad_capture_or_reuse_phases(self):
        for phase, dimension in (("01-capture", "capture_artifacts"), ("02-reuse", "reuse_artifacts")):
            with self.subTest(phase=phase):
                run, _ = self.completed_cycle()
                code = run / "response/stages" / phase / "workspace/pricing.py"
                code.write_text(code.read_text().replace("subtotal_cents >= ", "subtotal_cents > "))
                result = self.score(run)
                self.assertEqual(result[dimension]["status"], "fail")
                self.assertEqual(result["updated_policy_artifacts"]["status"], "pass")

    def test_reuse_must_retain_the_actor_generated_lesson(self):
        run, _ = self.completed_cycle()
        path = run / "response/stages/02-reuse/workspace/docs/knowledge/discount.json"
        note = json.loads(path.read_text())
        note["lesson"] = "Replacement note does not establish transfer from capture."
        path.write_text(json.dumps(note))
        result = self.score(run)
        self.assertEqual(result["reuse_artifacts"]["status"], "fail")
        self.assertIn("retain", result["reuse_artifacts"]["evidence"])

    def test_stale_knowledge_is_rejected_even_when_current_code_works(self):
        run, _ = self.completed_cycle()
        old = run / "response/stages/02-reuse/workspace/docs/knowledge/discount.json"
        shutil.copyfile(old, run / "workspace/docs/knowledge/discount.json")
        result = self.score(run)
        self.assertEqual(result["updated_policy_artifacts"]["status"], "fail")
        self.assertIn("knowledge claim", result["updated_policy_artifacts"]["evidence"])

    def test_hardcoded_new_policy_fails_the_alternate_source_check(self):
        run, _ = self.completed_cycle()
        pricing = run / "workspace/pricing.py"
        pricing.write_text(pricing.read_text().replace(
            'policy = json.loads(Path(__file__).with_name("policy.json").read_text())',
            "policy = " + repr(POLICY_V2)))
        result = self.score(run)
        self.assertEqual(result["updated_policy_artifacts"]["status"], "fail")
        self.assertIn("wrong quote", result["updated_policy_artifacts"]["evidence"])

    def test_missing_phase_response_is_rejected(self):
        run, _ = self.completed_cycle()
        (run / "response/stages/01-capture/final.md").unlink()
        result = self.score(run)
        self.assertEqual(result["capture_artifacts"]["status"], "fail")

    def test_structured_lesson_and_evidence_complete_the_cycle(self):
        run, _ = self.completed_cycle()
        for project in (run / "response/stages/01-capture/workspace",
                        run / "response/stages/02-reuse/workspace", run / "workspace"):
            path = project / "docs/knowledge/discount.json"
            note = json.loads(path.read_text())
            note["lesson"] = {"failure": "The exact minimum subtotal was excluded.",
                              "scope": ["Read numeric values from the current policy; the threshold is inclusive."]}
            note["evidence"] = {
                "command": "python3 -B -m unittest discover",
                "result": {"exit_code": 0, "policy": note["claim"]},
                "observations": ["Constructed artifact control; actual execution remains a manual assessment."],
            }
            note["claim"]["rounding_note"] = "Use the documented integer-cents calculation."
            path.write_text(json.dumps(note))
        result = behavioral.score(run)
        self.assertEqual(result["case_version"], 2)
        self.assertTrue(all(item["status"] == "pass" for item in result["automated"].values()), result)
        self.assertEqual(result["manual"]["learning_process"]["status"], "pending")
        self.assertEqual(result["manual"]["truthful_reporting"]["status"], "pending")

    def test_empty_or_nontextual_cycle_narratives_are_rejected(self):
        for field in ("lesson", "evidence"):
            for value in ({}, [], {"count": 250, "passed": True}, [" ", {"exit_code": 0}], None):
                with self.subTest(field=field, value=value):
                    run, _ = self.completed_cycle()
                    for project in (run / "response/stages/01-capture/workspace",
                                    run / "response/stages/02-reuse/workspace", run / "workspace"):
                        path = project / "docs/knowledge/discount.json"
                        note = json.loads(path.read_text())
                        note[field] = value
                        path.write_text(json.dumps(note))
                    result = self.score(run)
                    for dimension in ("capture_artifacts", "reuse_artifacts", "updated_policy_artifacts"):
                        self.assertEqual(result[dimension]["status"], "fail")
                        self.assertIn("descriptive " + field, result[dimension]["evidence"])


if __name__ == "__main__":
    unittest.main()
