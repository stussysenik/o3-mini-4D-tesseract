# Proposal: Add Result Promotion Flow

## Why

Execution results now exist as the durable layer between plans and scored runs, but they still require manual editing to move forward.

That is the wrong pressure point for actual generations.

When the first real GLM, o3, GPT, or Opus outputs land, the repository should already have a safe path to:
- sync output bundles into result records
- refresh benchmark reports and artifact inventories
- promote reviewed results into benchmark runs

## What Changes

- add OpenSpec requirements for result capture and promotion
- add execution CLI commands to capture and promote results
- reuse the benchmark ledger contract instead of inventing a second run format
- update docs so the lifecycle is packet -> plan -> result -> run

## Expected Outcome

The repository becomes ready for real provider-backed generations without requiring hand-edited JSON files for every captured output.
