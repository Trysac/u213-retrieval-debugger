# Security notes

## Threat model

`trysac-retrieval-debugger` is a pure Python library. It performs no network,
file, subprocess or database I/O, and it contains no `eval`, `exec`,
deserialization or credential handling.

Defended:

- Oversized inputs: `query` above 1,000 characters or `document` above
  1,000,000 characters raises `DebugError('input_too_large')`.
- Invalid cutoff: `k` outside 1 to 10,000 raises `DebugError('invalid_k')`.
- Invalid ranking: more than 10,000 entries, non-tuple entries, wrong tuple
  length, non-string document IDs, non-finite or non-numeric scores, or
  duplicate document IDs raise `DebugError('invalid_ranking')`.
- Unbounded term work: query terms are deduplicated and capped at 64; match
  positions are capped at 10 per term.
- Non-determinism: matching uses casefolding, NFD diacritic folding and a fixed
  suffix list (`ing`, `ed`, `s` with at least 3 characters remaining). There is
  no randomness, clock use or external state.
- Error surface: validation failures raise the library's `DebugError` with a
  fixed code; the library does not print or exit.
- Logging: the module defines a logger with `logging.NullHandler` and emits no
  log records.

Not defended:

- The library does not sanitize, escape or quote `query`, `document`, `doc_id`,
  term strings or reason strings for display. `render` includes `doc_id` and
  matched terms verbatim.
- It does not verify that a supplied `ranking` is actually sorted by score
  descending; it trusts the caller's order.
- It does not impose CPU or memory quotas beyond the character, entry, term and
  position limits. A 1,000,000-character document and 64 query terms can still
  be expensive to process.
- It does not authenticate or authorize callers; it is a library, not a
  service.
- Stemming is English-only and is not a security control.

## Publishing

The library contains no publishing or credential-handling code. Distribution
to package indexes is handled outside this code.
