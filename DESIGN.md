# Design

## Overview

The repository is designed as a control plane for multi-model benchmark generation rather than a single app.

It is split into five major layers:
- benchmark definition
- model registry
- prompt generation
- execution planning
- run recording and reporting

## Architectural Model

### 1. Benchmark Definition

[`benchmark_manifest.json`](./benchmark_manifest.json) defines:
- the benchmark id
- scoring dimensions and weights
- controlled and independent variables
- track ids and storage roots

This is the contract that packets, plans, and runs must satisfy.

### 2. Model Registry

[`models/registry.json`](./models/registry.json) defines stable repository-level model ids.

Why:
- provider aliases can drift
- execution channels differ by model
- storage should scale beyond two top-level folders

Each model records:
- provider
- provider model name
- execution channel
- primary auth profile
- optional tool profiles
- storage root

### 3. Provider Profiles

[`providers/registry.json`](./providers/registry.json) defines reusable auth and transport profiles.

This avoids scattering credential logic across the codebase.

Examples:
- OpenAI Responses API
- Codex workspace agent
- Anthropic Messages API
- Claude Code
- Z.AI openai-compatible API
- Z.AI Claude Code bridge
- NVIDIA NIM endpoint/container profiles

### 4. Prompt Generation

[`generation/`](./generation/) is the prompt control plane.

It contains:
- a central system prompt
- scene briefs
- recipe templates
- generated prompt packets

Each packet captures:
- model id
- recipe id
- generation kind
- target runtime/language
- locales
- capabilities
- compiled prompts

The packet is the replayable source artifact for generation.

### 5. Execution Planning

[`executions/`](./executions/) stores DSPy-oriented execution plans.

The current design is planning-first:
- packets can exist without generation
- plans can exist without provider spend
- auth readiness can be checked before dispatch

Each plan records:
- packet reference
- model profile
- auth status
- execution mode
- DSPy availability
- OpenSpec references
- planned artifacts

### 6. Run Recording

[`benchmark_ledger.py`](./benchmark_ledger.py) records benchmark runs.

A run captures:
- metrics
- time ledger
- environment
- artifacts
- scientific report fields

Runs are the scored historical record.

## Single Source Of Truth Strategy

The repository intentionally uses generated catalogs and manifests instead of ad hoc conventions.

The key SSOT files are:
- [`benchmark_manifest.json`](./benchmark_manifest.json)
- [`models/registry.json`](./models/registry.json)
- [`providers/registry.json`](./providers/registry.json)
- [`generation/manifest.json`](./generation/manifest.json)
- [`executions/manifest.json`](./executions/manifest.json)
- [`benchmark_catalog.json`](./benchmark_catalog.json)

[`benchmark_catalog.json`](./benchmark_catalog.json) is generated and answers:
- latest packet per model
- latest plan per model
- latest run per model
- duplicate packet groups

## Artifact Lifecycle

The intended lifecycle is:

1. Define or refine the benchmark contract.
2. Generate a prompt packet.
3. Create an execution plan.
4. Check provider/tool auth readiness.
5. Execute generation when desired.
6. Record a benchmark run.
7. Rebuild the catalog and README.

## Prompt Complexity Ladder

The prompt system is intentionally staged:
- `one-liner`
- `one-sentence`
- `one-shot`
- future checkpointed and IR-driven flows

This allows the benchmark to measure prompt architecture, not only model capability.

## Why DSPy And OpenSpec

DSPy is used as the programmable execution/planning surface.

OpenSpec is used as the repository-native planning and architecture memory layer.

They serve different purposes:
- DSPy: modules, signatures, optimization-ready LM program structure
- OpenSpec: specs, proposals, design intent, and implementation tasks

## Scaling Strategy

The design is meant to handle growing model count without a rewrite.

Scaling is handled through:
- stable model ids
- provider profiles
- storage-root indirection
- generated catalogs
- validation-first CLIs

That keeps the benchmark from collapsing into custom per-model glue as comparisons expand.

