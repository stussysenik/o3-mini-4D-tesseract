# Design: Showcase Comparisons

## Summary

Introduce a dedicated showcase layer with two artifact classes:

1. canonical comparison records under `showcase/comparisons/`
2. generated responsive sites under `showcase/site/`

## Comparison Inputs

Each side of a comparison may reference either:
- an execution result, or
- a benchmark run that can be traced back to a result artifact

Result-backed data is preferred because it exposes output bundles, generated files, captures, and benchmark reports directly.

## Site Structure

Each generated site contains:
- `index.html`
- `styles.css`
- `app.js`
- `comparison.json`

The site presents:
- summary metadata
- device preset controls for mobile, tablet, and desktop
- visual evidence panes
- side-by-side benchmark report snapshots
- code inventory and unified diffs for changed files

## Single Source of Truth

The comparison record is canonical. Generated site files are derived artifacts and can be rebuilt at any time.

## Catalog Integration

`benchmark_admin.py` will scan `showcase/comparisons/` and expose latest comparison paths in the generated catalog.
