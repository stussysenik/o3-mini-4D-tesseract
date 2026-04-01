# Proposal: Add DSPy and OpenSpec Execution Architecture

## Why

The repository already supports prompt packets and benchmark runs, but it does not yet have:

- a scalable model registry for many models
- a planning-first execution layer
- a single-source-of-truth catalog for latest packets and duplicate detection
- persistent OpenSpec artifacts describing the intended architecture

## What Changes

- Add a shared Python core module for reusable benchmark utilities.
- Add a stable model registry decoupled from external provider aliases.
- Add DSPy-ready execution planning artifacts and a headless execution CLI.
- Add an admin/catalog CLI for latest-packet selection and duplicate detection.
- Add OpenSpec specs and this change record so intent stays in the repository.

## Expected Outcome

The benchmark can grow from a two-track repo into a multi-model comparison system without hard-coded directory assumptions or prompt-packet sprawl.

