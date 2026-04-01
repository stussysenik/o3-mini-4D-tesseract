# Model Registry

This directory is the scalable storage root for benchmarked models beyond the original `o3/` and `glm-5.1/` top-level folders.

- The single source of truth for model identities lives in `registry.json`.
- Each model gets a stable benchmark id, a storage root, and an execution channel.
- External provider aliases can change over time; benchmark ids should not.

Planned model storage roots are created lazily as runs and execution plans are added.

