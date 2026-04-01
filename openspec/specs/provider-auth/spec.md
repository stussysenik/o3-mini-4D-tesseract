# provider-auth Specification

## Purpose

Define how provider credentials, tool-bridge configuration, and readiness checks are represented for benchmark execution.

## Requirements

### Requirement: Profile-driven auth

The system SHALL describe provider auth through reusable profiles instead of duplicating env rules per model.

#### Scenario: Multiple models share one provider

- GIVEN several benchmark models use the same provider transport
- WHEN the execution tooling checks auth
- THEN it reads one provider profile
- AND each model references that profile rather than copying env requirements

### Requirement: Tool bridge support

The system SHALL support config rendering for tool bridges such as Claude Code.

#### Scenario: GLM through Claude Code

- GIVEN GLM is used through a Claude Code-compatible bridge
- WHEN the engineer renders config for that tool profile
- THEN the system returns the required environment mapping and base URL

### Requirement: Readiness reporting

The system SHALL report whether required auth variables are present before execution.

#### Scenario: Planning before dispatch

- GIVEN an execution plan is created
- WHEN auth is incomplete
- THEN the plan records that status explicitly
- AND the execution remains safe to keep in `plan-only` mode

