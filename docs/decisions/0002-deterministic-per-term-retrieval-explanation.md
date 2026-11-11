# Deterministic per-term retrieval explanation

Status: accepted (generated, pending human review)

## Context

RAG engineers need to understand individual misses. The library must provide actionable, deterministic explanations for one query-document pair without re-running retrievers. It must be dependency-free and implement tokenization, term matching (exact, accent, stem), ranking analysis, and chunk boundary detection.

## Decision

Implement the utility as a pure Python package using only the standard library. Tokenize by maximal runs of `str.isalnum`; query terms are casefolded and deduplicated. Matching proceeds in order: exact, accent (diacritic folding), stem (light English stemming). Ranking is assumed already sorted by score descending; ties keep input order. The `Explanation` dataclass includes a private `_k` field to store the cutoff for rendering, as the rendering function requires it.

## Consequences

The library is simple and predictable, with no external dependencies. The deviation of adding `_k` is documented. Future extensions (embedding similarity, other languages) are explicitly out of scope.
