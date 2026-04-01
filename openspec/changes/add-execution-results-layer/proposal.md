# Proposal: Add Execution Results Layer

## Why

The repository currently has:
- prompt packets
- execution plans
- benchmark runs

It is missing a dedicated result layer between plans and runs.

That gap matters because real generations often exist before:
- scoring is complete
- benchmark runs are finalized
- artifacts are cleanly reviewed

## What Changes

- Add an execution result schema and storage path.
- Add CLI support to create and validate result artifacts.
- Support scaffolded output bundles for future real provider-backed generations.
- Extend the catalog to track latest results per model.

## Expected Outcome

The repository can safely capture generated outputs as durable artifacts before they become scored benchmark runs.

