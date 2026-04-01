# add-local-preview-server

## Why

Generated results are reviewable as files, but not yet first-class runnable artifacts. That makes the benchmark slower to inspect than it should be, especially for WebGPU browser outputs and showcase pages.

## What Changes

- Add a pinned Vite preview toolchain.
- Add a small preview CLI for execution results and showcase sites.
- Document the preview flow and verify path resolution with tests.

## Impact

- Captured model outputs can be opened locally in a browser with one command.
- Side-by-side comparison sites become equally easy to inspect.
- The repository gains a stable frontend preview surface without adopting a heavier app framework.
