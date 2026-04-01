# add-agent-capture-and-latest-showcase

## Why

The benchmark now has real workspace-agent lanes, but Codex or Claude-style responses still require hand-managed text artifacts and manual comparison path lookup. That is friction in the exact path we want engineers to use first while prompts and architecture are still maturing.

## What Changes

- Add a first-class CLI flow to capture workspace-agent responses into dispatch/result bundles with provenance.
- Add a showcase selector flow that resolves the latest result by model, target, and reasoning-effort variant.
- Regenerate docs so Codex-first execution and variant comparisons are part of the normal workflow.

## Impact

- Codex-backed generations can be ingested without manual JSON edits.
- Side-by-side comparisons become cheap to produce for latest model variants.
- Provenance stays honest even when token or cost telemetry is unavailable from the agent channel.
