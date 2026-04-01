# local-preview Specification

## Purpose

Define how engineers locally inspect generated benchmark outputs and showcase sites without hand-wiring ad hoc dev servers.

## Requirements

### Requirement: Captured result outputs must be previewable

The repository SHALL provide a stable local preview path for generated execution results.

#### Scenario: Review a captured WebGPU result

- GIVEN a captured execution result has a generated output bundle
- WHEN an engineer requests a local preview
- THEN the repository resolves the generated root automatically
- AND launches a local web server suitable for modern browser-native TypeScript output

### Requirement: Showcase sites must be previewable

The repository SHALL provide a stable local preview path for showcase comparison sites.

#### Scenario: Review a side-by-side comparison

- GIVEN a showcase comparison record or site root exists
- WHEN an engineer requests a local preview
- THEN the repository resolves the correct site root
- AND serves it locally without requiring manual path discovery

### Requirement: Preview tooling must be pinned

The repository SHALL pin its local preview toolchain rather than rely on floating remote package resolution.

#### Scenario: Repeated local review

- GIVEN engineers repeatedly preview generated outputs
- WHEN they install the preview toolchain
- THEN the preview server uses a pinned Vite dependency from the repository
