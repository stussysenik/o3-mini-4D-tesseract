from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from benchmark_core import (
    ROOT,
    build_time_ledger,
    collect_environment,
    load_benchmark_manifest,
    load_generation_manifest,
    load_model_registry,
    load_provider_registry,
    now_utc,
    parse_pairs,
    parse_timestamp,
    relative_path,
    run_dir_for_track,
    slugify,
    track_ids,
    track_map,
    write_text_if_changed,
)

README_PATH = ROOT / "README.md"
HISTORY_JSON_PATH = ROOT / "benchmark_history.json"
HISTORY_JSONL_PATH = ROOT / "benchmark_history.jsonl"


def metric_keys(manifest: dict[str, Any]) -> list[str]:
    return list(manifest["metrics"].keys())


def build_run_payload(
    manifest: dict[str, Any],
    *,
    model: str,
    title: str,
    status: str,
    summary: str,
    artifact_paths: list[str],
    condition_values: dict[str, Any] | None = None,
    metric_values: dict[str, Any] | None = None,
    recorded_at: Any | None = None,
    slug: str | None = None,
    scientific_report: dict[str, str] | None = None,
) -> dict[str, Any]:
    recorded = recorded_at or now_utc()
    timestamp_for_id = recorded.strftime("%Y%m%dT%H%M%SZ")
    title_slug = slug or slugify(title)
    conditions = dict(manifest["recommended_conditions"])
    metrics = {key: None for key in metric_keys(manifest)}
    artifacts = [{"path": path} for path in artifact_paths]

    if condition_values:
        conditions.update(condition_values)
    if metric_values:
        metrics.update(metric_values)

    report = {
        "hypothesis": "",
        "method": "",
        "result_summary": "",
        "limitations": "",
        "next_steps": "",
    }
    if scientific_report:
        report.update(scientific_report)

    return {
        "run_id": f"{model}--{timestamp_for_id}--{title_slug}",
        "benchmark_id": manifest["benchmark_id"],
        "track": model,
        "title": title,
        "status": status,
        "summary": summary,
        "created_at": recorded.isoformat().replace("+00:00", "Z"),
        "time_ledger": build_time_ledger(recorded),
        "environment": collect_environment(),
        "conditions": conditions,
        "metrics": metrics,
        "artifacts": artifacts,
        "scientific_report": report,
    }


def make_run_payload(args: argparse.Namespace, manifest: dict[str, Any]) -> dict[str, Any]:
    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    return build_run_payload(
        manifest,
        model=args.model,
        title=args.title,
        status=args.status,
        summary=args.summary,
        artifact_paths=args.artifact,
        condition_values=parse_pairs(args.condition),
        metric_values=parse_pairs(args.metric),
        recorded_at=recorded_at,
        slug=args.slug,
        scientific_report={
            "hypothesis": args.hypothesis,
            "method": args.method,
            "result_summary": args.result_summary,
            "limitations": args.limitations,
            "next_steps": args.next_steps,
        },
    )


def run_path_for(manifest: dict[str, Any], track: str, run_id: str) -> Path:
    suffix = run_id.split("--", 1)[1]
    return run_dir_for_track(manifest, track) / f"{suffix}.json"


def compute_composite(run: dict[str, Any], manifest: dict[str, Any]) -> float | None:
    total = 0.0
    for key, weight in manifest["weights"].items():
        value = run["metrics"].get(key)
        if value is None:
            return None
        total += float(value) * float(weight)
    return round(total, 2)


