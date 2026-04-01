# Proposal: Add Provider Execution Provenance

## Summary

Add a provider-execution provenance layer so live benchmark generations capture request settings, timing, normalized token usage, and pricing snapshots.

## Why

The repository can already prepare dispatches and ingest responses, but live paid generations need stronger provenance:

- explicit reasoning effort and similar request settings
- direct execution timing
- raw and normalized usage accounting
- cost estimates tied to a pricing source
- variant-aware labels for side-by-side showcase comparisons

## Scope

- Add a provider-execution-provenance spec.
- Extend dispatch creation with request settings.
- Add a direct `run-dispatch` CLI for HTTP-backed providers.
- Normalize token usage and compute cost estimates when pricing data exists.
- Expose variant identity in the showcase layer.
