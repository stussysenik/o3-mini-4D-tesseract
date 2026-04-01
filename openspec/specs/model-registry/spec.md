# model-registry Specification

## Purpose

Define a stable, scalable registry of benchmarked models that remains valid even when external provider aliases or execution channels evolve.

## Requirements

### Requirement: Stable benchmark ids

The system SHALL assign each benchmarked model a stable repository-level id.

#### Scenario: Provider alias changes

- GIVEN a provider changes or deprecates an external model alias
- WHEN the benchmark updates execution wiring
- THEN the repository-level model id remains unchanged
- AND historical packets, plans, and runs continue to reference the same benchmark id

### Requirement: Model storage roots

The system SHALL define a storage root for each model.

#### Scenario: Growing model count

- GIVEN the benchmark expands to many models
- WHEN a new model is registered
- THEN its packets, plans, and runs can be stored without forcing a new top-level root directory

### Requirement: Execution channel metadata

The system SHALL record how each model is expected to be executed.

#### Scenario: Mixed execution channels

- GIVEN some models run through provider APIs and others run through workspace-local agents
- WHEN the registry is read by execution tooling
- THEN the tooling can choose the appropriate execution strategy without hard-coded model-name conditionals

