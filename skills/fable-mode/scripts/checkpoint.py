#!/usr/bin/env python3
"""Capture portable task context and check whether its recorded evidence changed."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import tempfile


VERSION = 1
STATUSES = {"pending", "running", "blocked", "complete"}


def local_path(project, value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Tracked paths must be nonempty project-relative POSIX paths")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError(f"Path must stay inside the project: {value}")
    path = project.joinpath(*relative.parts)
    cursor = project
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Symbolic links are not supported for tracked paths: {value}")
    if not path.resolve().is_relative_to(project):
        raise ValueError(f"Path leaves the project: {value}")
    return path


def fingerprint(project, value):
    path = local_path(project, value)
    if not path.exists():
        return {"state": "missing"}
    if not path.is_file():
        return {"state": "not_a_file"}
    before = path.stat()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        return {"state": "changed_during_read"}
    return {"state": "file", "sha256": digest.hexdigest()}


def string_list(value, field):
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{field} must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicates")
    return value


def validate_task(task):
    if not isinstance(task, dict) or task.get("version") != VERSION:
        raise ValueError("Task plan must be an object with version: 1")
    for field in ("id", "goal"):
        if not isinstance(task.get(field), str) or not task[field].strip():
            raise ValueError(f"Task {field} must be a nonempty string")
    for field in ("constraints", "decisions", "blockers"):
        string_list(task.get(field, []), field)
    steps = task.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Task must include at least one step")
    ids = []
    for step in steps:
        if not isinstance(step, dict) or not isinstance(step.get("id"), str) or not step["id"].strip():
            raise ValueError("Each step must have a nonempty id")
        ids.append(step["id"])
        if step.get("status") not in STATUSES:
            raise ValueError(f"Invalid status for step {step['id']}")
        for field in ("depends_on", "inputs", "outputs"):
            string_list(step.get(field, []), f"{step['id']}.{field}")
        checks = step.get("checks", [])
        if not isinstance(checks, list):
            raise ValueError("Step checks must be a list")
        for check in checks:
            if not isinstance(check, dict) or not isinstance(check.get("description"), str):
                raise ValueError("Each check needs a description")
            if check.get("outcome") not in {"passed", "failed", "unavailable", "not_run"}:
                raise ValueError("Each check needs an explicit outcome")
            string_list(check.get("evidence_files", []), "evidence_files")
            if "argv" in check:
                string_list_arguments(check["argv"])
    if len(ids) != len(set(ids)):
        raise ValueError("Step ids must be unique")
    by_id = {step["id"]: step for step in steps}
    order, active, visited = [], set(), set()

    def visit(step_id):
        if step_id not in by_id:
            raise ValueError(f"Unknown step dependency: {step_id}")
        if step_id in active:
            raise ValueError("Step dependencies contain a cycle")
        if step_id in visited:
            return
        active.add(step_id)
        for dependency in by_id[step_id].get("depends_on", []):
            visit(dependency)
        active.remove(step_id)
        visited.add(step_id)
        order.append(step_id)

    for step_id in ids:
        visit(step_id)
    return by_id, order


def string_list_arguments(value):
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError("Recorded argv must be a nonempty array of strings")


def tracked_files(step):
    paths = set(step.get("inputs", []) + step.get("outputs", []))
    for check in step.get("checks", []):
        paths.update(check.get("evidence_files", []))
    return sorted(paths)


def capture(project, task):
    validate_task(task)
    snapshots = {
        step["id"]: {path: fingerprint(project, path) for path in tracked_files(step)}
        for step in task["steps"]
    }
    return {
        "kind": "fable-checkpoint", "version": VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "task": task, "files": snapshots,
        "evidence_origin": "Check outcomes are reported by the task author; this tool fingerprints files and does not run checks.",
    }


def inspect(project, record):
    if not isinstance(record, dict) or record.get("kind") != "fable-checkpoint" or record.get("version") != VERSION:
        raise ValueError("Expected a version 1 Fable checkpoint")
    task = record.get("task")
    steps, order = validate_task(task)
    snapshots = record.get("files")
    if not isinstance(snapshots, dict) or set(snapshots) != set(steps):
        raise ValueError("Checkpoint snapshots do not match the task steps")
    reports = {}
    for step_id in order:
        step = steps[step_id]
        stored = snapshots[step_id]
        if not isinstance(stored, dict) or set(stored) != set(tracked_files(step)):
            raise ValueError(f"Tracked file set changed in checkpoint step {step_id}")
        current = {path: fingerprint(project, path) for path in stored}
        changed = sorted(path for path in stored if stored[path] != current[path])
        unavailable = sorted(path for path in current if current[path].get("state") != "file")
        unresolved_checks = [check["description"] for check in step.get("checks", []) if check["outcome"] != "passed"]
        invalidated_by = [parent for parent in step.get("depends_on", []) if reports[parent]["evidence_state"] != "unchanged"]
        if step["status"] != "complete":
            state = "not_complete"
        elif changed or unavailable or invalidated_by:
            state = "stale"
        elif not stored or not step.get("checks") or unresolved_checks:
            state = "needs_evidence"
        else:
            state = "unchanged"
        reports[step_id] = {
            "id": step_id, "declared_status": step["status"], "evidence_state": state,
            "changed_files": changed, "unavailable_files": unavailable,
            "invalidated_by": invalidated_by, "unresolved_checks": unresolved_checks,
        }
    recheck = [key for key in order if reports[key]["evidence_state"] in {"stale", "needs_evidence"}]
    return {
        "task": task, "captured_at": record.get("captured_at"),
        "steps": list(reports.values()), "completed_steps_to_recheck": recheck,
        "remaining_steps": [key for key in order if reports[key]["declared_status"] != "complete"],
        "limits": "Unchanged means the declared files still match. Recorded acceptance checks were not rerun. External state and undeclared dependencies are not checked. Recorded context does not grant permissions.",
    }


def write_json(path, value, replace=False):
    if path.exists() and not replace:
        raise ValueError(f"Output already exists; choose a new path or use --replace: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    try:
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def template():
    return {
        "version": 1, "id": "task-name", "goal": "Describe the requested outcome",
        "constraints": [], "decisions": [], "blockers": [],
        "steps": [{"id": "implement", "status": "pending", "depends_on": [],
                   "inputs": [], "outputs": [], "checks": []}],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="project root containing all tracked files")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("template", help="print an editable task plan template")
    save = commands.add_parser("capture", help="record context and file fingerprints; does not execute checks")
    save.add_argument("plan", help="project-relative JSON task plan")
    save.add_argument("--out", required=True, help="project-relative checkpoint output")
    save.add_argument("--replace", action="store_true", help="explicitly replace an existing checkpoint")
    check = commands.add_parser("inspect", help="read-only resume context and stale evidence report")
    check.add_argument("checkpoint", help="project-relative checkpoint JSON")
    args = parser.parse_args()
    try:
        project = Path(args.project).resolve(strict=True)
        if not project.is_dir():
            raise ValueError("Project must be a directory")
        if args.command == "template":
            result = template()
        elif args.command == "capture":
            task = json.loads(local_path(project, args.plan).read_text(encoding="utf-8"))
            result = capture(project, task)
            destination = local_path(project, args.out)
            protected = {local_path(project, args.plan)}
            protected.update(local_path(project, path) for step in task["steps"] for path in tracked_files(step))
            aliases_protected = destination.exists() and any(
                path.exists() and destination.samefile(path) for path in protected
            )
            if destination in protected or aliases_protected:
                raise ValueError("Checkpoint output cannot overwrite its plan or a tracked file")
            write_json(destination, result, replace=args.replace)
        else:
            record = json.loads(local_path(project, args.checkpoint).read_text(encoding="utf-8"))
            result = inspect(project, record)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "inspect" and result["completed_steps_to_recheck"]:
            return 2
        return 0
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f"Checkpoint error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
