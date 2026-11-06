"""Behavior tests for the offline ticket agent."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from ticket_agent import CONFIDENCE_THRESHOLD, answer_ticket
from ticket_agent.agent import CONFIDENCE_THRESHOLD as AGENT_THRESHOLD
from ticket_agent.models import Ticket

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "tickets"
OTHER_ARTICLE_FACT = "A reset link expires after 15 minutes."


def load_ticket(name: str) -> Ticket:
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return Ticket(
        id=payload["id"],
        subject=payload["subject"],
        body=payload["body"],
        requester_email=payload["requester_email"],
    )


def test_refund_ticket_answers_and_cites_refund_doc():
    result = answer_ticket(load_ticket("refund.json"))
    assert result.action == "answer"
    assert result.answer
    assert result.escalation is None
    assert result.confidence >= CONFIDENCE_THRESHOLD
    assert result.citations
    assert all(item.source == "corpus/refunds.md" for item in result.citations)
    assert "30 days" in result.answer
    assert "original payment method" in result.answer


def test_answer_quotes_only_the_refund_article():
    result = answer_ticket(load_ticket("refund.json"))
    refund_text = (ROOT / "corpus" / "refunds.md").read_text(encoding="utf-8")
    assert result.answer is not None
    for line in result.answer.splitlines():
        heading, sentence = line.split(": ", 1)
        assert heading in refund_text
        assert sentence in refund_text


def test_answer_omits_fact_that_exists_only_in_password_article():
    result = answer_ticket(load_ticket("refund.json"))
    holders = [
        path.name
        for path in (ROOT / "corpus").glob("*.md")
        if OTHER_ARTICLE_FACT in path.read_text(encoding="utf-8")
    ]
    assert holders == ["password-reset.md"]
    assert result.answer is not None
    assert OTHER_ARTICLE_FACT not in result.answer
    assert "KESTREL-BACKUP" not in result.answer
    assert all("password-reset" not in item.source for item in result.citations)


def test_wifi_ticket_escalates():
    result = answer_ticket(load_ticket("wifi.json"))
    assert result.action == "escalate"
    assert result.answer is None
    assert result.escalation is not None
    assert result.escalation.reason in {"low_confidence", "empty_corpus_match"}
    assert result.escalation.queue == "human_support"
    assert result.escalation.reason == "empty_corpus_match"
    assert result.citations == ()
    assert result.confidence == 0


def test_weak_overlap_escalates_low_confidence():
    result = answer_ticket(load_ticket("weak-overlap.json"))
    assert result.action == "escalate"
    assert result.answer is None
    assert result.escalation is not None
    assert result.escalation.reason == "low_confidence"
    assert result.escalation.queue == "human_support"
    assert 0 < result.confidence < CONFIDENCE_THRESHOLD
    assert result.citations
    assert all(item.score < CONFIDENCE_THRESHOLD for item in result.citations)
    assert any("shipping" in item.source for item in result.citations)


def test_invalid_email_escalates_without_answering():
    result = answer_ticket(load_ticket("invalid-email.json"))
    assert result.action == "escalate"
    assert result.answer is None
    assert result.citations == ()
    assert result.escalation is not None
    assert result.escalation.reason == "invalid_requester"
    assert result.escalation.queue == "human_support"
    assert "30 days" not in (result.answer or "")


def test_threshold_constant_matches_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"CONFIDENCE_THRESHOLD is ([0-9]+(?:\.[0-9]+)?)", readme)
    assert match is not None
    assert CONFIDENCE_THRESHOLD == float(match.group(1))
    assert AGENT_THRESHOLD == CONFIDENCE_THRESHOLD
    assert CONFIDENCE_THRESHOLD == 0.18


def test_cli_refund_and_wifi_json():
    for name, action in (("refund.json", "answer"), ("wifi.json", "escalate")):
        completed = subprocess.run(
            [sys.executable, "-m", "ticket_agent"],
            input=(FIXTURES / name).read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["action"] == action
        assert "escalation" in payload
        assert "citations" in payload
