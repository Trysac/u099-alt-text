# Security notes

## Threat model

`trysac-alt-text` performs no network access and has no runtime dependencies. Its inputs are alt text, HTML documents, image bytes, context strings and model replies, all of which may be hostile.

Defended:

- **Prompt injection through context**: the system message declares that text inside `<context>` tags and text visible in the image are data, never instructions. Any `<` that starts a `context` or `/context` tag in the context string (any case) is replaced by `&lt;` so the user message contains only the real delimiters.
- **Hostile model replies**: replies are treated as plain text. Quotes, labels and prefixes are stripped, the text is cut at a sentence or word boundary and then linted. Replies are never treated as HTML; callers must HTML-escape `alt` before output. The `complex` purpose parses JSON with `json.loads` and requires a string `alt`.
- **Oversized input**: image data is capped by `max_image_bytes` (default 20 000 000 bytes, and at most 100 000 000 bytes in header parsing), context at 10 000 characters, replies at 50 000 characters, lint input at 100 000 characters, HTML at `max_chars` (default 5 000 000) and at most 10 000 images per document.
- **Malformed images**: header parsing validates signatures and lengths and rejects truncated headers and dimensions outside 1..65535 with `unsupported_image`. Pixels are never decoded.
- **Hostile HTML**: parsing uses the standard `html.parser`; no code is evaluated and no URL is fetched.
- **Error messages**: exception messages are cut to 200 characters.

Not defended:

- Prompt injection that the model follows despite the system message; the library cannot guarantee model behaviour.
- Misleading but well-formed alt text that passes the lint rules; the rules check form, not truth.
- Content that the vision model misdescribes or that is sensitive and sent to the LLM provider chosen by the caller.
- Denial of service from very large but within-limit inputs processed by the caller's model.
- Supply chain of the caller's own LLM adapter; the library does not authenticate it.

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).
