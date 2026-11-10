# Architecture

## Purpose

`trysac-retrieval-debugger` is a dependency-free Python library that explains
why one document was or was not retrieved for one query. It reports rank
against a cutoff, per-term exact, accent and stem matches, missing terms, terms
beyond a chunk boundary, and fixed reason codes.

## Shape

```text
caller code --> retrieval_debugger (public API in __init__.py)
                    |
                    +-- pure functions, no I/O, no global mutable state
```

- **Public API**: the names in `__all__` of
  `src/retrieval_debugger/__init__.py`: `DebugError`, `Explanation`,
  `TermMatch`, `explain`, `render`.
- **Errors**: invalid input raises `DebugError` with one of the codes
  `input_too_large`, `invalid_k` or `invalid_ranking`. The library does not
  print or exit.
- **Side effects**: none beyond defensive logging setup. The module defines a
  logger with `logging.NullHandler` and emits no records. No file, network,
  subprocess or database access occurs.
- **Data**: `Explanation` and `TermMatch` are frozen dataclasses. `Explanation`
  has a private `_k` field set by `explain()` and defaulting to 10 for direct
  construction.

## Quality contract

The provided tree contains the package in `src/retrieval_debugger/` and one test
module, `tests/test_retrieval_debugger.py`. There is no separate quality script
in the provided tree.

## Decisions

No architecture decision records are present in the provided repository.
