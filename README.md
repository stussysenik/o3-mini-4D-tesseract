# Tesseract Benchmark

Data-driven benchmark workspace for comparing model-authored 3D frontend systems over time. The current benchmark target is `webgpu-hypertesseract-v1`: a WebGPU-first hypertesseract scene with explicit performance, design, multilingual, and reproducibility reporting.

## Benchmark Contract
- Browser-native 3D frontend implementation
- WebGPU-first rendering path with explicit fallback notes
- Optional WASM compute or geometry pipeline when used by the experiment
- Documented environment capture for browser, GPU, locale, and display conditions
- Timestamped scientific report per run with hypothesis, method, results, limitations, and next steps
- README leaderboard generated from machine-readable run records

Controlled variables captured in every run: `browser_name`, `browser_version`, `browser_channel`, `gpu_vendor`, `gpu_adapter`, `gpu_driver`, `webgpu_backend`, `wasm_runtime`, `locale`, `canvas_size`, `device_pixel_ratio`, `headless`, `os_notes`

Independent variables encouraged per experiment: `model_track`, `generation_kind`, `target_id`, `prompt_packet_id`, `prompt_revision`, `scene_seed`, `toolchain`, `shader_strategy`, `geometry_strategy`, `wasm_enabled`, `multilingual_scope`

Target language matrix: `en`, `es`, `fr`, `de`, `ja`, `zh-CN`, `ar`

## Scoring
| Metric | Weight | Description |
| --- | ---: | --- |
| Visual Fidelity | 30% | Perceptual quality of shading, composition, geometry, and overall scene realism. |
| Performance | 25% | Frame pacing, responsiveness, and computational efficiency under declared test conditions. |
| Design Quality | 15% | Intentional interface design, presentation, typography, and interaction quality. |
| Multilingual Quality | 10% | Accuracy and polish of language support across required locales. |
| Scientific Reporting | 10% | Clarity of methodology, captured conditions, and defensible reporting. |
| Reproducibility | 10% | How easily another engineer can rerun the experiment from recorded data. |

Composite score = weighted average of all scored metrics. Runs can remain `pending` while a track is still being set up or waiting on manual evaluation.

## Project Docs
- [VISION.md](VISION.md): mission, benchmark philosophy, and long-range direction.
- [DESIGN.md](DESIGN.md): architecture, artifact lifecycle, and repository design decisions.
- [TECHSTACK.md](TECHSTACK.md): implementation stack, providers, and tooling choices.
- [PROJECT_MAP.md](PROJECT_MAP.md): fast repository navigation for docs, CLIs, and canonical artifact roots.
- [package.json](package.json): pinned local Vite preview toolchain for browser inspection.

## Quick Start
1. Put model-specific artifacts under either [`o3/`](o3/), [`glm-5.1/`](glm-5.1/), or the scalable [`models/`](models/) storage roots.
2. Generate a prompt packet from the central recipe system:

```bash
python benchmark_generate.py create-packet \
  --model o3 \
  --recipe baseline-webgpu-hypertesseract \
  --kind one-liner \
  --target ts-webgpu \
  --capability wasm \
  --locale en \
  --var creative_focus="visual fidelity and clean reporting"
```

3. Create a planning-first execution plan:

```bash
python benchmark_execute.py create-plan \
  --model o3 \
  --packet generation/packets/o3/some-packet.json \
  --mode plan-only
```

4. Check provider readiness or render tool config:

```bash
# These commands automatically read credentials from `.env.local` or `.env`.
python benchmark_execute.py auth-status --model glm-5.1 --allow-missing
python benchmark_execute.py render-config --model glm-5.1 --tool-profile zai-claude-code-bridge --format claude-settings
python benchmark_execute.py auth-status --profile nvidia-nim-endpoint --allow-missing
python benchmark_execute.py readiness-report --allow-partial
```

5. Bootstrap the full packet -> plan -> result -> dispatch chain for the model set:

```bash
python benchmark_execute.py bootstrap-readiness
```

6. Create an execution result bundle before scoring when you need a single lane manually:

```bash
python benchmark_execute.py create-result \
  --plan executions/plans/o3/some-plan.json \
  --status scaffolded
```

7. Prepare a provider dispatch bundle from the reviewed result:

```bash
python benchmark_execute.py create-dispatch \
  --result executions/results/o3/some-result.json \
  --profile openai-responses
```

8. After a real provider response lands, ingest it into the linked result bundle:

```bash
# `curl.sh` auto-sources `.env.local` or `.env` from the repo root.
python benchmark_execute.py ingest-response \
  --dispatch executions/dispatches/o3/some-dispatch.json \
  --status captured
```

