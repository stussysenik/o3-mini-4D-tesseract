# generation-readiness Specification

## Purpose

Define how the repository prepares all configured model lanes for actual generation runs.

## Requirements

### Requirement: Multi-model bootstrap

The system SHALL support bootstrapping missing prompt packets, execution plans, execution results, and dispatch bundles for a model set.

#### Scenario: Prepare the benchmark matrix

- GIVEN a repository with registered models
- WHEN an engineer runs the readiness bootstrap flow
- THEN each requested model can end with a latest packet, plan, result, and dispatch artifact
- AND existing artifacts are reused instead of duplicated when they still match

### Requirement: Readiness reporting

The system SHALL report whether each model is ready for actual generation based on current artifacts and provider auth state.

#### Scenario: Decide whether to run now

- GIVEN multiple model lanes exist
- WHEN an engineer runs the readiness report
- THEN the report shows the latest packet, plan, result, dispatch, and auth readiness for each model
- AND it identifies whether the model is currently runnable
