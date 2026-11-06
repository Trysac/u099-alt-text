# alt-text

[![PyPI version](https://img.shields.io/pypi/v/trysac-alt-text)](https://pypi.org/project/trysac-alt-text/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-alt-text)](LICENSE)
[![CI](https://github.com/Trysac/u099-alt-text/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u099-alt-text/actions/workflows/ci.yml)

Lint and generate image alt text following WCAG 2.2 and the WAI alt decision tree, with HTML scanning and a vision LLM port

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-alt-text
# or
uv add trysac-alt-text
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import alt_text

# normalize() trims surrounding whitespace and lower-cases the text.
print(alt_text.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    alt_text.normalize("   ")
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
