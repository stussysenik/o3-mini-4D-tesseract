# Generation System

This directory is the prompt and generation control plane for the benchmark.

## Principles
- One central system prompt for delivery rules, response format, and benchmark honesty.
- File-based scene briefs and recipe templates so prompts can evolve without code churn.
- Machine-readable packet IR so every generation request can be replayed, diffed, and attached to benchmark runs.
- Fairness first: primary visual SOTA should stay browser-native.

## Language Lanes
- Primary: TypeScript or JavaScript in the browser with WebGPU.
- Secondary: Zig compiled to WASM when the experiment explicitly benefits from compiled systems.
- Deferred: Lua, Python, and Elixir are intentionally not in the primary lane yet because they do not currently share a clean browser-native delivery contract.

## Tooling Stance
- Preferred long-term orchestration: DSPy-compatible Python pipeline.
- LangChain or LangSmith can be layered on later for traces or observability, but they are not the benchmark contract itself.

## Workflow
1. Edit the central rules in `prompts/system.md`.
2. Edit the benchmark brief in `prompts/scenes/`.
3. Add or refine prompt templates under `recipes/`.
4. Use `python benchmark_generate.py create-packet --model <id> ...` to emit a reproducible prompt packet.
5. Turn that packet into a planning-first execution artifact with `python benchmark_execute.py create-plan ...`.
6. Attach the generated packet path to a benchmark run via `python benchmark_ledger.py create-run --artifact ...`.
