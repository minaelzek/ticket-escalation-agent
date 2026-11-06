"""Deterministic token overlap helpers. No stemming and no network."""

from __future__ import annotations

import re

MIN_TOKEN_LENGTH = 3

# Function words only. Content words stay so scores are explainable.
STOPWORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "you",
        "your",
        "our",
        "are",
        "was",
        "were",
        "can",
        "not",
        "but",
        "with",
        "from",
        "this",
        "that",
        "have",
        "has",
        "had",
        "what",
        "when",
        "where",
        "who",
        "why",
        "how",
        "please",
        "about",
        "into",
        "than",
        "then",
        "there",
        "their",
        "they",
        "them",
        "been",
        "will",
        "would",
        "could",
        "should",
        "any",
        "all",
        "also",
        "more",
        "some",
        "such",
        "only",
        "other",
        "which",
        "while",
        "after",
        "before",
        "does",
        "did",
        "its",
        "let",
        "just",
        "out",
        "off",
        "too",
        "very",
        "here",
        "because",
        "each",
        "may",
        "must",
        "during",
        "within",
        "once",
        "over",
        "under",
        "back",
        "via",
        "per",
        "onto",
        "inside",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for token in _TOKEN_RE.findall(text.lower()):
        if len(token) < MIN_TOKEN_LENGTH or token in STOPWORDS:
            continue
        tokens.add(token)
    return tokens
