"""Whole-cent order pricing under the local policy."""

import json
from pathlib import Path


def quote(subtotal_cents):
    policy = json.loads(Path(__file__).with_name("policy.json").read_text())
    if subtotal_cents > policy["minimum_subtotal_cents"]:
        return subtotal_cents * (100 - policy["discount_percent"]) // 100
    return subtotal_cents
