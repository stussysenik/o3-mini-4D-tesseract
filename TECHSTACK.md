# Tech Stack

## Core Stack

### Python 3.12

Python is the orchestration layer for the repository.

It currently powers:
- packet generation
- execution planning
- provider auth inspection
- catalog generation
- benchmark run recording
- generated documentation refresh

Key files:
- [`benchmark_core.py`](./benchmark_core.py)
- [`benchmark_generate.py`](./benchmark_generate.py)
- [`benchmark_execute.py`](./benchmark_execute.py)
- [`benchmark_admin.py`](./benchmark_admin.py)
- [`benchmark_ledger.py`](./benchmark_ledger.py)

### JSON

JSON is the machine-readable persistence layer.

It is used for:
- benchmark manifests
- model registry
- provider registry
- generation manifest
- execution manifest
- prompt packets
- execution plans
- benchmark runs
- generated catalogs and history exports

### Markdown

Markdown is the human-readable documentation layer.

It is used for:
- root project docs
- scene briefs
- prompt templates
- prompt packet bundles
- execution plan bundles
- OpenSpec specs and change records

## Planning And Orchestration

### DSPy

DSPy is the primary programmable planning/orchestration direction.

Current role:
- execution-plan contract surface
- future optimization-ready planning layer

Installed dependency:
- `dspy==3.1.3`

### OpenSpec

OpenSpec is the repository-native planning layer.

Current role:
- living specs
- architecture change proposals
- durable design intent

Location:
- [`openspec/`](./openspec/)

## Provider And Tool Integrations

### OpenAI

Profiles:
- `openai-responses`
- `codex-workspace`

Used for:
- `o3`
- `gpt-5.4`
- codex-family model entries

### Anthropic

Profiles:
- `anthropic-messages`
- `claude-code-native`

Used for:
- `claude-opus-4`
- `claude-opus-4.1`

### Z.AI / GLM

Profiles:
- `zai-openai-compatible`
- `zai-claude-code-bridge`

Used for:
- `glm-5.1`

This supports both:
- direct API execution
- Claude Code bridge configuration

### NVIDIA NIM

Profiles:
- `nvidia-nim-endpoint`
- `nvidia-nim-container`

Used for:
- future endpoint-based or self-hosted model execution

## Benchmark Target Stack

### Primary Visual Lane

Browser-native targets:
- TypeScript + WebGPU
- JavaScript + WebGPU

Why:
- strongest apples-to-apples visual comparison
- browser-native delivery
- easiest benchmark fairness story

### Secondary Systems Lane

Browser-delivered compiled path:
- Zig + WASM + WebGPU

Why:
- useful when compiled/WASM-heavy architecture is part of the experiment

## Storage Layout

### Top-Level Historical Roots

- [`o3/`](./o3/)
- [`glm-5.1/`](./glm-5.1/)

These preserve the original benchmark roots and active early tracks.

### Scalable Model Roots

- [`models/`](./models/)

This is the long-term storage strategy for the larger comparison matrix.

## Validation And Integrity

### GitHub Actions

Workflow:
- [`benchmark-integrity.yml`](./.github/workflows/benchmark-integrity.yml)

It validates:
- generated packets
- execution plans
- run records
- generated catalog freshness
- generated README freshness

### Local Validation Commands

```bash
python benchmark_generate.py validate
python benchmark_execute.py validate
python benchmark_admin.py build-catalog --check
python benchmark_ledger.py validate
python benchmark_ledger.py build-readme --check
```

## Environment And Secrets

Example env file:
- [`.env.example`](./.env.example)

The system currently relies on environment variables for credentials and tool bridge config.

Examples:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `ZAI_API_KEY`
- `NIM_BASE_URL`
- `NVIDIA_API_KEY`
- `NGC_API_KEY`

## Deliberate Non-Choices

The repository does not currently depend on:
- a database
- a task queue
- LangChain as the primary architecture
- LangSmith as the required tracing layer

Those can be added later if they become useful, but they are intentionally not the benchmark contract.

