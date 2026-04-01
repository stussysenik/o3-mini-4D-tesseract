# showcase-comparison Specification

## Purpose

Define a repository-native comparison and showcase layer for viewing two benchmark subjects side by side across responsive device presets.

## Requirements

### Requirement: Durable comparison records

The system SHALL store comparison records independent of execution results and scored runs.

#### Scenario: Compare two benchmark subjects

- GIVEN two benchmark subjects exist as results or runs
- WHEN an engineer creates a showcase comparison
- THEN the repository stores a machine-readable comparison record
- AND that record resolves both subjects to their canonical result bundles

### Requirement: Responsive showcase surfaces

The system SHALL generate a responsive static HTML showcase for each comparison.

#### Scenario: View on mobile, tablet, and desktop

- GIVEN a comparison record exists
- WHEN the showcase site is built
- THEN the generated page presents mobile, tablet, and desktop presets
- AND visual evidence and code deltas are available from the same comparison surface

### Requirement: Code and capture multiplexing

The system SHALL multiplex generated code changes and capture artifacts side by side.

#### Scenario: Compare visual and implementation deltas

- GIVEN both comparison subjects have generated files or capture files
- WHEN the showcase is rendered
- THEN the page highlights added, removed, changed, and unchanged generated files
- AND aligns available captures for left/right comparison

### Requirement: Catalog integration

The system SHALL index comparison records and generated showcase pages in the benchmark catalog.

#### Scenario: Latest comparison lookup

- GIVEN one or more showcase comparisons exist
- WHEN the catalog is rebuilt
- THEN the latest comparison artifact and latest showcase page are discoverable from the catalog

### Requirement: Latest variant resolution

The system SHALL resolve the latest relevant result by model, target, and variant selectors.

#### Scenario: Compare latest reasoning variants without hand-picking paths

- GIVEN multiple result bundles exist for the same model and target
- WHEN an engineer requests a showcase comparison by model ids and reasoning-effort selectors
- THEN the showcase layer resolves the latest matching result for each side
- AND the resulting comparison preserves variant identity in the title, labels, and pair key
