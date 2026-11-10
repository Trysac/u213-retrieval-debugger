"""Explain why a document was or was not retrieved for a query.

The module provides a deterministic, per-term explanation for one query and
one document. It reports the document's rank against a cutoff, per-term
exact, accent and stem matches, missing terms, and terms cut off by chunking.
"""

from __future__ import annotations

import logging
import math
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "DebugError",
    "Explanation",
    "TermMatch",
    "explain",
    "render",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Limits
MAX_QUERY_CHARS = 1_000
MAX_DOC_CHARS = 1_000_000
MAX_RANKING_ENTRIES = 10_000
MIN_K = 1
MAX_K = 10_000
MAX_QUERY_TERMS = 64
MAX_POSITIONS = 10

# Stemming suffixes in order of preference
_STEM_SUFFIXES = ("ing", "ed", "s")


class DebugError(Exception):
    """Error raised by the retrieval debugger.

    Attributes:
        code: A machine-readable code indicating the error type.
    """

    def __init__(self, code: Literal["input_too_large", "invalid_k", "invalid_ranking"]) -> None:
        super().__init__(f"retrieval-debugger error: {code}")
        self.code = code


@dataclass(frozen=True)
class TermMatch:
    """Matching outcome for a single query term."""

    term: str
    status: Literal["exact", "accent", "stem", "missing"]
    positions: tuple[int, ...]
    beyond_chunk: bool


@dataclass(frozen=True)
class Explanation:
    """Explanation for one query-document pair.

    The ``_k`` field stores the cutoff value used during rendering. It is
    private and defaults to 10 for direct construction; ``explain()`` sets it.
    """

    doc_id: str
    rank: int | None
    in_top_k: bool | None
    gap_to_cutoff: float | None
    terms: tuple[TermMatch, ...]
    reasons: tuple[str, ...]
    _k: int = field(default=10, repr=False, compare=False)


def _tokenize(text: str) -> list[tuple[str, int]]:
    """Return maximal runs of ``str.isalnum`` characters with start offsets."""
    tokens: list[tuple[str, int]] = []
    start: int | None = None
    for i, ch in enumerate(text):
        if ch.isalnum():
            if start is None:
                start = i
        else:
            if start is not None:
                tokens.append((text[start:i], start))
                start = None
    if start is not None:
        tokens.append((text[start:], start))
    return tokens


def _fold_diacritics(s: str) -> str:
    """Normalize to NFD and drop combining marks."""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")


def _stem(s: str) -> str:
    """Apply light English stemming.

    Strips the first matching suffix among ``'ing'``, ``'ed'`` and ``'s'``
    when at least 3 characters remain.
    """
    for suffix in _STEM_SUFFIXES:
        if s.endswith(suffix) and len(s) - len(suffix) >= 3:
            return s[: -len(suffix)]
    return s


def _match_term(
    term: str, doc_tokens: list[tuple[str, int]]
) -> tuple[Literal["exact", "accent", "stem", "missing"], tuple[int, ...]]:
    """Return (status, positions) for a single query term against document tokens."""
    # Exact: casefolded equality
    positions = [pos for token, pos in doc_tokens if token.casefold() == term]
    if positions:
        positions.sort()
        return "exact", tuple(positions[:MAX_POSITIONS])

    folded_term = _fold_diacritics(term)

    # Accent: equality after diacritic folding
    positions = [
        pos for token, pos in doc_tokens if _fold_diacritics(token.casefold()) == folded_term
    ]
    if positions:
        positions.sort()
        return "accent", tuple(positions[:MAX_POSITIONS])

    # Stem: equality after folding and stemming
    stemmed_term = _stem(folded_term)
    positions = [
        pos
        for token, pos in doc_tokens
        if _stem(_fold_diacritics(token.casefold())) == stemmed_term
    ]
    if positions:
        positions.sort()
        return "stem", tuple(positions[:MAX_POSITIONS])

    return "missing", ()


