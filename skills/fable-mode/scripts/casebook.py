#!/usr/bin/env python3
"""Search project lessons and explicitly replay trusted checks (Python 3.9+)."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
import uuid


class CaseError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def local_path(root, value):
    """Reject lexical escapes and symlinks, including links inside the project."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise CaseError("Paths must be nonempty project-relative POSIX paths")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise CaseError("Path escapes the selected project: " + value)
    target = root
    for part in relative.parts:
        target = target / part
        if target.is_symlink():
            raise CaseError("Symbolic links are not accepted: " + value)
    if not target.resolve().is_relative_to(root):
        raise CaseError("Path escapes the selected project: " + value)
    return target


def text_field(obj, key):
    if not isinstance(obj.get(key), str) or not obj[key].strip():
        raise CaseError("Missing or invalid text field: " + key)


def string_list(value, name, required=False):
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise CaseError(name + " must be a list of nonempty strings")
    if required and not value:
        raise CaseError(name + " must not be empty")
    return value


def load_cases(root, path):
    try:
        document = json.loads(local_path(root, path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseError("Cannot read case definitions: " + type(exc).__name__) from exc
    if not isinstance(document, dict) or document.get("version") != 1:
        raise CaseError("Expected casebook version 1")
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise CaseError("cases must be a list")
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise CaseError("Each case must be an object")
        for field in ("id", "title", "lesson", "invariant"):
            text_field(case, field)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", case["id"]) or case["id"] in ids:
            raise CaseError("Case IDs must be unique lowercase slugs")
        ids.add(case["id"])
        string_list(case.get("tags"), "tags")
        applicability = case.get("applicability")
        dependencies = case.get("dependencies")
        check = case.get("check")
        if not all(isinstance(x, dict) for x in (applicability, dependencies, check)):
            raise CaseError("applicability, dependencies, and check must be objects")
        text_field(applicability, "when")
        paths = list(string_list(applicability.get("paths"), "applicability.paths", True))
        paths += string_list(dependencies.get("paths"), "dependencies.paths", True)
        tools = string_list(dependencies.get("executables"), "dependencies.executables")
        if any("/" in tool or "\\" in tool or ":" in tool for tool in tools):
            raise CaseError("Dependency executables must be command names")
        sources = case.get("sources")
        if not isinstance(sources, list) or not sources:
            raise CaseError("sources must contain at least one project source")
        for source in sources:
            if not isinstance(source, dict):
                raise CaseError("sources must contain objects")
            text_field(source, "path")
            text_field(source, "note")
            paths.append(source["path"])
        for path in paths:
            local_path(root, path)
        argv = string_list(check.get("argv"), "check.argv", True)
        if any("\x00" in arg for arg in argv):
            raise CaseError("Command arguments cannot contain NUL")
        text_field(check, "cwd")
        local_path(root, check["cwd"])
        timeout = check.get("timeout_seconds")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
            raise CaseError("timeout_seconds must be greater than 0 and at most 3600")
    return cases


def observed_paths(case):
    return sorted(set(case["applicability"]["paths"] + case["dependencies"]["paths"] + [s["path"] for s in case["sources"]]))


def fingerprint_files(root, case, results):
    hashes, stamps, missing = {}, {}, []

    def visit(path):
        relative = path.relative_to(root).as_posix()
        if path == results or path.is_relative_to(results) or path.name in (".git", "__pycache__"):
            return
        local_path(root, relative)
        if not path.exists():
            missing.append(relative)
        elif path.is_dir():
            hashes[relative + "/"] = "directory"
            for child in sorted(path.iterdir()):
                visit(child)
        elif path.is_file():
            before = path.stat()
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(chunk)
            after = path.stat()
            stamp = (after.st_mtime_ns, after.st_ctime_ns, after.st_size, after.st_ino)
            if (before.st_mtime_ns, before.st_ctime_ns, before.st_size, before.st_ino) != stamp:
                raise CaseError("Input changed while hashing: " + relative)
            hashes[relative], stamps[relative] = hasher.hexdigest(), stamp
        else:
            raise CaseError("Only regular files and directories are supported: " + relative)

    for value in observed_paths(case):
        visit(local_path(root, value))
    return hashes, stamps, sorted(set(missing))


def execution(root, case):
    argv = list(case["check"]["argv"])
    missing = []
    if argv[0] == "{python}":
        argv[0] = sys.executable
    elif "/" in argv[0] or "\\" in argv[0] or ":" in argv[0]:
        command = local_path(root, argv[0])
        argv[0] = str(command)
        if not command.is_file() or not os.access(command, os.X_OK):
            missing.append("executable: " + case["check"]["argv"][0])
    else:
        resolved = shutil.which(argv[0])
        if resolved:
            argv[0] = resolved
        else:
            missing.append("executable: " + argv[0])
    executables = {}
    for name in case["dependencies"]["executables"]:
        found = shutil.which(name)
        if found:
            executables[name] = found
        else:
            missing.append("executable: " + name)
    cwd = local_path(root, case["check"]["cwd"])
    if not cwd.is_dir():
        missing.append("working directory: " + case["check"]["cwd"])
    return argv, cwd, executables, missing


def inspect_case(root, case, results):
    for value in observed_paths(case):
        path = local_path(root, value)
        if path == results or path.is_relative_to(results):
            raise CaseError("Case inputs cannot be inside the runtime results directory")
    hashes, stamps, missing = fingerprint_files(root, case, results)
    argv, cwd, executables, unavailable = execution(root, case)
    return {
        "definition_sha256": digest(case),
        "file_hashes": hashes,
        "argv": argv,
        "cwd": str(cwd),
        "executables": executables,
        "missing": ["path: " + x for x in missing] + unavailable,
    }, stamps


def latest_record(root, results, case_id):
    if not results.exists():
        return None
    # IDs may themselves contain "--". Match the complete filename grammar so
    # evidence for "a--b" cannot be selected when looking up case "a".
    record_name = re.compile(re.escape(case_id) + r"--[0-9]{8}T[0-9]{12}Z--[0-9a-f]{32}\.json")
    paths = sorted((path for path in results.glob(case_id + "--*.json")
                    if record_name.fullmatch(path.name)), reverse=True)
    if not paths:
        return None
    path = local_path(root, paths[0].relative_to(root).as_posix())
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CaseError("Latest evidence is unreadable; inspect " + str(path)) from exc
    if not isinstance(record, dict) or record.get("version") != 1 or record.get("case_id") != case_id:
        raise CaseError("Invalid evidence record: " + str(path))
    record["record_path"] = str(path)
    return record


def status(root, case, results):
    current, _ = inspect_case(root, case, results)
    record = latest_record(root, results, case["id"])
    state, reasons = "unrecorded", []
    if current["missing"]:
        state, reasons = "not_applicable", current["missing"]
    elif record:
        for key in ("definition_sha256", "file_hashes", "argv", "cwd", "executables"):
            if record.get(key) != current[key]:
                reasons.append(key + " changed")
        if record.get("project") != str(root):
            reasons.append("selected project changed")
        state = "stale" if reasons else "current"
    return {
        "case_id": case["id"], "state": state, "reasons": reasons,
        "latest_outcome": record.get("outcome") if record else None,
        "record_path": record.get("record_path") if record else None,
        "recorded_at": record.get("recorded_at") if record else None,
        "scope": case["invariant"],
    }


def save_record(root, results, record):
    # Validate immediately before writing, and use an exclusive unique name.
    local_path(root, results.relative_to(root).as_posix())
    results.mkdir(parents=True, exist_ok=True)
    filename = record["case_id"] + "--" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "--" + uuid.uuid4().hex + ".json"
    path = results / filename
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


def run_check(argv, cwd, timeout):
    """No shell expansion and no raw output retention; not an OS sandbox."""
    process = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=(os.name == "posix"))
    try:
        return process.wait(timeout=timeout), False
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            process.kill()
        process.wait()
        return process.returncode, True


def replay(root, case, results, cases_path):
    # Create the excluded runtime location before observing directory membership.
    # A dependency on the project root must not invalidate itself on first replay.
    results.mkdir(parents=True, exist_ok=True)
    if not os.access(results, os.W_OK):
        raise CaseError("Runtime results directory is not writable")
    snapshot, stamps = inspect_case(root, case, results)
    record = dict(snapshot, version=1, case_id=case["id"], project=str(root),
                  recorded_at=datetime.now(timezone.utc).isoformat(),
                  scope=case["invariant"], returncode=None, duration_seconds=0)
    outcome, summary = "not_applicable", "Prerequisites are missing; the check was not run."
    if not snapshot["missing"]:
        started = time.monotonic()
        try:
            code, timed_out = run_check(snapshot["argv"], snapshot["cwd"], case["check"]["timeout_seconds"])
            record["returncode"] = code
            if timed_out:
                outcome, summary = "inconclusive", "The check exceeded its timeout."
            elif code == 0:
                outcome, summary = "check_passed", "The configured check exited successfully within its declared scope."
            else:
                outcome, summary = "check_failed", "The check returned a nonzero exit status; inspect it before attributing a cause."
        except OSError as exc:
            outcome, summary = "inconclusive", "Could not execute the check (" + type(exc).__name__ + ")."
        record["duration_seconds"] = round(time.monotonic() - started, 3)
        try:
            definitions = load_cases(root, cases_path)
            updated = next((item for item in definitions if item["id"] == case["id"]), None)
            if updated is None:
                raise CaseError("Case definition was removed during the check")
            after, after_stamps = inspect_case(root, updated, results)
            if snapshot != after or stamps != after_stamps:
                outcome, summary = "inconclusive", "Observed inputs changed during the check; this result is not valid evidence."
        except (CaseError, OSError):
            outcome, summary = "inconclusive", "Observed inputs became unavailable or unsafe during the check; this result is not valid evidence."
    record.update(outcome=outcome, summary=summary)
    path = save_record(root, results, record)
    record["record_path"] = str(path)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default=".", help="Selected trusted project root")
    parser.add_argument("--cases", default="docs/knowledge/cases.json", help="Project-relative definitions")
    parser.add_argument("--results-dir", default=".fable/runtime/casebook", help="Project-relative runtime evidence directory")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("list", "search"):
        command = commands.add_parser(name, help="Retrieve lessons without execution")
        command.add_argument("query", nargs="?", default="")
    for name in ("show", "replay"):
        command = commands.add_parser(name)
        command.add_argument("case_id")
    commands.add_parser("status").add_argument("case_id", nargs="?")
    args = parser.parse_args(argv)
    try:
        root = Path(args.project).resolve()
        if not root.is_dir():
            raise CaseError("Selected project must be an existing directory")
        results = local_path(root, args.results_dir)
        if results == root:
            raise CaseError("Runtime results must use a subdirectory")
        cases = load_cases(root, args.cases)
        if args.command in ("list", "search"):
            terms = args.query.casefold().split()
            selected = [c for c in cases if all(t in canonical(c).casefold() for t in terms)]
            answer = [{key: case[key] for key in ("id", "title", "lesson", "tags", "applicability")} for case in selected]
        else:
            selected = [case for case in cases if not args.case_id or case["id"] == args.case_id]
            if args.case_id and not selected:
                raise CaseError("Unknown case: " + args.case_id)
            if args.command == "status":
                answer = [status(root, case, results) for case in selected]
            elif args.command == "show":
                snapshot, _ = inspect_case(root, selected[0], results)
                answer = {"case": selected[0], "preview": snapshot,
                          "execution_note": "Replay executes trusted project code with inherited permissions and environment. No isolation is provided."}
            else:
                answer = replay(root, selected[0], results, args.cases)
        print(json.dumps(answer, indent=2, sort_keys=True))
        if args.command == "replay":
            return {"check_passed": 0, "check_failed": 1, "not_applicable": 3, "inconclusive": 3}[answer["outcome"]]
        return 0
    except (CaseError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
