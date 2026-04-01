# Design: Provider Execution Provenance

## Dispatch Layer

Dispatch records gain a `request_settings` object. This stores provider-neutral settings such as:

- `reasoning_effort`
- `max_output_tokens`

These settings are copied into the emitted provider request payload whenever the transport supports them.

## Live Execution Layer

`benchmark_execute.py run-dispatch` executes HTTP-capable dispatches directly from the repository. It captures:

- request start and finish timestamps
- total duration in milliseconds
- endpoint
- request and response byte counts
- HTTP status

The raw provider response is written before any ingestion step.

## Ingestion Layer

When a response is ingested, the result benchmark report stores:

- raw provider usage
- normalized usage
- pricing-backed cost estimate when available
- prompt/request hashes and paths
- request settings and request execution timing

## Pricing Layer

Pricing snapshots live in `providers/pricing.json`. They are versioned repo artifacts with:

- provider/model identity
- effective date
- per-million token rates
- source URL and retrieval date

## Showcase Layer

Result-backed showcase sides derive a variant-aware label from provider execution settings. For example:

- `gpt-5.4 (xhigh)`

The comparison key uses that variant identity so side-by-side surfaces can distinguish reasoning variants of the same model.
