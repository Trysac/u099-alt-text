# Testing

## Running

```sh
uv run pytest --cov=alt_text   # tests with coverage report
uv run python scripts/check.py      # every gate, as CI and the factory run it
```

## Policy

- Branch coverage of `src/alt_text` must stay at or above 80 %; the gate fails below it.
- Tests exercise the public API (`import alt_text`) and assert observable effects: return values, raised exceptions and their codes.
- Each bug fix starts with a failing test that reproduces it.
- Tests are deterministic: no network, no wall clock, no dependence on test order.

## Layout

`tests/test_<module>.py` mirrors each public module. Shared fixtures go in `tests/conftest.py`.

The specification's acceptance checks cover: lint codes for the examples given in the spec and adjacent non-matching phrases; `scan_html` missing and decorative detection and the absence of any fetch; `read_image_info` for PNG, JPEG, GIF and WebP fixtures and rejection of BMP and truncated headers; `generate_alt_text` decorative behaviour, prefix cleaning and the single retry; the size limit and `</context>` neutralisation; and the CLI exit codes.
