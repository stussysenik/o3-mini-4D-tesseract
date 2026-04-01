# Design

This change is intentionally non-destructive.

- Keep all current benchmark paths stable.
- Add navigation instead of moving artifact roots.
- Update the README generator instead of editing the generated README directly.
- Add a small `Makefile` as a convenience layer, not a second source of truth.

The organization target here is clarity, not hierarchy churn.
