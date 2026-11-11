# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | The code uses `from __future__ import annotations`, PEP 604 union types, `Literal` and frozen dataclasses. |
| Python standard library | The implementation imports `logging`, `math`, `unicodedata`, `collections.abc`, `dataclasses` and `typing`. No third-party runtime dependencies are used. |
| pytest | The test module `tests/test_retrieval_debugger.py` uses pytest assertions and `pytest.raises`. |
| `py.typed` | The package ships `src/retrieval_debugger/py.typed` for PEP 561 typing. |

## Discarded

| Tool | Why not |
|---|---|
| Third-party runtime libraries | The package is stdlib-only. |
| Non-English stemmers | The implementation strips only `ing`, `ed` and `s` for light English stemming. |
| Embedding models or vector stores | Out of scope; the library explains supplied text and rankings. |
