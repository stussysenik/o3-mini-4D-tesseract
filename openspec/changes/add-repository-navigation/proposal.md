# add-repository-navigation

## Why

The repository has the right subsystems now, but the root is busy and the generated README is doing too much without clearly pointing to the durable docs and operator commands. That makes the repo harder to scan than it needs to be.

## What Changes

- Add a root `PROJECT_MAP.md`.
- Add a `tests/README.md`.
- Add a small `Makefile` for the common maintenance flows.
- Teach the generated README to surface the project docs, repo map, and short command aliases.

## Impact

- Faster orientation for humans.
- Cleaner operator flow for repeated validation and catalog rebuilds.
- No breaking path changes to existing benchmark artifacts or CLIs.
