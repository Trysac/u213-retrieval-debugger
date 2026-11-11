# Testing

## Running

```sh
python -m pytest tests/test_retrieval_debugger.py
```

## Policy

- Tests use `pytest` and import the public package as `retrieval_debugger`.
- Assertions cover return values (`rank`, `in_top_k`, `gap_to_cutoff`, term
  statuses, positions, `beyond_chunk`, `reasons`) and exact rendered strings.
- Limit tests assert `DebugError.code` for `input_too_large`, `invalid_k` and
  `invalid_ranking`.
- Tests are deterministic: no network, no wall clock and no dependence on test
  order.

## Tiers

The repository contains one local test tier. There are no conformance markers,
CI-only tests or external tool downloads in the provided test tree.

## Layout

`tests/test_retrieval_debugger.py` contains:

- `test_acceptance_below_cutoff`: rank 2 against `k=1`, `gap_to_cutoff == 0.7`,
  exact terms and `reasons == ('below_cutoff',)`.
- `test_acceptance_stem_mismatch`: `install packages` against
  `How to installing a package` yields stem status and `stem_mismatch` without
  a ranking.
- `test_acceptance_accent_mismatch`: `café` against `Cafe menu` yields accent
  status and `accent_mismatch`.
- `test_acceptance_accent_escape_literal`: the same accent behavior with the
  escaped `caf\u00e9` literal.
- `test_acceptance_not_in_ranking_and_missing`: an absent document with missing
  terms yields `not_in_ranking` then `missing_terms`.
- `test_acceptance_beyond_chunk`: a term at position 32 with `chunk_chars=20`
  reports `beyond_chunk` and `term_beyond_chunk`.
- `test_acceptance_render`: exact multi-line output from `render`.
- `test_acceptance_limits`: 1,000,001-character document and 1,001-character
  query raise `input_too_large`; `k=0` raises `invalid_k`; a duplicate ranking
  ID raises `invalid_ranking`.
- `test_rank_exactly_at_cutoff`: a document at rank `k` has `in_top_k` true,
  `gap_to_cutoff` `None` and no `below_cutoff` reason.
- `test_term_exact_wins_over_stem`: exact status takes precedence when both
  exact and stem matches exist.
- `test_accent_then_stem_precedence`: `Cafés` against `cafe` exercises accent
  matching before stemming.