def read_runs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for track in track_ids(manifest):
        run_dir = run_dir_for_track(manifest, track)
        for path in sorted(run_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = relative_path(path)
            data["_composite_score"] = compute_composite(data, manifest)
            runs.append(data)
    runs.sort(key=lambda run: run["created_at"], reverse=True)
    return runs


def validate_run(run: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_keys = {
        "run_id",
        "benchmark_id",
        "track",
        "title",
        "status",
        "summary",
        "created_at",
        "time_ledger",
        "environment",
        "conditions",
        "metrics",
        "artifacts",
        "scientific_report",
    }
    missing = sorted(required_keys - set(run))
    if missing:
        errors.append(f"{run.get('_path', '<unknown>')}: missing keys {', '.join(missing)}")
        return errors

    if run["benchmark_id"] != manifest["benchmark_id"]:
        errors.append(f"{run['_path']}: benchmark_id must be {manifest['benchmark_id']}")

    if run["track"] not in track_ids(manifest):
        errors.append(f"{run['_path']}: unknown track {run['track']}")

    if run["status"] not in set(manifest["status_values"]):
        errors.append(f"{run['_path']}: invalid status {run['status']}")

    expected_metrics = set(metric_keys(manifest))
    actual_metrics = set(run["metrics"])
    if expected_metrics != actual_metrics:
        errors.append(
            f"{run['_path']}: metrics must exactly match manifest keys "
            f"{sorted(expected_metrics)}"
        )

    for key, value in run["metrics"].items():
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            errors.append(f"{run['_path']}: metric {key} must be numeric or null")
            continue
        if not 0 <= numeric <= 100:
            errors.append(f"{run['_path']}: metric {key} must be between 0 and 100")

    if run["status"] == "completed" and run.get("_composite_score") is None:
        errors.append(f"{run['_path']}: completed runs require all scored metrics")

    if not isinstance(run["artifacts"], list):
        errors.append(f"{run['_path']}: artifacts must be a list")
    else:
        for artifact in run["artifacts"]:
            path = artifact.get("path") if isinstance(artifact, dict) else None
            if not path:
                errors.append(f"{run['_path']}: each artifact must include a path")
                continue
            if not (ROOT / path).exists():
                errors.append(f"{run['_path']}: artifact path does not exist: {path}")

    return errors


def validate_runs(manifest: dict[str, Any], runs: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for run in runs:
        errors.extend(validate_run(run, manifest))
    return errors


def score_display(run: dict[str, Any]) -> str:
    score = run.get("_composite_score")
    return f"{score:.2f}" if isinstance(score, (float, int)) else "pending"


def first_artifact_path(run: dict[str, Any]) -> str:
    if not run["artifacts"]:
        return "-"
    return run["artifacts"][0]["path"]


def truncate(text: str, limit: int = 78) -> str:
    stripped = " ".join(text.split())
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."


def render_metrics_table(manifest: dict[str, Any]) -> str:
    lines = ["| Metric | Weight | Description |", "| --- | ---: | --- |"]
    for key, meta in manifest["metrics"].items():
        weight = manifest["weights"][key] * 100
        lines.append(f"| {meta['label']} | {weight:.0f}% | {meta['description']} |")
    return "\n".join(lines)


def render_generation_kinds(generation_manifest: dict[str, Any]) -> str:
    lines = ["| Kind | Status | Rank | Description |", "| --- | --- | ---: | --- |"]
    ordered = sorted(
        generation_manifest["generation_kinds"],
        key=lambda item: item["complexity_rank"],
    )
    for kind in ordered:
        lines.append(
            f"| {kind['id']} | {kind['status']} | {kind['complexity_rank']} | {kind['description']} |"
        )
    return "\n".join(lines)


def render_generation_targets(generation_manifest: dict[str, Any]) -> str:
    lines = ["| Target | Lane | Language | Runtime | Notes |", "| --- | --- | --- | --- | --- |"]
    for target in generation_manifest["targets"]:
        lines.append(
            f"| {target['id']} | {target['lane']} | {target['language']} | {target['runtime']} | {target['notes']} |"
        )
    return "\n".join(lines)


def render_deferred_languages(generation_manifest: dict[str, Any]) -> str:
    return "\n".join(
        f"- `{entry['language']}`: {entry['reason']}"
        for entry in generation_manifest["deferred_languages"]
    )


def render_model_table(model_registry: dict[str, Any]) -> str:
    lines = ["| Model | Provider | Family | Channel | Auth Profile | Tool Profiles | Status |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for model in model_registry["models"]:
        tool_profiles = ", ".join(model.get("tool_profiles", [])) or "-"
        lines.append(
            f"| {model['id']} | {model['provider']} | {model['family']} | {model['execution_channel']} | {model['provider_profile']} | {tool_profiles} | {model['status']} |"
        )
    return "\n".join(lines)


def render_provider_table(provider_registry: dict[str, Any]) -> str:
    lines = ["| Profile | Provider | Transport | Required Env | Notes |", "| --- | --- | --- | --- | --- |"]
    for profile in provider_registry["profiles"]:
        required = ", ".join(profile.get("required_env", [])) or "-"
        any_required = " | ".join("/".join(group) for group in profile.get("required_any_env", []))
        requirement_text = required if not any_required else f"{required}; one of {any_required}" if required != "-" else f"one of {any_required}"
        lines.append(
            f"| {profile['id']} | {profile['provider']} | {profile['transport']} | {requirement_text} | {profile['notes']} |"
        )
    return "\n".join(lines)


def render_leaderboard(manifest: dict[str, Any], runs: list[dict[str, Any]]) -> str:
    lines = ["| Track | Best Run | Status | Score | Recorded At (UTC) | Artifact |", "| --- | --- | --- | ---: | --- | --- |"]
    tracks = track_map(manifest)
    for track_id in track_ids(manifest):
        track = tracks[track_id]
        track_runs = [run for run in runs if run["track"] == track_id]
        scored_runs = [run for run in track_runs if run.get("_composite_score") is not None]
        if scored_runs:
            best_run = max(scored_runs, key=lambda run: run["_composite_score"])
        elif track_runs:
            best_run = track_runs[0]
        else:
            lines.append(f"| {track['label']} | no runs yet | - | - | - | - |")
            continue

        run_link = f"[{best_run['title']}]({best_run['_path']})"
        artifact_link = f"[artifact]({first_artifact_path(best_run)})"
        lines.append(
            f"| {track['label']} | {run_link} | {best_run['status']} | {score_display(best_run)} | "
            f"{best_run['created_at']} | {artifact_link} |"
        )
    return "\n".join(lines)


def render_history(runs: list[dict[str, Any]], limit: int = 10) -> str:
    lines = ["| Recorded At (UTC) | Track | Run | Status | Score | Summary |", "| --- | --- | --- | --- | ---: | --- |"]
    if not runs:
        lines.append("| - | - | no runs yet | - | - | - |")
        return "\n".join(lines)

    for run in runs[:limit]:
        run_link = f"[{run['title']}]({run['_path']})"
        lines.append(
            f"| {run['created_at']} | {run['track']} | {run_link} | {run['status']} | "
            f"{score_display(run)} | {truncate(run['summary'])} |"
        )
    return "\n".join(lines)


def render_readme(
    manifest: dict[str, Any],
    runs: list[dict[str, Any]],
    generation_manifest: dict[str, Any],
    model_registry: dict[str, Any],
    provider_registry: dict[str, Any],
) -> str:
    controlled = ", ".join(f"`{key}`" for key in manifest["controlled_variables"])
    independent = ", ".join(f"`{key}`" for key in manifest["independent_variables"])
    languages = ", ".join(f"`{language}`" for language in manifest["languages"])
    latest_snapshot = runs[0]["created_at"] if runs else "no runs recorded yet"
    core_requirements = "\n".join(
        f"- {requirement}" for requirement in manifest["core_requirements"]
    )

    return f"""# {manifest['repo_title']}

Data-driven benchmark workspace for comparing model-authored 3D frontend systems over time. The current benchmark target is `{manifest['benchmark_id']}`: a WebGPU-first hypertesseract scene with explicit performance, design, multilingual, and reproducibility reporting.

## Benchmark Contract
{core_requirements}

Controlled variables captured in every run: {controlled}

Independent variables encouraged per experiment: {independent}

Target language matrix: {languages}

## Scoring
{render_metrics_table(manifest)}

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
python benchmark_generate.py create-packet \\
  --model o3 \\
  --recipe baseline-webgpu-hypertesseract \\
  --kind one-liner \\
  --target ts-webgpu \\
  --capability wasm \\
  --locale en \\
  --var creative_focus="visual fidelity and clean reporting"
```

3. Create a planning-first execution plan:

```bash
python benchmark_execute.py create-plan \\
  --model o3 \\
  --packet generation/packets/o3/some-packet.json \\
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
python benchmark_execute.py create-result \\
  --plan executions/plans/o3/some-plan.json \\
  --status scaffolded
```

7. Prepare a provider dispatch bundle from the reviewed result:

```bash
python benchmark_execute.py create-dispatch \\
  --result executions/results/o3/some-result.json \\
  --profile openai-responses
```

8. After a real provider response lands, ingest it into the linked result bundle:

```bash
# `curl.sh` auto-sources `.env.local` or `.env` from the repo root.
python benchmark_execute.py ingest-response \\
  --dispatch executions/dispatches/o3/some-dispatch.json \\
  --status captured
```

9. For Codex or Claude-style workspace generations, capture the text response directly into the dispatch bundle:

```bash
python benchmark_execute.py capture-agent-response \\
  --dispatch executions/dispatches/gpt-5.4/some-dispatch.json \\
  --source path/to/response.md
```

10. If you make any manual report edits after ingestion, sync the result bundle again:

```bash
python benchmark_execute.py capture-result \\
  --result executions/results/o3/some-result.json \\
  --status captured
```

11. Promote a reviewed result into a benchmark run:

```bash
python benchmark_execute.py promote-result \\
  --result executions/results/o3/some-result.json \\
  --status completed \\
  --metric visual_fidelity=92 \\
  --metric performance=88 \\
  --metric design_quality=91 \\
  --metric multilingual_quality=86 \\
  --metric scientific_reporting=93 \\
  --metric reproducibility=89
```

12. Build a responsive side-by-side showcase from two results or runs:

```bash
python benchmark_showcase.py create-comparison \\
  --left executions/results/o3/some-result.json \\
  --right executions/results/glm-5.1/some-result.json
```

13. Or resolve the latest result variants directly by model and reasoning effort:

```bash
python benchmark_showcase.py create-latest-comparison \\
  --left-model gpt-5.4 \\
  --left-reasoning-effort medium \\
  --right-model glm-5.1 \\
  --target-id ts-webgpu \\
  --allow-scaffolded
```

14. Rebuild the showcase index when comparisons change:

```bash
python benchmark_showcase.py build-index
```

15. Preview a captured result or showcase locally:

```bash
python benchmark_preview.py serve-result \\
  --result executions/results/gpt-5.4/some-result.json

python benchmark_preview.py serve-showcase \\
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
python benchmark_ledger.py create-run \\
  --model o3 \\
  --title "webgpu hypertesseract v1" \\
  --status completed \\
  --summary "First fully scored benchmark pass." \\
  --artifact generation/packets/o3/some-packet-path.json \\
  --artifact o3/some-artifact-path \\
  --condition generation_kind=one-liner \\
  --condition target_id=ts-webgpu \\
  --condition prompt_packet_id=o3--timestamp--packet-slug \\
  --condition prompt_revision=v1 \\
  --condition toolchain=manual \\
  --condition shader_strategy=webgpu-native \\
  --condition geometry_strategy=procedural \\
  --condition wasm_enabled=true \\
  --condition multilingual_scope=en,es,ja \\
  --metric visual_fidelity=92 \\
  --metric performance=88 \\
  --metric design_quality=91 \\
  --metric multilingual_quality=86 \\
  --metric scientific_reporting=93 \\
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
Central system prompt: [`{generation_manifest['system_prompt_path']}`]({generation_manifest['system_prompt_path']})

Preferred orchestration stance: `{generation_manifest['orchestration_strategy']['primary']}`. LangChain/LangSmith remain optional rather than mandatory so the benchmark contract stays lightweight and DSPy-friendly.

### Prompt Complexity Ladder
{render_generation_kinds(generation_manifest)}

### Supported Targets
{render_generation_targets(generation_manifest)}

Deferred for now:
{render_deferred_languages(generation_manifest)}

## Model Registry
{render_model_table(model_registry)}

## Provider Profiles
{render_provider_table(provider_registry)}

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
{render_leaderboard(manifest, runs)}

## Recent History
{render_history(runs)}

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

Latest recorded snapshot in this README: `{latest_snapshot}`.
"""


def render_history_exports(runs: list[dict[str, Any]]) -> tuple[str, str]:
    exported_runs = []
    for run in runs:
        record = {key: value for key, value in run.items() if not key.startswith("_")}
        record["composite_score"] = run.get("_composite_score")
        record["run_file"] = run.get("_path")
        exported_runs.append(record)

    json_text = json.dumps(exported_runs, indent=2, ensure_ascii=False) + "\n"
    jsonl_lines = [json.dumps(record, ensure_ascii=False) for record in exported_runs]
    jsonl_text = "\n".join(jsonl_lines) + ("\n" if jsonl_lines else "")
    return json_text, jsonl_text


def build_outputs(manifest: dict[str, Any], runs: list[dict[str, Any]], check: bool) -> int:
    generation_manifest = load_generation_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    readme_text = render_readme(
        manifest,
        runs,
        generation_manifest,
        model_registry,
        provider_registry,
    )
    history_json_text, history_jsonl_text = render_history_exports(runs)

    expected = {
        README_PATH: readme_text,
        HISTORY_JSON_PATH: history_json_text,
        HISTORY_JSONL_PATH: history_jsonl_text,
    }

    if check:
        stale = []
        for path, content in expected.items():
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current != content:
                stale.append(path.name)
        if stale:
            print("Generated files are stale:", ", ".join(stale), file=sys.stderr)
            return 1
        return 0

    for path, content in expected.items():
        write_text_if_changed(path, content)
    return 0


def cmd_create_run(args: argparse.Namespace) -> int:
    manifest = load_benchmark_manifest()
    if args.model not in track_ids(manifest):
        raise SystemExit(f"Unknown model track: {args.model}")

    payload = make_run_payload(args, manifest)
    payload["_composite_score"] = compute_composite(payload, manifest)
    temp_run = dict(payload)
    temp_run["_path"] = relative_path(run_path_for(manifest, args.model, payload["run_id"]))
    errors = validate_run(temp_run, manifest)
    payload.pop("_composite_score", None)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    target = run_path_for(manifest, args.model, payload["run_id"])
    if target.exists():
        print(f"Run already exists: {relative_path(target)}", file=sys.stderr)
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(relative_path(target))
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    manifest = load_benchmark_manifest()
    runs = read_runs(manifest)
    errors = validate_runs(manifest, runs)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(runs)} run(s).")
    return 0


def cmd_build_readme(args: argparse.Namespace) -> int:
    manifest = load_benchmark_manifest()
    runs = read_runs(manifest)
    errors = validate_runs(manifest, runs)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return build_outputs(manifest, runs, check=args.check)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesseract benchmark ledger CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-run", help="Create a timestamped run record")
    create.add_argument("--model", required=True, help="Track id, for example o3 or gpt-5.4")
    create.add_argument("--title", required=True, help="Human-readable run title")
    create.add_argument("--slug", help="Optional slug override used in the filename")
    create.add_argument("--status", required=True, help="planned, in-progress, completed, archived")
    create.add_argument("--summary", required=True, help="Short run summary for the README history")
    create.add_argument(
        "--artifact",
        action="append",
        default=[],
        required=True,
        help="Artifact path relative to the repo root. Repeat as needed.",
    )
    create.add_argument(
        "--condition",
        action="append",
        default=[],
        help="Condition as KEY=VALUE. Repeat as needed.",
    )
    create.add_argument(
        "--metric",
        action="append",
        default=[],
        help="Metric as KEY=VALUE using 0-100 scores. Repeat as needed.",
    )
    create.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create.add_argument("--hypothesis", default="", help="Scientific report hypothesis")
    create.add_argument("--method", default="", help="Scientific report method")
    create.add_argument("--result-summary", default="", help="Scientific report results")
    create.add_argument("--limitations", default="", help="Scientific report limitations")
    create.add_argument("--next-steps", default="", help="Scientific report next steps")
    create.set_defaults(func=cmd_create_run)

    validate = subparsers.add_parser("validate", help="Validate all run files")
    validate.set_defaults(func=cmd_validate)

    build = subparsers.add_parser("build-readme", help="Regenerate README and history exports")
    build.add_argument("--check", action="store_true", help="Fail instead of writing when files are stale")
    build.set_defaults(func=cmd_build_readme)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
