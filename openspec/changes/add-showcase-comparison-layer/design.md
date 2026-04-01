# Design: Showcase Comparison Layer

## Integration Point

The comparison layer should anchor on execution results, not runs.

- Results already own `output_root`, `benchmark_report`, generated files, captures, and dispatch lineage.
- Runs are still supported, but they should resolve to their originating result via `conditions.execution_result_id` or artifact references.

## Storage

- `showcase/manifest.json`: shared comparison/device contract
- `showcase/comparisons/`: machine-readable comparison records
- `showcase/site/`: generated static HTML comparison pages

## Comparison Resolution

Each subject resolves to:
- label and identity
- canonical result path
- output root
- benchmark report
- generated file inventory
- capture inventory

## Rendering

Each showcase page should include:
- left/right summary cards
- mobile/tablet/desktop device preset toggles
- side-by-side visual panes for captures
- code delta summaries with file status counts
- expandable unified diffs for changed text files

## Validation

- comparison subjects must resolve successfully
- generated comparison artifacts must exist
- catalog integration should publish latest comparison and site paths
