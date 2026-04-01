# Design: Execution Results Layer

## Summary

Execution results sit between:
- prompt packets
- execution plans
- scored benchmark runs

They represent “what was actually produced or prepared for production” regardless of whether benchmark scoring has happened.

## Data Model

Each execution result records:
- stable result id
- model id
- plan id and packet id
- plan path and packet path
- execution mode
- result status
- summary
- benchmark report payload
- artifact paths

## Filesystem Layout

- `executions/results/<model-id>/*.json`
- `executions/results/<model-id>/*.md`
- `executions/output/<model-id>/<result-suffix>/...`

The output directory is where scaffolded or real generated files live.

## CLI Behavior

The execution CLI should:
- create scaffolded results from plans
- generate placeholder output/report files when needed
- validate result records

The admin CLI should:
- index results
- expose latest result per model

## Why This Layer Exists

This keeps the benchmark honest.

Not every generation should instantly become a scored run. A result can exist first, be reviewed later, and only then become benchmark history.

