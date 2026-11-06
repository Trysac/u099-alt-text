# Architecture

## Purpose

`trysac-alt-text` is a small, dependency-free Python library that lints and generates image alt text following WCAG 2.2 and the WAI alt decision tree, with HTML scanning and a vision LLM port.

## Shape

```text
caller code --> alt_text (public API in __init__.py)
                    |
                    +-- lint, html_scan, images: pure functions, no I/O
                    +-- generate: calls a VisionLLMPort supplied by the caller
                    +-- __main__: command line, reads files, prints results
```

- **Public API**: the names listed in `__all__` of `src/alt_text/__init__.py`: `AltIssue`, `AltTextError`, `AltTextResult`, `ImageInfo`, `ImgFinding`, `Purpose`, `__version__`, `generate_alt_text`, `lint_alt_text`, `read_image_info`, `scan_html`.
- **Errors**: invalid input raises `AltTextError` with a stable `code`, or built-in `TypeError` and `ValueError` for wrong argument types and values.
- **Network**: the library makes no network calls. Image bytes are sent only to the LLM object the caller provides.
- **Logging**: a module logger with a `NullHandler` only.

## Decisions

Architecture decisions are recorded in [decisions/](decisions/) as numbered ADRs.
