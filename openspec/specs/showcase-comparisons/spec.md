# showcase-comparisons Specification

## Purpose

Define how the repository produces responsive side-by-side comparison artifacts for model outputs, including visual evidence and code changes.

## Requirements

### Requirement: Durable comparison records

The system SHALL store comparison records as canonical machine-readable artifacts.

#### Scenario: Compare two benchmark outputs

- GIVEN two execution results or benchmark runs exist
- WHEN an engineer creates a showcase comparison
- THEN the repository stores a comparison record that references both sides
- AND the record captures target, device presets, and generated artifacts

### Requirement: Responsive showcase sites

The system SHALL generate a responsive comparison site from a comparison record.

#### Scenario: Mobile, tablet, and desktop review

- GIVEN a comparison record exists
- WHEN the site is built
- THEN the generated site presents side-by-side review surfaces for mobile, tablet, and desktop contexts
- AND visual evidence and code-change summaries remain visible without hand-authoring HTML

### Requirement: Visual and code multiplexing

The system SHALL support visual evidence and generated-code comparison in the same comparison surface.

#### Scenario: Capture-driven visual review with code deltas

- GIVEN both sides expose captures and generated source files
- WHEN the comparison site is built
- THEN the site links or embeds the best available captures per device
- AND the site includes common-file diffs plus left-only and right-only generated files

### Requirement: Catalog continuity

The system SHALL index showcase comparisons in the repository catalog.

#### Scenario: Latest comparison lookup

- GIVEN one or more comparisons exist
- WHEN the benchmark catalog is rebuilt
- THEN the latest comparison paths are available alongside packets, plans, results, dispatches, and runs
