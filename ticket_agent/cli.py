"""Read one ticket JSON document from stdin and print an AgentResult."""

from __future__ import annotations

import json
import sys

from ticket_agent.agent import answer_ticket
from ticket_agent.models import ticket_from_mapping


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("ticket must be a JSON object", file=sys.stderr)
        return 2
    try:
        ticket = ticket_from_mapping(data)
    except (KeyError, TypeError, ValueError) as exc:
        print(f"invalid ticket: {exc}", file=sys.stderr)
        return 2
    json.dump(answer_ticket(ticket).to_dict(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0
