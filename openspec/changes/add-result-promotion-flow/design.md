# Design: Result Promotion Flow

## Summary

The result lifecycle gains two explicit transitions:
- `capture-result`
- `promote-result`

These transitions operate on the existing execution result record instead of bypassing it.

## Capture

`capture-result` reads the existing result and its output bundle.

It:
- loads `benchmark_report.json`
- refreshes the result artifact inventory from the bundle filesystem
- updates result status and review metadata
- rewrites the result markdown and bundle manifest

This makes the output bundle the practical source of truth for provider-produced files while keeping the result JSON synchronized.

## Promotion

`promote-result` creates a benchmark run from a reviewed result.

It:
- derives run conditions from `recommended_run_conditions`
- carries forward scientific report fields from the result benchmark report
- includes packet, plan, result, and bundle artifacts in the run
- writes the run file using the benchmark ledger contract
- links the result back to the run

## Safety

Promotion should reject scaffold-only results unless explicitly overridden.

This prevents the repository from claiming benchmark history before any actual generation has been captured.
