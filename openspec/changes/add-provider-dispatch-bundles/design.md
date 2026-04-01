# Design: Provider Dispatch Bundles

## Summary

Dispatch preparation sits after result creation and before real model execution.

The command should create:
- a machine-readable dispatch record under `executions/dispatches/<model-id>/`
- a runnable request bundle under `executions/request-bundles/<model-id>/`

## Data Shape

The dispatch request records:
- model and provider identifiers
- selected provider profile
- packet, plan, and result references
- prompt messages and delivery contract
- output directories for generated files and captures
- auth readiness snapshot

## Why Separate Dispatch Records

Dispatch preparation has its own lifecycle and should be indexable independently of result output files.

The result still remains the provenance anchor, but the dispatch record and request bundle become the execution-facing artifacts.

## Safety

Preparing dispatch does not call a provider.

It only writes the package needed for later execution and records how that execution should be captured.
