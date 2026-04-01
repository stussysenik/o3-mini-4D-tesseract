# result-promotion Specification

## Purpose

Define how execution results are synchronized from output bundles and promoted into benchmark runs.

## Requirements

### Requirement: Controlled result capture

The system SHALL support synchronizing an execution result from its output bundle after generation artifacts are added or the benchmark report is edited.

#### Scenario: Sync output bundle into result record

- GIVEN an execution result already exists
- AND its output bundle contains updated generated files or a revised `benchmark_report.json`
- WHEN an engineer runs the capture flow
- THEN the result record reflects the updated benchmark report
- AND the artifact inventory is refreshed from the bundle

### Requirement: Promotion into benchmark runs

The system SHALL support promoting a reviewed execution result into a benchmark run without manual JSON editing.

#### Scenario: Create run from reviewed result

- GIVEN an execution result is ready for scoring
- WHEN an engineer provides run status and metric values
- THEN the system can create a benchmark run derived from that result
- AND the result record links back to the created run
