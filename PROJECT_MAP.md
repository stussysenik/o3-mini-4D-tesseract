# Project Map

This file is the fastest way to understand where things live without scanning the whole repository.

## Core Docs
- [README.md](/Users/s3nik/Desktop/tesseract-benchmark/README.md): generated operational overview and benchmark status.
- [VISION.md](/Users/s3nik/Desktop/tesseract-benchmark/VISION.md): long-term mission and benchmark direction.
- [DESIGN.md](/Users/s3nik/Desktop/tesseract-benchmark/DESIGN.md): architecture, artifact lifecycle, and system design.
- [TECHSTACK.md](/Users/s3nik/Desktop/tesseract-benchmark/TECHSTACK.md): implementation surface, providers, and tooling choices.

## Core CLIs
- [benchmark_generate.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_generate.py): prompt packets and recipe-driven generation inputs.
- [benchmark_execute.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_execute.py): plans, results, dispatches, response capture, and ingestion.
- [benchmark_showcase.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_showcase.py): side-by-side comparison records and responsive showcase sites.
- [benchmark_preview.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_preview.py): local Vite-based preview server for captured results and showcase sites.
- [benchmark_admin.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_admin.py): single-source catalog and latest-artifact lookup.
- [benchmark_ledger.py](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_ledger.py): scored runs, history exports, and generated README output.

## Canonical Data Areas
- [generation/](/Users/s3nik/Desktop/tesseract-benchmark/generation): prompts, recipes, and reproducible prompt packets.
- [executions/](/Users/s3nik/Desktop/tesseract-benchmark/executions): plans, results, dispatches, request bundles, and generated output bundles.
- [showcase/](/Users/s3nik/Desktop/tesseract-benchmark/showcase): comparison records and static responsive comparison sites.
- [providers/](/Users/s3nik/Desktop/tesseract-benchmark/providers): provider profiles, auth expectations, and pricing snapshots.
- [models/](/Users/s3nik/Desktop/tesseract-benchmark/models): scalable model registry for lanes beyond `o3` and `glm-5.1`.

## Model Lanes
- [o3/](/Users/s3nik/Desktop/tesseract-benchmark/o3): `o3` track storage, archived baseline import, and scored run records.
- [glm-5.1/](/Users/s3nik/Desktop/tesseract-benchmark/glm-5.1): `glm-5.1` track storage and scored run records.

## Planning And Specs
- [openspec/](/Users/s3nik/Desktop/tesseract-benchmark/openspec): living specs and change proposals.
- [openspec/specs/](/Users/s3nik/Desktop/tesseract-benchmark/openspec/specs): durable requirements.
- [openspec/changes/](/Users/s3nik/Desktop/tesseract-benchmark/openspec/changes): proposal, design, and task records for implemented changes.

## Verification
- [tests/](/Users/s3nik/Desktop/tesseract-benchmark/tests): unit tests for env loading, execution ingestion, provenance, and showcase behavior.
- [Makefile](/Users/s3nik/Desktop/tesseract-benchmark/Makefile): short aliases for the most common validation and maintenance commands.
- [package.json](/Users/s3nik/Desktop/tesseract-benchmark/package.json): pinned local preview toolchain for Vite-based browser inspection.

## Common Paths
- Latest catalog: [benchmark_catalog.json](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_catalog.json)
- Run history export: [benchmark_history.json](/Users/s3nik/Desktop/tesseract-benchmark/benchmark_history.json)
- Showcase index: [showcase/site/index.html](/Users/s3nik/Desktop/tesseract-benchmark/showcase/site/index.html)