9. For Codex or Claude-style workspace generations, capture the text response directly into the dispatch bundle:

```bash
python benchmark_execute.py capture-agent-response \
  --dispatch executions/dispatches/gpt-5.4/some-dispatch.json \
  --source path/to/response.md
```

10. If you make any manual report edits after ingestion, sync the result bundle again:

```bash
python benchmark_execute.py capture-result \
  --result executions/results/o3/some-result.json \
  --status captured
```

11. Promote a reviewed result into a benchmark run:

```bash
python benchmark_execute.py promote-result \
  --result executions/results/o3/some-result.json \
  --status completed \
  --metric visual_fidelity=92 \
  --metric performance=88 \
  --metric design_quality=91 \
  --metric multilingual_quality=86 \
  --metric scientific_reporting=93 \
  --metric reproducibility=89
```

12. Build a responsive side-by-side showcase from two results or runs:

```bash
python benchmark_showcase.py create-comparison \
  --left executions/results/o3/some-result.json \
  --right executions/results/glm-5.1/some-result.json
```

13. Or resolve the latest result variants directly by model and reasoning effort:

```bash
python benchmark_showcase.py create-latest-comparison \
  --left-model gpt-5.4 \
  --left-reasoning-effort medium \
  --right-model glm-5.1 \
  --target-id ts-webgpu \
  --allow-scaffolded
```

14. Rebuild the showcase index when comparisons change:

```bash
python benchmark_showcase.py build-index
```

15. Preview a captured result or showcase locally:

```bash
python benchmark_preview.py serve-result \
  --result executions/results/gpt-5.4/some-result.json

python benchmark_preview.py serve-showcase \
  --comparison showcase/comparisons/some-comparison.json
```

16. Export the environment details you want captured:

```bash
export TB_BROWSER_NAME=chrome
export TB_BROWSER_VERSION=123
export TB_GPU_ADAPTER="Apple M4 GPU"
export TB_WEBGPU_BACKEND=metal
export TB_WASM_RUNTIME=browser
export TB_LOCALE=en-US
export TB_CANVAS_SIZE=1920x1080
export TB_DEVICE_PIXEL_RATIO=2
```

17. Record a run manually when needed:

```bash
python benchmark_ledger.py create-run \
  --model o3 \
  --title "webgpu hypertesseract v1" \
  --status completed \
  --summary "First fully scored benchmark pass." \
  --artifact generation/packets/o3/some-packet-path.json \
  --artifact o3/some-artifact-path \
  --condition generation_kind=one-liner \
  --condition target_id=ts-webgpu \
  --condition prompt_packet_id=o3--timestamp--packet-slug \
  --condition prompt_revision=v1 \
  --condition toolchain=manual \
  --condition shader_strategy=webgpu-native \
  --condition geometry_strategy=procedural \
  --condition wasm_enabled=true \
  --condition multilingual_scope=en,es,ja \
  --metric visual_fidelity=92 \
  --metric performance=88 \
  --metric design_quality=91 \
  --metric multilingual_quality=86 \
  --metric scientific_reporting=93 \
  --metric reproducibility=89
```

18. Or use the short maintenance aliases:

```bash
make test
make validate
make catalog
make readme
```

19. Regenerate and validate repo-level reporting:

```bash
python benchmark_generate.py validate
python benchmark_execute.py validate
python benchmark_showcase.py validate
python benchmark_admin.py build-catalog
python benchmark_ledger.py build-readme
python benchmark_ledger.py validate
```

## Generation System
Central system prompt: [`generation/prompts/system.md`](generation/prompts/system.md)

Preferred orchestration stance: `dspy-compatible lightweight python cli`. LangChain/LangSmith remain optional rather than mandatory so the benchmark contract stays lightweight and DSPy-friendly.

### Prompt Complexity Ladder
| Kind | Status | Rank | Description |
| --- | --- | ---: | --- |
| one-liner | active | 1 | Single imperative line. Minimal steering and maximal model autonomy. |
| one-sentence | active | 2 | Single sentence with slightly richer creative and technical steering. |
| one-shot | active | 3 | Single-shot prompt with explicit constraints, output contract, and benchmark reporting. |
| checkpointed-one-shot | planned | 4 | Adds intermediate checkpoints and review gates to a single-shot prompt. |
| ir-scaffold | planned | 5 | Model receives explicit intermediate representation, design scaffolds, and implementation phases. |
| multi-pass-critic-loop | planned | 6 | Planner, implementer, and critic passes coordinated around shared benchmark checkpoints. |

