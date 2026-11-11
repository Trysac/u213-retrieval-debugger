# Project record

## Objective

Explain why a document was or was not retrieved for a query: its rank against
the cutoff, per-term exact, accent and stem matches, missing terms, and terms
cut off by chunking. The explanation is deterministic, per-term and uses stable
reason codes for one query-document pair.

## Scope

In scope:

- The public API `explain`, `render`, `Explanation`, `TermMatch` and
  `DebugError` in `retrieval_debugger`.
- Casefolded tokenization of the query and document into maximal runs of
  `str.isalnum` characters with character offsets.
- Per-term status in precedence order: exact, accent (NFD diacritic folding),
  stem (light English suffixes `ing`, `ed`, `s`) and missing.
- Up to 10 ascending match positions per term and `beyond_chunk` reporting
  when `chunk_chars` is supplied.
- Rank, `in_top_k` and `gap_to_cutoff` from a caller-supplied ranking and
  cutoff `k`.
- Reason codes in fixed order and the `render` text format.
- Input validation limits: query length, document length, ranking size and
  shape, finite scores, unique document IDs, and `k` range.

Out of scope:

- Embedding similarity explanations or any model internals.
- Re-running a retriever or computing retrieval metrics.
- Languages other than English for stemming.
- I/O, network access, persistence, configuration files and runtime
  third-party dependencies.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 527620 / 54548 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.0835 |

## Factory run u213 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1576 | 17348 | 0 | 3328 | 0.0355 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 8747 | 1180 | 0 | 54528 | 0.0022 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 6101 | 942 | 0 | 19840 | 0.0015 |
| 2026-11-10 | audit | deepseek-flash | no | 30533 | 21733 | 0 | 283648 | 0.0185 |
| 2026-11-10 | docs | deepseek-flash | no | 119063 | 13345 | 0 | 256 | 0.0259 |

Total: $0.0835. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
