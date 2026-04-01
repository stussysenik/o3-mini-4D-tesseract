# execution-results Specification

## Purpose

Define the durable artifact layer between execution plans and scored benchmark runs.

## Requirements

### Requirement: First-class execution results

The system SHALL store execution results as machine-readable artifacts independent of final scored runs.

#### Scenario: Generation exists before scoring

- GIVEN a model generation has been captured
- WHEN scoring and review are not complete yet
- THEN the repository can persist the output as an execution result
- AND the scored benchmark run can be created later

### Requirement: Scaffoldable output bundles

The system SHALL support scaffolded result bundles before real generated files exist.

#### Scenario: Prepare a result slot

- GIVEN an engineer wants to prepare for a real provider-backed generation
- WHEN they create a result from a plan
- THEN the system can scaffold an output directory and report template
- AND future generated files can be dropped into that location

### Requirement: Catalog integration

The system SHALL index execution results in the repository catalog.

#### Scenario: Latest relevant result

- GIVEN multiple results exist for a model
- WHEN the catalog is rebuilt
- THEN the latest result path is available alongside latest packet, plan, and run

