# Proposal: Add Response Ingestion Flow

## Why

The repository can already prepare dispatch bundles and scaffold result bundles, but after a real model call lands there is still a manual gap: raw provider output has to be copied, interpreted, and attached by hand.

That is the last practical blocker before repeated live generations are low-friction and auditable.

## What Changes

- add an OpenSpec capability for provider response ingestion
- add an execution CLI command that captures raw provider responses from dispatch bundles
- normalize assistant output into result-bundle artifacts and benchmark report updates
- validate captured response artifacts as part of the dispatch and result lifecycle

## Expected Outcome

An engineer can run a provider request, save the raw response, ingest it once, and continue with capture/review/promotion without hand-editing result JSON or moving files manually.
