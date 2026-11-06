"""Ticket and agent result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Ticket:
    id: str
    subject: str
    body: str
    requester_email: str


@dataclass(frozen=True)
class Citation:
    source: str
    heading: str
    score: float


@dataclass(frozen=True)
class Escalation:
    reason: str
    missing_evidence: str
    queue: str


@dataclass(frozen=True)
class AgentResult:
    action: str
    answer: str | None
    citations: tuple[Citation, ...]
    confidence: float
    escalation: Escalation | None

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "answer": self.answer,
            "citations": [
                {"source": item.source, "heading": item.heading, "score": item.score}
                for item in self.citations
            ],
            "confidence": self.confidence,
            "escalation": None
            if self.escalation is None
            else {
                "reason": self.escalation.reason,
                "missing_evidence": self.escalation.missing_evidence,
                "queue": self.escalation.queue,
            },
        }


def ticket_from_mapping(data: dict) -> Ticket:
    required = ("id", "subject", "body", "requester_email")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing fields: " + ", ".join(missing))
    values: list[str] = []
    for key in required:
        value = data[key]
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
        values.append(value)
    return Ticket(*values)