### Supported Targets
| Target | Lane | Language | Runtime | Notes |
| --- | --- | --- | --- | --- |
| ts-webgpu | primary | ts | browser | Best default for the visual benchmark. Browser-native and highly comparable across models. |
| js-webgpu | primary | js | browser | Good baseline when the model is stronger at plain JavaScript than TypeScript. |
| zig-wasm-webgpu | secondary | zig | browser-wasm | Use when the experiment explicitly cares about compiled systems or WASM-heavy geometry/rendering. |

Deferred for now:
- `lua`: No clean browser-native lane has been standardized yet. Add only after a reproducible browser delivery contract exists.
- `python`: Useful for tooling and offline analysis, but not a clean primary visual benchmark target without a consistent browser/runtime contract.
- `elixir`: Interesting for server-assisted generation flows, but it changes the benchmark from pure client-side visual synthesis.

## Model Registry
| Model | Provider | Family | Channel | Auth Profile | Tool Profiles | Status |
| --- | --- | --- | --- | --- | --- | --- |
| o3 | openai | reasoning | api-or-workspace | openai-responses | codex-workspace | active |
| glm-5.1 | z-ai | general | manual-or-api | zai-openai-compatible | zai-claude-code-bridge | active |
| gpt-5.4 | openai | gpt | workspace-agent | openai-responses | codex-workspace | planned |
| gpt-5.4-mini | openai | gpt | workspace-agent | openai-responses | codex-workspace | planned |
| gpt-5.3-codex | openai | codex | workspace-agent | openai-responses | codex-workspace | planned |
| gpt-5.3-codex-spark | openai | codex | workspace-agent | openai-responses | codex-workspace | planned |
| gpt-5.2-codex | openai | codex | api-or-workspace | openai-responses | codex-workspace | planned |
| gpt-5.1-codex-max | openai | codex | workspace-agent | openai-responses | codex-workspace | planned |
| gpt-5.1-codex-mini | openai | codex | api-or-workspace | openai-responses | codex-workspace | planned |
| gpt-5-codex | openai | codex | api | openai-responses | codex-workspace | planned |
| claude-opus-4.1 | anthropic | opus | api | anthropic-messages | claude-code-native | planned |
| claude-opus-4 | anthropic | opus | api | anthropic-messages | claude-code-native | planned |

## Provider Profiles
| Profile | Provider | Transport | Required Env | Notes |
| --- | --- | --- | --- | --- |
| openai-responses | openai | responses-api | OPENAI_API_KEY | Primary OpenAI API profile. Use Responses API semantics for programmable execution. |
| codex-workspace | openai | workspace-agent | - | Uses the current coding workspace agent channel rather than direct provider API credentials. |
| anthropic-messages | anthropic | messages-api | ANTHROPIC_API_KEY | Direct Anthropic API profile for Claude model comparisons. |
| claude-code-native | anthropic | claude-code | ANTHROPIC_API_KEY | Native Claude Code configuration against Anthropic endpoints. |
| zai-openai-compatible | z-ai | openai-compatible | ZAI_API_KEY | Primary GLM API profile. The official quick start describes OpenAI-compatible tool configuration via https://api.z.ai/api/paas/v4. |
| zai-claude-code-bridge | z-ai | claude-code-bridge | ZAI_API_KEY | Official Z.AI quick start for Claude Code uses ANTHROPIC_AUTH_TOKEN plus ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic. |
| nvidia-nim-endpoint | nvidia | openai-compatible-or-custom | NIM_BASE_URL; one of NVIDIA_API_KEY/NIM_API_KEY/NIM_ENDPOINT_API_KEY | Supports a hosted or self-managed NIM endpoint once a base URL and one API key variable are present. |
| nvidia-nim-container | nvidia | container-runtime | NGC_API_KEY | Container/image access for self-hosted NIM flows. This is infrastructure auth rather than prompt-dispatch auth. |

## Planning
- OpenSpec specs live in [`openspec/specs/`](openspec/specs/).
- The active architecture change record lives in [`openspec/changes/add-dspy-openspec-execution/`](openspec/changes/add-dspy-openspec-execution/).
- The execution results change record lives in [`openspec/changes/add-execution-results-layer/`](openspec/changes/add-execution-results-layer/).
- The result promotion change record lives in [`openspec/changes/add-result-promotion-flow/`](openspec/changes/add-result-promotion-flow/).
- The provider dispatch bundle change record lives in [`openspec/changes/add-provider-dispatch-bundles/`](openspec/changes/add-provider-dispatch-bundles/).
- The generation readiness bootstrap change record lives in [`openspec/changes/add-generation-readiness-bootstrap/`](openspec/changes/add-generation-readiness-bootstrap/).
- The response ingestion change record lives in [`openspec/changes/add-response-ingestion-flow/`](openspec/changes/add-response-ingestion-flow/).
- The showcase comparison change record lives in [`openspec/changes/add-showcase-comparisons/`](openspec/changes/add-showcase-comparisons/).
- The local env loading change record lives in [`openspec/changes/add-local-env-loading/`](openspec/changes/add-local-env-loading/).
- DSPy-oriented execution plans, result records, dispatch bundles, and output bundles live in [`executions/`](executions/).
- Responsive comparison records and generated showcase sites live in [`showcase/`](showcase/).
- The generated showcase hub lives at [`showcase/site/index.html`](showcase/site/index.html).

