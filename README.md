# retrieval-debugger

[![PyPI version](https://img.shields.io/pypi/v/trysac-retrieval-debugger)](https://pypi.org/project/trysac-retrieval-debugger/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-retrieval-debugger)](LICENSE)
[![CI](https://github.com/Trysac/u213-retrieval-debugger/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u213-retrieval-debugger/actions/workflows/ci.yml)

Explain why a document was or was not retrieved for a query: its rank against the cutoff, per-term exact, accent and stem matches, missing terms and terms cut off by chunking

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-retrieval-debugger
# or
uv add trysac-retrieval-debugger
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import retrieval_debugger

# normalize() trims surrounding whitespace and lower-cases the text.
print(retrieval_debugger.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    retrieval_debugger.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
