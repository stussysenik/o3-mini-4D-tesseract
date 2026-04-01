# prompt-packet-lifecycle Specification

## Purpose

Define how prompt packets are created, indexed, deduplicated, and selected as the latest relevant source of truth for generation.

## Requirements

### Requirement: Reproducible prompt packets

The system SHALL emit machine-readable prompt packets and human-readable prompt bundles for each generated request.

#### Scenario: Replaying a prompt

- GIVEN a model packet exists in the repository
- WHEN an engineer wants to rerun the same generation
- THEN the packet contains the system prompt, scene brief, compiled user prompt, target, locales, and capability set

### Requirement: Latest packet selection

The system SHALL identify the latest relevant packet for a model and recipe combination.

#### Scenario: Selecting the newest packet

- GIVEN multiple packets exist for the same model, recipe, kind, and target
- WHEN the catalog is built
- THEN the catalog marks the newest packet as the latest relevant packet for that semantic key

### Requirement: Duplicate detection

The system SHALL detect exact and semantic packet duplicates.

#### Scenario: Recreated equivalent packet

- GIVEN two packets differ only by timestamp or filename
- WHEN their normalized semantic content matches
- THEN the catalog reports them as semantic duplicates