## Current SOTA
| Track | Best Run | Status | Score | Recorded At (UTC) | Artifact |
| --- | --- | --- | ---: | --- | --- |
| o3 | [Legacy o3-mini-4D-tesseract import](o3/runs/20260401T153600Z--legacy-o3-mini-4d-tesseract-import.json) | archived | pending | 2026-04-01T15:36:00.466740Z | [artifact](o3/archive/o3-mini-4d-tesseract) |
| glm-5.1 | no runs yet | - | - | - | - |
| gpt-5.4 | no runs yet | - | - | - | - |
| gpt-5.4-mini | no runs yet | - | - | - | - |
| gpt-5.3-codex | no runs yet | - | - | - | - |
| gpt-5.3-codex-spark | no runs yet | - | - | - | - |
| gpt-5.2-codex | no runs yet | - | - | - | - |
| gpt-5.1-codex-max | no runs yet | - | - | - | - |
| gpt-5.1-codex-mini | no runs yet | - | - | - | - |
| gpt-5-codex | no runs yet | - | - | - | - |
| claude-opus-4.1 | no runs yet | - | - | - | - |
| claude-opus-4 | no runs yet | - | - | - | - |

## Recent History
| Recorded At (UTC) | Track | Run | Status | Score | Summary |
| --- | --- | --- | --- | ---: | --- |
| 2026-04-01T15:36:00.466740Z | o3 | [Legacy o3-mini-4D-tesseract import](o3/runs/20260401T153600Z--legacy-o3-mini-4d-tesseract-import.json) | archived | pending | Imported the original pygame-based fork as the zero-point historical baseli... |

## Repo Layout
- [`o3/`](o3/): o3-family experiments, historical imports, and timestamped run records.
- [`glm-5.1/`](glm-5.1/): GLM-5.1 experiments and timestamped run records.
- [`models/`](models/): scalable storage roots and registry entries for additional models.
- [`providers/`](providers/): provider and tool auth profiles for OpenAI, Claude, GLM, and NIM flows.
- [`generation/`](generation/): system prompt, scene briefs, prompt recipes, and generated prompt packets.
- [`executions/`](executions/): DSPy-oriented execution plans, execution result records, provider dispatch bundles, and output bundles awaiting scoring.
- [`showcase/`](showcase/): canonical comparison records plus generated responsive side-by-side showcase sites and the showcase index.
- [`openspec/`](openspec/): OpenSpec living specs and change proposals.
- [`benchmark_core.py`](benchmark_core.py): shared utilities used by the CLIs.
- [`benchmark_generate.py`](benchmark_generate.py): headless prompt-packet generator for recipes, targets, and prompt kinds.
- [`benchmark_execute.py`](benchmark_execute.py): execution-plan generator, result lifecycle manager, and provider-dispatch surface.
- [`benchmark_showcase.py`](benchmark_showcase.py): responsive side-by-side comparison generator for captures, reports, and code diffs.
- [`benchmark_preview.py`](benchmark_preview.py): local Vite preview server for generated results and showcase sites.
- [`benchmark_admin.py`](benchmark_admin.py): single-source-of-truth catalog builder plus latest/duplicate tooling.
- [`benchmark_catalog.json`](benchmark_catalog.json): generated single source of truth for packets, plans, results, dispatches, comparisons, runs, latest artifacts, and duplicate groups.
- [`benchmark_ledger.py`](benchmark_ledger.py): CLI for creating run records, validating them, and regenerating the README plus consolidated history exports.
- [`benchmark_history.json`](benchmark_history.json): generated aggregate history for downstream analysis.
- [`benchmark_history.jsonl`](benchmark_history.jsonl): generated line-delimited run export.
- [`tests/`](tests/): regression coverage for env loading, execution ingestion, provenance, and showcase behavior.
- [`Makefile`](Makefile): short aliases for common validation and maintenance flows.
- [`package.json`](package.json): pinned local preview dependency manifest for Vite.

Latest recorded snapshot in this README: `2026-04-01T15:36:00.466740Z`.
