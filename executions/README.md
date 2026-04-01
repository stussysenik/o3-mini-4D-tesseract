# Executions

This directory stores DSPy-oriented execution plans, execution results, provider dispatch bundles, and generated output bundles.

- `manifest.json` defines execution-plan, execution-result, and dispatch-bundle requirements.
- `plans/<model-id>/` contains machine-readable execution plans.
- `results/<model-id>/` contains captured or scaffolded execution results.
- `dispatches/<model-id>/` contains machine-readable provider dispatch records.
- `request-bundles/<model-id>/` contains runnable prompt bundles, request payloads, invocation notes, and response placeholders.
- `output/<model-id>/` contains scaffolded or real generated files referenced by results.
- [`benchmark_catalog.json`](../benchmark_catalog.json) is generated and acts as a single source of truth for latest packets, plans, results, outputs, runs, and duplicate detection.

The current phase is still planning-first. Results let the repo capture raw or scaffolded generations before they are reviewed and promoted into scored benchmark runs.

Useful commands:
- `python benchmark_execute.py readiness-report --allow-partial`
- `python benchmark_execute.py bootstrap-readiness`
- `python benchmark_execute.py create-result --plan ...`
- `python benchmark_execute.py create-dispatch --result ... --profile ...`
- `python benchmark_execute.py capture-agent-response --dispatch ... --source ...`
- `python benchmark_execute.py ingest-response --dispatch ...`
- `python benchmark_execute.py capture-result --result ...`
- `python benchmark_execute.py promote-result --result ... --metric key=value`
- `python benchmark_preview.py serve-result --result ...`
