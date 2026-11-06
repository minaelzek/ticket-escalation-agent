"""Chunk local markdown and score it by normalized token overlap."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ticket_agent.tokenize import tokenize

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Chunk:
    source: str
    heading: str
    text: str
    tokens: frozenset[str]


@dataclass(frozen=True)
class ScoredChunk:
    source: str
    heading: str
    text: str
    score: float


def overlap_score(query: set[str], chunk_tokens: frozenset[str]) -> float:
    """|query ∩ chunk| / |query|, rounded to 4 decimals. 0 when nothing overlaps."""
    if not query:
        return 0.0
    overlap = len(query & chunk_tokens)
    if overlap == 0:
        return 0.0
    return round(overlap / len(query), 4)


def chunk_markdown(source: str, text: str) -> list[Chunk]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return []
    matches = list(_HEADING_RE.finditer(normalized))
    sections: list[tuple[str, str]] = []
    if not matches:
        sections.append(("Introduction", normalized))
    else:
        if matches[0].start() > 0:
            preamble = normalized[: matches[0].start()].strip()
            if preamble:
                sections.append(("Introduction", preamble))
        for index, match in enumerate(matches):
            heading = match.group(2).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized)
            body = normalized[start:end].strip()
            if body:
                sections.append((heading, body))

    chunks: list[Chunk] = []
    for heading, body in sections:
        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", body) if part.strip()]
        for paragraph in paragraphs:
            flat = " ".join(paragraph.split())
            chunks.append(
                Chunk(
                    source=source,
                    heading=heading,
                    text=flat,
                    tokens=frozenset(tokenize(f"{heading}\n{flat}")),
                )
            )
    return chunks


def load_chunks(root: Path | None = None) -> list[Chunk]:
    project_root = PROJECT_ROOT if root is None else root
    corpus_dir = project_root / "corpus"
    if not corpus_dir.is_dir():
        return []
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.glob("*.md")):
        source = path.relative_to(project_root).as_posix()
        chunks.extend(chunk_markdown(source, path.read_text(encoding="utf-8")))
    return chunks


def rank_chunks(query: set[str], chunks: list[Chunk]) -> list[ScoredChunk]:
    scored = [
        ScoredChunk(
            source=chunk.source,
            heading=chunk.heading,
            text=chunk.text,
            score=overlap_score(query, chunk.tokens),
        )
        for chunk in chunks
    ]
    scored.sort(key=lambda item: (-item.score, item.source, item.heading, item.text))
    return scored
