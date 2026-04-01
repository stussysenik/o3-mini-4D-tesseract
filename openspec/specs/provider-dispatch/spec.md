# provider-dispatch Specification

## Purpose

Define how reviewed execution results become concrete provider-dispatch bundles that can be executed reproducibly.

## Requirements

### Requirement: Durable dispatch records

The system SHALL store provider-dispatch records independent of results and scored runs.

#### Scenario: Prepared request bundle

- GIVEN an execution result is ready for provider execution
- WHEN an engineer prepares a dispatch bundle
- THEN the repository stores a machine-readable dispatch record
- AND that record references the exact result, plan, packet, and provider profile being used

### Requirement: Runnable request bundles

The system SHALL emit provider-specific request bundles that an engineer can execute without reconstructing prompts by hand.

#### Scenario: OpenAI-compatible or Anthropic dispatch

- GIVEN a dispatch bundle is created for an API-capable profile
- WHEN the request bundle is written
- THEN it contains the request payload, prompt bundle, and invocation instructions
- AND the payload is derived from the current packet and result contract

### Requirement: Catalog integration

The system SHALL index dispatch records in the benchmark catalog.

#### Scenario: Latest dispatch lookup

- GIVEN one or more dispatches exist for a model
- WHEN the catalog is rebuilt
- THEN the latest dispatch and latest request bundle path are available alongside packets, plans, results, outputs, and runs
