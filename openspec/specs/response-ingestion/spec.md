# response-ingestion Specification

## Purpose

Define how raw provider responses are captured, normalized, and attached to execution results without manual JSON editing.

## Requirements

### Requirement: Provider response capture

The system SHALL be able to ingest a raw provider response for an existing dispatch bundle.

#### Scenario: Capture an API response into the dispatch lifecycle

- GIVEN a provider dispatch bundle exists
- WHEN an engineer captures a raw provider response
- THEN the repository stores that response under the dispatch bundle
- AND links the captured response back to the referenced execution result

### Requirement: Normalized result materialization

The system SHALL normalize captured provider output into stable result-bundle artifacts.

#### Scenario: Extract machine-usable output from markdown generation

- GIVEN the provider response contains the benchmark delivery contract
- WHEN the response is ingested
- THEN the result bundle stores the assistant response in a stable location
- AND declared files are materialized under `generated/`
- AND the benchmark report is updated from the parsed report block

### Requirement: Provenance-preserving validation

The system SHALL keep dispatch, result, and catalog provenance consistent after ingestion.

#### Scenario: Ingested response becomes the current result state

- GIVEN a response has been ingested for a dispatch
- WHEN validation or catalog rebuild runs
- THEN the dispatch references the captured response artifacts
- AND the result artifact inventory includes the normalized output artifacts
