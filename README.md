# alt-text

[![PyPI version](https://img.shields.io/pypi/v/trysac-alt-text)](https://pypi.org/project/trysac-alt-text/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-alt-text)](LICENSE)
[![CI](https://github.com/Trysac/u099-alt-text/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u099-alt-text/actions/workflows/ci.yml)

Lint and generate image alt text following WCAG 2.2 and the WAI alt decision tree, with HTML scanning and a vision LLM port.

## Problem

Images ship with missing alt attributes, filenames as alt text or captions starting with "image of", which fail WCAG 2.2 success criterion 1.1.1 and help nobody. axe-core flags a missing alt but cannot judge or write good text, and raw captioning models ignore the guidance. This library lints alt text, scans HTML and generates guideline-compliant text through a vision LLM port.

## Install

```sh
pip install trysac-alt-text
# or
uv add trysac-alt-text
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from alt_text import lint_alt_text, scan_html

print([i.code for i in lint_alt_text("Image of a dog")])  # ['ALT001']
for finding in scan_html('<img src="a.png">'):
    print(finding.line, finding.missing_alt, [i.code for i in finding.issues])
```

Command line:

```sh
alt-text lint page.html [--format text|json]
alt-text check "Image of a dog" --purpose informative
alt-text generate photo.png --recorded replies.json
```

Exit codes: 0 no findings, 1 findings, 2 usage, I/O or parse error.

## API summary

- `lint_alt_text(alt, *, purpose='informative', filename=None, max_chars=150) -> list[AltIssue]`. Codes ALT001 to ALT008: redundant prefix, over `max_chars`, filename-like, empty for non-decorative, non-empty for decorative, placeholder word, URL, and click-here wording for functional images.
- `scan_html(html, *, max_chars=5_000_000) -> list[ImgFinding]`. Uses `html.parser`, 1-based lines, never fetches images. Raises `AltTextError` (`too_large`) above 10 000 images.
- `read_image_info(data: bytes) -> ImageInfo`. Reads PNG, JPEG, GIF and WebP headers only. Raises `AltTextError` with code `unsupported_image` for other formats, truncated headers or dimensions outside 1..65535.
- `generate_alt_text(image, llm, *, purpose, context='', max_chars=150, max_image_bytes=20_000_000) -> AltTextResult`. Calls a `VisionLLMPort`; a decorative image makes no model call. Context is fenced in `<context>` tags and `</context` sequences are neutralised. Raises `AltTextError` with codes `too_large`, `unsupported_image` or `invalid_reply`.
- `alt_text.llm`: `RecordedLLM` (replays fixed replies, raises `RecordingExhaustedError` when empty) and `FakeLLM` for tests.
- Errors: `AltTextError` with `code` in `unsupported_image`, `too_large`, `invalid_reply`. Messages are cut to 200 characters.
- Limits: `max_chars` is a screen-reader convention (150), not a WCAG requirement. Lint input is capped at 100 000 characters.

## Why not axe-core

axe-core detects a missing alt attribute but does not judge alt text quality or write replacement text. This library checks the text itself and can generate it through a model port.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and limits.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
