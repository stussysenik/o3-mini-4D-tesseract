# Design: DSPy and OpenSpec Execution Architecture

## Summary

The design separates the benchmark into four long-lived control planes:

1. `benchmark_manifest.json`
   Defines scoring, run conditions, and benchmark-wide variables.
2. `models/registry.json`
   Defines stable model ids, storage roots, execution channels, and provider aliases.
3. `generation/`
   Defines prompt recipes and prompt packets.
4. `executions/`
   Defines DSPy-oriented execution plans that point to model ids and packet ids.
5. `providers/`
   Defines reusable auth and transport profiles for APIs and coding tools.

OpenSpec sits alongside these as the repository-native planning layer.

## Key Decisions

### Stable model ids over provider aliases

Provider aliases can change. Repository ids should not.

### Planning before paid execution

Execution plans can be created in `plan-only` or `dry-run` mode while prompt architecture matures.

### Generated catalog as single source of truth

The admin CLI generates a deterministic catalog that:

- indexes packets and plans
- identifies latest relevant artifacts
- reports duplicates

### Provider profiles over hard-coded env logic

Credential and tool-bridge logic should live in reusable provider profiles so that:

- GLM can be used directly or through Claude Code
- OpenAI models can use API or workspace-agent paths
- NIM and future providers can be added without scattering auth rules through the codebase

### Incremental migration

The existing `o3/` and `glm-5.1/` directories remain valid while future models live under `models/`.
