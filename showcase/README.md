# Showcase

This directory stores responsive side-by-side comparison artifacts.

- `manifest.json` defines shared device presets.
- `comparisons/` stores machine-readable comparison records.
- `site/` stores generated static HTML showcase pages plus the generated `index.html` comparison hub.

Use `python benchmark_showcase.py create-comparison ...` to generate new comparison artifacts.
Use `python benchmark_showcase.py build-index` to rebuild the showcase hub after comparison changes.
Use `python benchmark_preview.py serve-showcase --comparison ...` to open a local browser preview for a comparison site.
