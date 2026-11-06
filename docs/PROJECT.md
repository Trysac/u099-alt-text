# Project record

## Objective

Provide a dependency-free Python library that lints alt text against WCAG 2.2 success criterion 1.1.1 and the WAI alt decision tree, scans HTML for images, reads image dimensions from headers, and generates alt text through a vision LLM port.

## Scope

- In scope: alt text lint rules ALT001 to ALT008; HTML scanning of `<img>` elements with `html.parser`; PNG, JPEG, GIF and WebP header parsing; alt text generation through a caller-supplied vision LLM port with prompt-injection neutralisation of context; a command line interface (`lint`, `check`, `generate`).
- Out of scope: OCR, running or bundling any model, non-English rules, fetching images or pages over the network, and judging or writing alt text beyond the rules listed above.

## Timeline

| Date | Event |
|---|---|
| 2026 | Repository created from the factory utility template. |

## Effort metrics

Measured values only; a value that has not been measured stays "pending measurement".

| Metric | Value |
|---|---|
| Tokens (input / output) | 360600 / 127253 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.8665 |

## Factory run u099 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | claude-sonnet-5-5 | yes | 2574 | 115690 | 0 | 4246 | 0.5814 |
| fix-1 | claude-sonnet-5-5 | no | 8 | 1182 | 7279 | 55338 | 0.0356 |
| audit | claude-sonnet-5-5 | no | 12 | 4654 | 30085 | 125964 | 0.1344 |
| fix-2 | claude-sonnet-5-5 | no | 6 | 1453 | 8060 | 41110 | 0.0388 |
| docs | claude-haiku-5-5 | no | 131342 | 4274 | 0 | 0 | 0.0764 |

Total: $0.8665. Prices: Anthropic list prices.
