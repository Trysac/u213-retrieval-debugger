# trysac-retrieval-debugger

[![PyPI version](https://img.shields.io/pypi/v/trysac-retrieval-debugger)](https://pypi.org/project/trysac-retrieval-debugger/)
[![Python versions](https://img.shields.io/pypi/pyversions/trysac-retrieval-debugger)](https://pypi.org/project/trysac-retrieval-debugger/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Explain why one document was or was not retrieved for a query. For a single
query-document pair the library reports the document's rank against a cutoff,
per-term exact, accent and stem matches, missing terms, and terms whose every
occurrence lies at or beyond a chunk boundary. The output is deterministic and
uses fixed reason codes.

## Installation

```bash
pip install trysac-retrieval-debugger
```

The import name is `retrieval_debugger`. Python >= 3.10 is required. The
package has no runtime third-party dependencies.

## Usage

```python
from retrieval_debugger import explain, render

e = explain(
    "Running shoes",
    "I bought running shoes yesterday.",
    doc_id="d1",
    ranking=[("d0", 3.2), ("d1", 2.5)],
    k=1,
)
print(render(e))
```

Output:

```text
doc d1: rank 2, cutoff k=1, below cutoff by 0.7
running: exact
shoes: exact
reasons: below_cutoff
```

## API

- `explain(query: str, document: str, *, doc_id: str, ranking: Sequence[tuple[str, float]] | None = None, k: int = 10, chunk_chars: int | None = None) -> Explanation`
  Tokenizes `query` and `document` into maximal runs of `str.isalnum`
  characters. Query terms are casefolded, deduplicated in first-seen order and
  limited to 64. For each term the first applicable status is `exact`
  (casefolded equality), `accent` (equality after NFD diacritic folding),
  `stem` (equality after folding and stripping the first matching suffix among
  `ing`, `ed`, `s` when at least 3 characters remain) or `missing`. Positions
  are the start offsets of up to 10 matching document tokens, ascending.
  `beyond_chunk` is true when `chunk_chars` is set and every captured position
  is `>= chunk_chars`. With `ranking`, `rank` is the 1-based index of `doc_id`,
  `in_top_k` is `rank <= k`, and `gap_to_cutoff` is
  `round(score_of_kth_entry - doc_score, 6)` when the document is below the
  cutoff; otherwise both are `None`. Without `ranking`, rank fields are `None`.
  Reasons are emitted in this fixed order, each at most once:
  `not_in_ranking`, `below_cutoff`, `missing_terms`, `accent_mismatch`,
  `stem_mismatch`, `term_beyond_chunk`.
- `render(e: Explanation) -> str` returns the human-readable form. The first
  line is `doc <id>: rank <r>, cutoff k=<k>` (plus `, below cutoff by <gap>`
  when below), `doc <id>: not in ranking, cutoff k=<k>`, or
  `doc <id>: no ranking`. Then one `<term>: <status>` line per term, with
  ` (beyond chunk)` when applicable. The last line is `reasons: ` followed by
  the comma-separated reason codes or `none`.
- `Explanation` is a frozen dataclass with `doc_id`, `rank`, `in_top_k`,
  `gap_to_cutoff`, `terms` and `reasons`. It also carries a private `_k`
  field that stores the cutoff for rendering; `explain()` sets it and direct
  construction defaults it to 10.
- `TermMatch` is a frozen dataclass with `term`, `status` (`exact`, `accent`,
  `stem`, `missing`), `positions` and `beyond_chunk`.
- `DebugError` has a `code` attribute: `input_too_large`, `invalid_k` or
  `invalid_ranking`. Its message is `retrieval-debugger error: <code>`.

Options: `ranking` is a sequence of `(doc_id, score)` tuples used in the order
given; scores must be finite. `k` is the cutoff rank (default 10). `chunk_chars`
opts into chunk-boundary reporting.

## Limits

- Query: at most 1,000 characters; document: at most 1,000,000 characters.
- Ranking: at most 10,000 entries, each a `(str, int|float)` tuple with a
  finite score and no duplicate document IDs.
- Cutoff `k`: 1 to 10,000 inclusive.
- Query terms: at most 64 after casefolding and deduplication.
- Reported match positions: at most 10 per term.

## Why not retrieval metrics

Retrieval metrics such as recall@k, MRR or nDCG aggregate results over a query
set and report that a miss happened. This utility explains one miss for one
document in terms an engineer can act on: which query term failed and how
(exact, accent, stem or missing), whether every occurrence of the term lies
beyond the configured chunk boundary, and how far the document is below the
cutoff. It does not compute or replace retrieval metrics.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and the limits
enforced by the code.

## Development

Run the tests with `python -m pytest tests/test_retrieval_debugger.py`.
