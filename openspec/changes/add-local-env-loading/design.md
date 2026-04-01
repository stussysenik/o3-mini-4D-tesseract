# Design: Local Env Loading

## Summary

The shared environment reader in `benchmark_core.py` will become the single source of truth for both shell-exported variables and repo-local env files.

## Loading Order

1. process environment
2. `.env.local`
3. `.env`

Process environment remains authoritative so CI and explicit shell exports continue to override local files.

## Parsing Rules

- Support blank lines and comment lines.
- Support `export KEY=value`.
- Support quoted and unquoted scalar values.
- Ignore malformed lines rather than failing auth checks.

## Dispatch Script Behavior

Generated `curl.sh` scripts will source `.env.local` or `.env` from the repo root before invoking the provider endpoint. That keeps the request bundle runnable as a standalone artifact from the checked-out repo.

## Validation

- Unit tests cover env-file parsing and precedence.
- Auth and readiness commands are re-run against the updated environment surface.
