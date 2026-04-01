# provider-execution-provenance Specification

## Purpose

Define how provider-backed executions record request settings, timing, token usage, and cost provenance.

## Requirements

### Requirement: Request settings must be durable

The system SHALL persist provider-neutral request settings on dispatch records.

#### Scenario: Reasoning-aware dispatch

- GIVEN an engineer prepares a dispatch with a reasoning effort or output cap
- WHEN the dispatch bundle is written
- THEN the dispatch record stores those request settings
- AND the request payload reflects the provider-specific equivalent where supported

### Requirement: HTTP execution must capture timing provenance

The system SHALL record timing and transport details when a dispatch is executed directly through the repository.

#### Scenario: Live provider request

- GIVEN a dispatch uses an HTTP-capable provider transport
- WHEN the engineer runs the dispatch from the CLI
- THEN the system stores request start time, finish time, duration, endpoint, and HTTP status
- AND the raw provider response is persisted before any ingestion step

### Requirement: Agent execution must capture response provenance

The system SHALL support provenance capture for workspace-agent style executions that return text outside direct HTTP dispatch.

#### Scenario: Codex workspace response capture

- GIVEN a dispatch uses a workspace or code-agent transport
- WHEN an engineer captures the generated response text through the CLI
- THEN the system stores approximate start/finish timing, transport identity, prompt bundle provenance, and raw response text
- AND the linked result can be ingested without manual JSON edits

### Requirement: Usage and cost must be normalized

The system SHALL normalize provider usage metadata into benchmark-friendly token accounting.

#### Scenario: GPT-5.4 execution ingestion

- GIVEN a provider response includes token usage fields
- WHEN the result is ingested
- THEN the benchmark report stores raw usage, normalized usage, and any available cost estimate
- AND the pricing snapshot references its source and retrieval date

### Requirement: Variant identity must survive comparisons

The system SHALL expose execution variants to downstream comparison surfaces.

#### Scenario: Compare reasoning variants

- GIVEN two results differ by reasoning effort or similar request settings
- WHEN the showcase layer resolves those results
- THEN their labels and comparison keys remain distinguishable in side-by-side views
