# Proposal: Add Showcase Comparisons

## Why

The benchmark pipeline already captures packets, plans, results, dispatches, and runs, but it does not yet provide a fast side-by-side review surface for visual output differences and generated code changes across devices.

That comparison layer is required for quick evaluation on mobile, iPad, and desktop without manually assembling presentations.

## What Changes

- Add a showcase-comparisons spec.
- Add a `benchmark_showcase.py` CLI for creating comparison records and building responsive sites.
- Add a `showcase/` artifact layer with canonical comparison records and generated sites.
- Index comparisons in the benchmark catalog.

## Expected Outcome

An engineer can point the repo at two results or runs and immediately generate a responsive comparison surface that shows captures, report metadata, and generated code diffs side by side.
