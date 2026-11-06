# Pure-stdlib alt text linter with a vision LLM port and injection-safe generation

Status: accepted (generated, pending human review)

## Context

Images fail WCAG 2.2 SC 1.1.1 when alt text is missing, a file name, or starts with 'image of'. axe-core only flags missing alt, and raw captioning models ignore the guidance. The library must lint text, scan HTML, read image headers and drive a vision model, while treating page context and in-image text as untrusted input and staying deterministic and dependency-free in tests.

## Decision

Use only the standard library: html.parser for scanning, struct-based header parsing for PNG, JPEG, GIF and WebP, and regex rules with word boundaries for ALT001-ALT008. The model sits behind a small Protocol (LLMPort, VisionLLMPort) with RecordedLLM and FakeLLM doubles. Generation uses a fixed system message that declares <context> and in-image text to be data, neutralises any '</context' in the context by turning its '<' into '&lt;', treats replies as plain text (JSON only for the complex purpose), cleans and cuts them at sentence or word boundaries, lints them and makes at most one retry that names the issue codes, keeping the better result. Every untrusted input has a named size cap and failures use one AltTextError with a stable code.

## Consequences

No runtime dependencies and fully deterministic tests. The rules are English-only heuristics and cannot judge whether a description is truthful; the result is plain text that callers must HTML-escape. A worse retry is discarded, so one bad model answer cannot make the output worse, but each generation can cost two model calls. Header-only parsing is cheap but does not validate pixel data.