def explain(
    query: str,
    document: str,
    *,
    doc_id: str,
    ranking: Sequence[tuple[str, float]] | None = None,
    k: int = 10,
    chunk_chars: int | None = None,
) -> Explanation:
    """Produce an explanation for one query-document pair.

    Args:
        query: The query string (max 1,000 characters).
        document: The document string (max 1,000,000 characters).
        doc_id: Identifier of the document.
        ranking: Optional sequence of ``(doc_id, score)`` pairs sorted by
            score descending; ties keep input order. Max 10,000 entries, all
            scores finite.
        k: The cutoff rank (1 to 10,000 inclusive). Defaults to 10.
        chunk_chars: If set, triggers ``beyond_chunk`` flags for terms whose
            every position is at or beyond this offset.

    Returns:
        An :class:`Explanation` object.

    Raises:
        DebugError: If an input violates the documented limits. Codes:
            - ``input_too_large``: query or document exceeds size limits.
            - ``invalid_k``: k is outside the allowed range.
            - ``invalid_ranking``: ranking is malformed or exceeds limits.
    """
    # Validate inputs
    if len(query) > MAX_QUERY_CHARS:
        raise DebugError("input_too_large")
    if len(document) > MAX_DOC_CHARS:
        raise DebugError("input_too_large")
    if k < MIN_K or k > MAX_K:
        raise DebugError("invalid_k")
    if ranking is not None:
        if len(ranking) > MAX_RANKING_ENTRIES:
            raise DebugError("invalid_ranking")
        seen_ids: set[str] = set()
        for entry in ranking:
            if not isinstance(entry, tuple) or len(entry) != 2:
                raise DebugError("invalid_ranking")
            doc_id_rank, score = entry
            if (
                not isinstance(doc_id_rank, str)
                or not isinstance(score, (int, float))
                or not math.isfinite(score)
            ):
                raise DebugError("invalid_ranking")
            if doc_id_rank in seen_ids:
                raise DebugError("invalid_ranking")
            seen_ids.add(doc_id_rank)

    # Tokenize document and query terms
    doc_tokens = _tokenize(document)
    query_tokens = [token for token, _ in _tokenize(query)]
    query_terms: list[str] = []
    seen_terms: set[str] = set()
    for token in query_tokens:
        casefolded = token.casefold()
        if casefolded not in seen_terms:
            seen_terms.add(casefolded)
            query_terms.append(casefolded)
            if len(query_terms) >= MAX_QUERY_TERMS:
                break

    # Match each query term
    term_matches = []
    for term in query_terms:
        status, positions = _match_term(term, doc_tokens)
        beyond = False
        if chunk_chars is not None and status != "missing":
            beyond = all(pos >= chunk_chars for pos in positions) if positions else False
        term_matches.append(
            TermMatch(term=term, status=status, positions=positions, beyond_chunk=beyond)
        )

    # Ranking information
    rank: int | None = None
    in_top_k: bool | None = None
    gap: float | None = None
    if ranking is not None:
        for idx, (doc_id_rank, score) in enumerate(ranking):
            if doc_id_rank == doc_id:
                rank = idx + 1
                doc_score = score
                break
        if rank is not None:
            in_top_k = rank <= k
            if not in_top_k:
                # rank > k; get score of the k-th entry
                kth_score = ranking[k - 1][1]
                gap = round(kth_score - doc_score, 6)

    # Reasons in fixed order
    reasons: list[str] = []
    if ranking is not None and rank is None:
        reasons.append("not_in_ranking")
    if rank is not None and rank > k:
        reasons.append("below_cutoff")
    if any(tm.status == "missing" for tm in term_matches):
        reasons.append("missing_terms")
    if any(tm.status == "accent" for tm in term_matches):
        reasons.append("accent_mismatch")
    if any(tm.status == "stem" for tm in term_matches):
        reasons.append("stem_mismatch")
    if any(tm.beyond_chunk for tm in term_matches):
        reasons.append("term_beyond_chunk")

    return Explanation(
        doc_id=doc_id,
        rank=rank,
        in_top_k=in_top_k,
        gap_to_cutoff=gap,
        terms=tuple(term_matches),
        reasons=tuple(reasons),
        _k=k,
    )


def render(e: Explanation) -> str:
    """Return a human-readable string representation of an explanation."""
    lines: list[str] = []
    if e.rank is None:
        if "not_in_ranking" in e.reasons:
            lines.append(f"doc {e.doc_id}: not in ranking, cutoff k={e._k}")
        else:
            lines.append(f"doc {e.doc_id}: no ranking")
    else:
        line = f"doc {e.doc_id}: rank {e.rank}, cutoff k={e._k}"
        if e.rank > e._k:
            line += f", below cutoff by {e.gap_to_cutoff!r}"
        lines.append(line)

    for tm in e.terms:
        line = f"{tm.term}: {tm.status}"
        if tm.beyond_chunk:
            line += " (beyond chunk)"
        lines.append(line)

    reasons_str = ", ".join(e.reasons) if e.reasons else "none"
    lines.append(f"reasons: {reasons_str}")
    return "\n".join(lines)
