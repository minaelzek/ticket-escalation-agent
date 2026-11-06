"""Decide whether a ticket can be answered from the local help center."""

from __future__ import annotations

import re

from ticket_agent.models import AgentResult, Citation, Escalation, Ticket
from ticket_agent.retrieve import rank_chunks, load_chunks
from ticket_agent.tokenize import tokenize

# Best normalized token overlap required before the agent may answer.
CONFIDENCE_THRESHOLD = 0.18
MAX_SUPPORTING_CHUNKS = 3
HUMAN_SUPPORT_QUEUE = "human_support"

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    if not value or any(character.isspace() for character in value):
        return False
    return _EMAIL_RE.fullmatch(value) is not None


def _citation(source: str, heading: str, score: float) -> Citation:
    return Citation(source=source, heading=heading, score=score)


def _render_answer(chunks: list) -> str:
    # Quote chunk text only. Do not add policy that is not in those chunks.
    return "\n".join(f"{chunk.heading}: {chunk.text}" for chunk in chunks)


def answer_ticket(ticket: Ticket) -> AgentResult:
    # Invalid addresses never receive a corpus answer.
    if not is_valid_email(ticket.requester_email):
        return AgentResult(
            action="escalate",
            answer=None,
            citations=(),
            confidence=0.0,
            escalation=Escalation(
                reason="invalid_requester",
                missing_evidence="The requester email is invalid, so no answer was generated.",
                queue=HUMAN_SUPPORT_QUEUE,
            ),
        )

    query = tokenize(f"{ticket.subject}\n{ticket.body}")
    ranked = rank_chunks(query, load_chunks())
    best = ranked[0].score if ranked else 0.0
    selected = [item for item in ranked if item.score >= CONFIDENCE_THRESHOLD][:MAX_SUPPORTING_CHUNKS]

    if best >= CONFIDENCE_THRESHOLD and selected:
        return AgentResult(
            action="answer",
            answer=_render_answer(selected),
            citations=tuple(_citation(item.source, item.heading, item.score) for item in selected),
            confidence=best,
            escalation=None,
        )

    if best == 0:
        reason = "empty_corpus_match"
        missing = "No help-center chunk shares tokens with the ticket subject and body."
        weak: list = []
    else:
        reason = "low_confidence"
        missing = (
            f"Best overlap score {best} is below CONFIDENCE_THRESHOLD {CONFIDENCE_THRESHOLD}."
        )
        weak = [item for item in ranked if item.score > 0][:MAX_SUPPORTING_CHUNKS]

    return AgentResult(
        action="escalate",
        answer=None,
        citations=tuple(_citation(item.source, item.heading, item.score) for item in weak),
        confidence=best,
        escalation=Escalation(
            reason=reason,
            missing_evidence=missing,
            queue=HUMAN_SUPPORT_QUEUE,
        ),
    )
