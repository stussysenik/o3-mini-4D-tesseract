# Vision

## Mission

Build the most credible long-term benchmark for model-authored 3D frontend systems.

The benchmark should show:
- what different models can generate
- how those outputs evolve over time
- which prompt and architecture patterns actually improve quality
- how performance, design, and multilingual support trade off against each other

## Core Idea

This repository is not just a prompt dump and not just a leaderboard.

It is a longitudinal benchmark system with:
- a shared scene brief
- reproducible prompt packets
- explicit execution plans
- machine-readable benchmark records
- generated catalogs for latest artifacts and duplicate control

The immediate benchmark target is a browser-native hypertesseract experience with WebGPU-first expectations and optional WASM.

## What We Want To Learn

We want to compare:
- `o3`
- `glm-5.1`
- `gpt-5.4`
- codex-family models
- Opus-family models

We also want to compare:
- one-liner prompts
- one-sentence prompts
- one-shot prompts
- future checkpointed and IR-driven prompt recipes

The goal is not only “which model is best,” but also:
- which prompt structure is most leverageable
- which architecture scales as model count grows
- which outputs stay reproducible and defensible

## Principles

- Fairness first: primary leaderboard comparisons should stay browser-native and comparable.
- Single source of truth: packets, plans, runs, and catalogs should be machine-readable and deterministic.
- Planning before spend: architecture and eval maturity come before large-scale paid generation.
- Honest reporting: no inflated claims about performance, quality, or multilingual support.
- Longitudinal value: history matters, not just the latest best-looking output.

## Product Direction

This benchmark should become:
- a historical archive of state-of-the-art generated visual systems
- a rigorous prompt-engineering and generation-architecture lab
- a provider-agnostic orchestration workspace
- a reproducible benchmark that other engineers can rerun and extend

## Near-Term Roadmap

1. Finalize comparable prompt packets across the target model set.
2. Turn on actual generation for the first execution path, starting with models that already have credentials available.
3. Capture real generated artifacts and benchmark reports.
4. Score the first completed runs.
5. Expand prompt complexity from one-liners to richer checkpointed and IR-driven flows.

## Long-Term Goal

The end state is a benchmark that can answer:

"Given the same visual ambition, target runtime, and reporting contract, which model and prompt architecture produce the best real frontend system today, and how has that answer changed over time?"

