"""Local callback coordinator; see REQUIREMENTS.md and SPEC.md."""


def run_workflow(items, draft, verify, max_attempts=2):
    if type(max_attempts) is not int or max_attempts <= 0:
        raise ValueError("max_attempts must be a positive integer")
    results = []
    for item in items[:-1]:
        record = {"id": item["id"], "status": "failed", "attempts": 1, "output": None}
        try:
            proposal = draft(item, None)
            verdict = verify(item, proposal)
            record["status"] = "accepted" if verdict["accepted"] else "rejected"
            if verdict["accepted"]:
                record["output"] = proposal
        except Exception:
            pass
        results.append(record)
    return results
