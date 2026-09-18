#!/usr/bin/env python3
"""Prepare, score and compare provider-neutral Fable behavioral trials.

The task workspace is a separate directory, not an OS sandbox. Scoring executes
submitted fixture code. No provider APIs, shell command strings or installations.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SCHEMA = 1
SCORER_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
AUTOMATED = {
    "review-boundary": [], "misleading-tests": [], "requirement-conflict": [],
    "bug-fix": ["merge_contract"],
    "stale-knowledge": ["cli_contract", "structured_documentation"],
    "interrupted-work": ["completed_output", "retry_and_recovery"],
}
MEASUREMENT_KEYS = ("elapsed_seconds", "tool_calls", "input_tokens", "output_tokens")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def tree_manifest(directory):
    """Include additions, deletions, directory/mode changes; reject links/devices."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"Expected an ordinary directory: {directory}")
    result = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"Links and special files are not allowed in trial data: {relative}")
        entry = {"type": "directory" if path.is_dir() else "file", "mode": stat.S_IMODE(mode)}
        if path.is_file():
            entry["sha256"] = file_digest(path)
        result[relative] = entry
    return result


def get_catalog(evals=EVALS):
    catalog = read_json(evals / "cases.json")
    if catalog.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported case catalog schema")
    return catalog


def contained(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError("Case paths must be relative")
    target = root / relative
    if ".." in Path(relative).parts or target.is_symlink() or root.resolve() not in target.resolve().parents:
        raise ValueError(f"Case path escapes evaluation data: {relative}")
    return target


def prepare(case_id, destination, variant, skill, host, model, budget="unspecified",
            tools="unspecified", extra_context="none", evals=EVALS):
    catalog = get_catalog(evals)
    matches = [case for case in catalog["cases"] if case["id"] == case_id]
    if len(matches) != 1:
        raise ValueError(f"Unknown or ambiguous case: {case_id}")
    case = dict(matches[0])
    case["manual"] = {**catalog["common_manual"], **case["manual"]}
    case["automated"] = case.get("automated", AUTOMATED.get(case_id))
    if (not isinstance(case["automated"], list)
            or any(not isinstance(name, str) or not name for name in case["automated"])
            or len(case["automated"]) != len(set(case["automated"]))):
        raise ValueError("Case must declare a valid list of automated dimensions")
    if variant not in ("candidate", "baseline"):
        raise ValueError("variant must be candidate or baseline")
    if (variant == "candidate") != (skill is not None):
        raise ValueError("candidate requires --skill; baseline must omit --skill")
    if not host.strip() or not model.strip():
        raise ValueError("Record a nonempty host and model")
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination already exists; prepare a fresh directory for every trial")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fixture = contained(evals, case["fixture"])
    tree_manifest(fixture)
    if skill is not None:
        skill = Path(skill).absolute()
        tree_manifest(skill)
        if not (skill / "SKILL.md").is_file():
            raise ValueError("Candidate skill must contain SKILL.md")
        if skill == destination or skill in destination.parents:
            raise ValueError("Run destination must be outside candidate skill")
    core_prompt = contained(evals, case["prompt"]).read_text(encoding="utf-8")
    staging = Path(tempfile.mkdtemp(prefix=".fable-prepare-", dir=destination.parent))
    try:
        snapshot = staging / "control/snapshot"
        snapshot.mkdir(parents=True)
        shutil.copytree(fixture, snapshot / "fixture")
        shutil.copytree(fixture, staging / "workspace")
        shutil.copyfile(evals / "checkers/check.py", snapshot / "check.py")
        (snapshot / "prompt.md").write_text(core_prompt, encoding="utf-8")
        write_json(snapshot / "case.json", case)
        (staging / "context").mkdir()
        if skill is not None:
            shutil.copytree(skill, staging / "context/skill")
        (staging / "response").mkdir()
        activation = (
            "Read context/skill/SKILL.md and use that Fable Mode snapshot for this task. "
            "Load its referenced resources only when relevant.\n" if variant == "candidate" else
            "Complete the task using your ordinary host instructions; no Fable skill is supplied.\n"
        )
        task = (
            "# Fresh-context task\n\n"
            f"Work in: `{destination / 'workspace'}`\n\n" + activation + "\n"
            "Treat workspace/ as the project. TASK.md and context/ are read-only task inputs. "
            "Do not read or modify control/, assessment.template.json, or score files; those are "
            "evaluator material. Do not inspect the source evaluation suite or other runs. "
            "These directories are separated for evaluation, but are not an OS sandbox.\n\n"
            "Use `python3 -B` or PYTHONDONTWRITEBYTECODE=1 for Python checks. "
            "For review-only tasks, use an external temporary directory for any scratch files.\n\n"
            + core_prompt + "\n"
            "## Delivery\n\n"
            "Save your final response to response/final.md outside the project workspace. "
            "The evaluator should capture the host's tool/action trace separately as "
            "response/trace.md; do not manufacture a trace or present a retrospective summary "
            "as an independent tool log. If trace capture is unavailable, say so.\n"
        )
        (staging / "TASK.md").write_text(task, encoding="utf-8")
        manifest = {
            "schema_version": SCHEMA, "run_id": str(uuid.uuid4()),
            "prepared_utc": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id, "case_version": case["version"],
            "experiment": {"variant": variant, "host": host, "model": model,
                           "budget": budget, "tools": tools, "extra_context": extra_context},
            "snapshot": tree_manifest(snapshot), "context": tree_manifest(staging / "context"),
            "initial_workspace": tree_manifest(staging / "workspace"),
            "task_sha256": file_digest(staging / "TASK.md"),
            "runner_sha256": file_digest(Path(__file__)),
        }
        seal = digest(manifest)
        write_json(staging / "control/manifest.json", manifest)
        (staging / "control/SEAL").write_text(seal + "\n", encoding="ascii")
        template = {
            "schema_version": SCHEMA, "run_id": manifest["run_id"], "run_seal": seal,
            "input_digest": "COPY_FROM_SCORE_JSON_AFTER_EXECUTION", "reviewer": "",
            "dimensions": {name: {"status": "unassessable", "evidence": rubric}
                           for name, rubric in case["manual"].items()},
        }
        write_json(staging / "assessment.template.json", template)
        staging.rename(destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {"run": str(destination), "run_id": manifest["run_id"], "seal": seal,
            "task": str(destination / "TASK.md"), "workspace": str(destination / "workspace"),
            "next": "Start a fresh host context with TASK.md; keep this seal outside the run for anchored scoring."}


def validate_run(run, expected_seal=None):
    run = Path(run).absolute()
    if run.is_symlink() or not run.is_dir():
        raise ValueError("Run must be an ordinary directory")
    # Check all control entries before reading or executing any snapshot content.
    tree_manifest(run / "control")
    manifest = read_json(run / "control/manifest.json")
    if manifest.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported run schema")
    seal = digest(manifest)
    if (run / "control/SEAL").read_text(encoding="ascii").strip() != seal:
        raise ValueError("Run metadata changed after preparation (seal mismatch)")
    if expected_seal is not None and expected_seal != seal:
        raise ValueError("Run seal differs from the evaluator's recorded seal")
    for directory, key in (("control/snapshot", "snapshot"), ("context", "context")):
        if tree_manifest(run / directory) != manifest[key]:
            raise ValueError(f"Sealed {key} changed after preparation")
    if (run / "TASK.md").is_symlink() or file_digest(run / "TASK.md") != manifest["task_sha256"]:
        raise ValueError("Task prompt changed after preparation")
    case = read_json(run / "control/snapshot/case.json")
    if case["id"] != manifest["case_id"] or case["version"] != manifest["case_version"]:
        raise ValueError("Case identity conflicts with sealed manifest")
    if tree_manifest(run / "control/snapshot/fixture") != manifest["initial_workspace"]:
        raise ValueError("Initial workspace conflicts with original fixture snapshot")
    tree_manifest(run / "workspace")
    tree_manifest(run / "response")
    return run, manifest, case, seal


def input_state(run):
    return {"workspace": tree_manifest(run / "workspace"), "response": tree_manifest(run / "response")}


def changes(before, after):
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def validate_assessment(assessment, manifest, seal, state_digest, case, trace_present):
    if assessment.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported assessment schema")
    if (assessment.get("run_id") != manifest["run_id"] or assessment.get("run_seal") != seal
            or assessment.get("input_digest") != state_digest):
        raise ValueError("Assessment does not match this run and its current outputs")
    if not isinstance(assessment.get("reviewer"), str) or not assessment["reviewer"].strip():
        raise ValueError("Assessment must identify its reviewer")
    dimensions = assessment.get("dimensions", {})
    if set(dimensions) != set(case["manual"]):
        raise ValueError("Assessment must cover exactly the case's manual dimensions")
    for name, value in dimensions.items():
        if value.get("status") not in ("pass", "fail", "unassessable"):
            raise ValueError(f"Invalid manual status for {name}")
        if not isinstance(value.get("evidence"), str) or not value["evidence"].strip():
            raise ValueError(f"Manual assessment needs evidence for {name}")
        trace_required = {"truthful_reporting", "process_proportionality", *case.get("trace_required_manual", [])}
        if name in trace_required and not trace_present:
            if value["status"] != "unassessable":
                raise ValueError(f"{name} is unassessable without a captured trace")
    return dimensions


def score(directory, assessment_path=None, expected_seal=None):
    run, manifest, case, seal = validate_run(directory, expected_seal)
    initial = input_state(run)
    state_digest = digest(initial)
    final = run / "response/final.md"
    trace = run / "response/trace.md"
    final_present = final.is_file() and bool(final.read_text(encoding="utf-8").strip())
    trace_present = trace.is_file() and bool(trace.read_text(encoding="utf-8").strip())
    automated = {"response_present": {
        "status": "pass" if final_present else "fail",
        "evidence": "Final response file is present" if final_present else "Missing or empty response/final.md",
    }}
    modified = changes(manifest["initial_workspace"], initial["workspace"])
    if case["mode"] == "review":
        automated["read_only_boundary"] = {
            "status": "fail" if modified else "pass",
            "evidence": "Changed workspace entries: " + ", ".join(modified) if modified else
                        "Workspace contents and modes match initial manifest; transient or outside writes are not observed",
        }
    if case["automated"]:
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory(prefix="fable-evaluator-") as scratch:
            try:
                result = subprocess.run(
                    [sys.executable, "-I", "-B", str(run / "control/snapshot/check.py"),
                     case["id"], str(run / "workspace"), str(run / "control/snapshot/fixture")],
                    cwd=scratch, env=environment, capture_output=True, text=True, timeout=45,
                )
                if result.returncode:
                    raise ValueError(f"Evaluator exited {result.returncode}: {result.stderr[:1000]}")
                checked = json.loads(result.stdout)["dimensions"]
                if set(checked) != set(case["automated"]):
                    raise ValueError("Evaluator returned unexpected dimensions")
                for value in checked.values():
                    if value.get("status") not in ("pass", "fail") or not isinstance(value.get("evidence"), str):
                        raise ValueError("Evaluator returned an invalid dimension")
                automated.update(checked)
            except (subprocess.TimeoutExpired, ValueError, KeyError, TypeError) as error:
                for name in case["automated"]:
                    automated[name] = {"status": "error", "evidence": f"Evaluation did not complete: {error}"[:2000]}
    # Detect evaluator/candidate side effects before accepting any results.
    validate_run(run, seal)
    if input_state(run) != initial:
        raise ValueError("Scoring changed the submitted artifacts; results were not accepted")
    manual = {name: {"status": "pending", "evidence": rubric} for name, rubric in case["manual"].items()}
    assessment = None
    if assessment_path is not None:
        assessment = read_json(Path(assessment_path))
        manual = validate_assessment(assessment, manifest, seal, state_digest, case, trace_present)
    statuses = [item["status"] for item in [*automated.values(), *manual.values()]]
    if "error" in statuses:
        overall = "error"
    elif "fail" in statuses:
        overall = "fail"
    elif any(status in ("pending", "unassessable") for status in statuses):
        overall = "incomplete"
    else:
        overall = "pass"
    result = {
        "schema_version": SCHEMA, "run_id": manifest["run_id"], "run_seal": seal,
        "case_id": case["id"], "case_version": case["version"],
        "scored_utc": datetime.now(timezone.utc).isoformat(), "input_digest": state_digest,
        "scorer_sha256": SCORER_SHA256,
        "experiment": manifest["experiment"], "automated": automated, "manual": manual,
        "assessment": assessment, "workspace_changes": modified, "overall": overall,
        "integrity": "external seal matched" if expected_seal else "local seal only; not independently anchored",
        "limits": ["Directory separation is not an OS sandbox; fixture code executes with evaluator permissions.",
                   "Artifact checks do not certify truthful reporting, reasoning quality, transient writes, or outside effects.",
                   "Manual judgments are reviewer assertions bound to these artifacts and captured trace."],
    }
    result["result_digest"] = digest(result)
    score_path = run / "score.json"
    if score_path.is_symlink():
        raise ValueError("Refusing to overwrite symlinked score.json")
    write_json(score_path, result)
    return result


def checked_result(directory, expected_seal=None):
    run, manifest, case, seal = validate_run(directory, expected_seal)
    path = run / "score.json"
    if path.is_symlink():
        raise ValueError("score.json must not be a link")
    result = read_json(path)
    stored_digest = result.pop("result_digest", None)
    if digest(result) != stored_digest:
        raise ValueError("Stored score was modified")
    result["result_digest"] = stored_digest
    if (result["run_id"] != manifest["run_id"] or result["run_seal"] != seal
            or result["input_digest"] != digest(input_state(run))
            or result["experiment"] != manifest["experiment"]):
        raise ValueError("Stored score is stale or belongs to different artifacts/metadata; score again")
    return manifest, case, result


def normalized_measurements(observation, manifest, seal, state_digest):
    """Validate observer assertions without treating them as measured by this CLI."""
    if not isinstance(observation, dict) or observation.get("schema_version") != SCHEMA:
        raise ValueError("Unsupported observation schema")
    if (observation.get("run_id") != manifest["run_id"] or observation.get("run_seal") != seal
            or observation.get("input_digest") != state_digest):
        raise ValueError("Observation does not match this run and its current outputs/trace")
    for field in ("observer", "source"):
        if not isinstance(observation.get(field), str) or not observation[field].strip():
            raise ValueError(f"Observation must identify its {field}")
    supplied = observation.get("metrics")
    if not isinstance(supplied, dict) or set(supplied) - set(MEASUREMENT_KEYS):
        raise ValueError("Observation metrics must use only supported measurement names")
    metrics = {}
    for name in MEASUREMENT_KEYS:
        entry = supplied.get(name)
        if entry is None:
            metrics[name] = {"value": None, "coverage": "unavailable", "evidence": "No observation supplied"}
            continue
        if not isinstance(entry, dict) or set(entry) != {"value", "coverage", "evidence"}:
            raise ValueError(f"Measurement {name} requires value, coverage, and evidence")
        value, coverage, evidence = entry["value"], entry["coverage"], entry["evidence"]
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"Measurement {name} requires provenance evidence")
        if value is None:
            if coverage != "unavailable":
                raise ValueError(f"Unknown measurement {name} must have unavailable coverage")
        else:
            if coverage not in ("complete", "partial"):
                raise ValueError(f"Observed measurement {name} needs complete or partial coverage")
            numeric = type(value) in (int, float) if name == "elapsed_seconds" else type(value) is int
            if not numeric or value < 0 or (type(value) is float and not math.isfinite(value)):
                raise ValueError(f"Invalid nonnegative {'number' if name == 'elapsed_seconds' else 'integer'} for {name}")
        metrics[name] = {"value": value, "coverage": coverage, "evidence": evidence.strip()}
    return metrics


def record_measurements(directory, observation_path, trace_path=None, expected_seal=None):
    run, manifest, case, seal = validate_run(directory, expected_seal)
    state_digest = digest(input_state(run))
    observation = read_json(Path(observation_path))
    metrics = normalized_measurements(observation, manifest, seal, state_digest)
    record_path, trace_destination = run / "measurements.json", run / "measurement-trace.log"
    if record_path.is_symlink() or trace_destination.is_symlink():
        raise ValueError("Measurement outputs must not be symbolic links")
    trace_data = None
    source_trace = None
    if trace_path is not None:
        trace_path = Path(trace_path)
        if trace_path.is_symlink() or not trace_path.is_file():
            raise ValueError("Measurement trace must be an ordinary file")
        trace_data = trace_path.read_bytes()
        if not trace_data.strip():
            raise ValueError("Measurement trace must not be empty")
        source_trace = {"file": "measurement-trace.log", "sha256": hashlib.sha256(trace_data).hexdigest()}
    record = {
        "schema_version": SCHEMA, "run_id": manifest["run_id"], "run_seal": seal,
        "input_digest": state_digest, "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "recorder_sha256": SCORER_SHA256, "observer": observation["observer"].strip(),
        "source": observation["source"].strip(), "metrics": metrics, "source_trace": source_trace,
    }
    record["record_digest"] = digest(record)
    if trace_data is not None:
        trace_destination.write_bytes(trace_data)
    write_json(record_path, record)
    return record


def checked_measurements(directory, manifest, seal, state_digest):
    run = Path(directory).absolute()
    record_path = run / "measurements.json"
    if record_path.is_symlink():
        raise ValueError("measurements.json must not be a link")
    if not record_path.exists():
        return None
    record = read_json(record_path)
    recorded_digest = record.pop("record_digest", None)
    if digest(record) != recorded_digest:
        raise ValueError("Stored measurements were modified")
    record["record_digest"] = recorded_digest
    normalized_measurements(record, manifest, seal, state_digest)
    source_trace = record.get("source_trace")
    if source_trace is not None:
        if not isinstance(source_trace, dict) or source_trace.get("file") != "measurement-trace.log":
            raise ValueError("Invalid measurement trace reference")
        trace_path = run / "measurement-trace.log"
        if trace_path.is_symlink() or not trace_path.is_file() or file_digest(trace_path) != source_trace.get("sha256"):
            raise ValueError("Measurement source trace changed or is missing")
    return record


def compare(left, right, allow_host_model_difference=False, left_seal=None, right_seal=None):
    left_manifest, left_case, left_result = checked_result(left, left_seal)
    right_manifest, right_case, right_result = checked_result(right, right_seal)
    incompatible = []
    for field in ("case_id", "case_version", "snapshot", "initial_workspace", "runner_sha256"):
        if left_manifest[field] != right_manifest[field]:
            incompatible.append(field)
    if not left_result.get("scorer_sha256") or not right_result.get("scorer_sha256"):
        raise ValueError("Stored scores lack the actual scorer version; score both runs again")
    if left_result["scorer_sha256"] != right_result["scorer_sha256"]:
        incompatible.append("scorer_sha256")
    controlled = ("budget", "tools", "extra_context")
    if not allow_host_model_difference:
        controlled += ("host", "model")
    for field in controlled:
        if left_manifest["experiment"][field] != right_manifest["experiment"][field]:
            incompatible.append("experiment." + field)
    if incompatible:
        raise ValueError("Incompatible trials: " + ", ".join(incompatible))
    if any(left_manifest["experiment"][field] == "unspecified" for field in ("budget", "tools")):
        raise ValueError("Record tools and budget descriptors before preparation to make a controlled comparison")
    dimensions = {}
    for group in ("automated", "manual"):
        if set(left_result[group]) != set(right_result[group]):
            raise ValueError("Incompatible scoring dimensions")
        dimensions[group] = {name: {"left": left_result[group][name], "right": right_result[group][name]}
                             for name in left_result[group]}
    host_model_changed = any(left_manifest["experiment"][field] != right_manifest["experiment"][field]
                             for field in ("host", "model"))
    return {
        "schema_version": SCHEMA, "case_id": left_case["id"], "case_version": left_case["version"],
        "left": {"run_id": left_result["run_id"], "experiment": left_result["experiment"],
                 "candidate_digest": digest(left_manifest["context"]),
                 "preparer_sha256": left_manifest["runner_sha256"],
                 "scorer_sha256": left_result["scorer_sha256"],
                 "measurements": checked_measurements(left, left_manifest, left_result["run_seal"], left_result["input_digest"])},
        "right": {"run_id": right_result["run_id"], "experiment": right_result["experiment"],
                  "candidate_digest": digest(right_manifest["context"]),
                  "preparer_sha256": right_manifest["runner_sha256"],
                  "scorer_sha256": right_result["scorer_sha256"],
                  "measurements": checked_measurements(right, right_manifest, right_result["run_seal"], right_result["input_digest"])},
        "dimensions": dimensions,
        "interpretation": "Descriptive paired results; host/model differs by explicit opt-in." if host_model_changed else
                          "Paired artifact and reviewer outcomes under matching declared conditions.",
        "limits": "One pair is not a provider benchmark or proof of skill improvement. Conditions are operator-declared; repeat fresh runs and inspect evidence. No aggregate quality score is computed.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="list versioned case IDs")
    prepare_parser = commands.add_parser("prepare", help="create a fresh isolated-directory trial")
    prepare_parser.add_argument("case")
    prepare_parser.add_argument("--out", type=Path, required=True)
    prepare_parser.add_argument("--variant", choices=("candidate", "baseline"), required=True)
    prepare_parser.add_argument("--skill", type=Path)
    for name in ("host", "model"):
        prepare_parser.add_argument("--" + name, required=True)
    for name in ("budget", "tools"):
        prepare_parser.add_argument("--" + name, default="unspecified", help="declared condition; required for comparison")
    prepare_parser.add_argument("--extra-context", default="none", help="describe any additional host/project context")
    score_parser = commands.add_parser("score", help="check artifacts; human dimensions remain pending without assessment")
    score_parser.add_argument("run", type=Path)
    score_parser.add_argument("--assessment", type=Path)
    score_parser.add_argument("--seal", help="preparation seal recorded outside the run")
    measure_parser = commands.add_parser("measure", help="record observer-supplied metrics bound to current outputs")
    measure_parser.add_argument("run", type=Path)
    measure_parser.add_argument("observation", type=Path, help="external observer JSON; no provider calls or automatic telemetry")
    measure_parser.add_argument("--trace", type=Path, help="optional actual observer/host trace to preserve as provenance")
    measure_parser.add_argument("--seal", help="preparation seal recorded outside the run")
    compare_parser = commands.add_parser("compare", help="compare dimension evidence for compatible trials")
    compare_parser.add_argument("left", type=Path)
    compare_parser.add_argument("right", type=Path)
    compare_parser.add_argument("--allow-host-model-difference", action="store_true")
    compare_parser.add_argument("--left-seal")
    compare_parser.add_argument("--right-seal")
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "list":
            output = {"schema_version": SCHEMA, "cases": [
                {key: case[key] for key in ("id", "version", "mode", "title")}
                for case in get_catalog()["cases"]]}
        elif arguments.command == "prepare":
            output = prepare(arguments.case, arguments.out, arguments.variant, arguments.skill,
                             arguments.host, arguments.model, arguments.budget, arguments.tools,
                             arguments.extra_context)
        elif arguments.command == "score":
            output = score(arguments.run, arguments.assessment, arguments.seal)
        elif arguments.command == "measure":
            output = record_measurements(arguments.run, arguments.observation, arguments.trace, arguments.seal)
        else:
            output = compare(arguments.left, arguments.right, arguments.allow_host_model_difference,
                             arguments.left_seal, arguments.right_seal)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"Behavioral evaluation failed: {error}\n")
    print(json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False))
    if arguments.command == "score":
        return {"pass": 0, "fail": 1, "error": 2, "incomplete": 3}[output["overall"]]
    return 0


if __name__ == "__main__":
    sys.exit(main())
