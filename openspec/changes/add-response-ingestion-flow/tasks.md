# Tasks: Add Response Ingestion Flow

## Phase 1: Specification

- [x] Add response-ingestion spec.
- [x] Add OpenSpec proposal, design, and tasks for this change.

## Phase 2: Implementation

- [x] Add provider-aware response extraction to the execution CLI.
- [x] Normalize assistant responses into generated artifacts and benchmark report updates.
- [x] Persist captured response metadata in the dispatch bundle and sync result artifacts.
- [x] Tighten the system prompt contract so file extraction is deterministic.

## Phase 3: Validation

- [x] Add parser coverage for current provider response shapes.
- [x] Rebuild latest readiness artifacts from the tightened prompt contract.
- [x] Validate execution, catalog, and README generation end to end.
