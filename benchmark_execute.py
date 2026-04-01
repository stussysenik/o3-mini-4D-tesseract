from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from importlib import metadata
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any

from benchmark_core import (
    ROOT,
    content_hash,
    evaluate_env_requirements,
    execution_dispatch_dir_for_model,
    execution_output_dir_for_model,
    execution_plan_dir_for_model,
    execution_request_bundle_dir_for_model,
    execution_result_dir_for_model,
    index_by_id,
    load_benchmark_manifest,
    load_execution_manifest,
    load_model_registry,
    load_pricing_manifest,
    load_provider_registry,
    now_utc,
    parse_pairs,
    parse_timestamp,
    provider_ids,
    provider_map,
    read_env,
    relative_path,
    track_ids,
    unique_strings,
    write_json_if_changed,
    write_text_if_changed,
)
from benchmark_generate import (
    build_markdown_packet,
    build_packet,
    packet_path_for,
)
from benchmark_ledger import (
    build_run_payload,
    compute_composite,
    run_path_for,
    validate_run,
)

try:
    import dspy
except ImportError as exc:  # pragma: no cover - behavior validated via CLI
    dspy = None
    DSPY_IMPORT_ERROR = str(exc)
else:
    DSPY_IMPORT_ERROR = None


if dspy is not None:
    class BenchmarkExecutionPlanSignature(dspy.Signature):
        """Plan a benchmark generation execution from a packet and model profile."""

        model_profile = dspy.InputField(desc="Model registry entry as JSON text")
        prompt_packet = dspy.InputField(desc="Prompt packet as JSON text")
        openspec_context = dspy.InputField(desc="Relevant OpenSpec capability summary")
        execution_plan = dspy.OutputField(desc="Stepwise execution plan")


    class BenchmarkExecutionPlanner(dspy.Module):
        def __init__(self) -> None:
            super().__init__()
            self.plan = dspy.Predict(BenchmarkExecutionPlanSignature)

        def forward(
            self,
            model_profile: str,
            prompt_packet: str,
            openspec_context: str,
        ) -> Any:
            return self.plan(
                model_profile=model_profile,
                prompt_packet=prompt_packet,
                openspec_context=openspec_context,
            )


def dspy_status() -> dict[str, Any]:
    version = None
    try:
        version = metadata.version("dspy")
    except metadata.PackageNotFoundError:
        version = None

    return {
        "available": dspy is not None,
        "version": version,
        "import_error": DSPY_IMPORT_ERROR,
        "signature": "BenchmarkExecutionPlanSignature" if dspy is not None else None,
        "module": "BenchmarkExecutionPlanner" if dspy is not None else None,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def display_path(path: Path) -> str:
    try:
        return relative_path(path)
    except ValueError:
        return str(path)


REQUIRED_GENERATION_SECTIONS = (
    "Implementation Summary",
    "Target Declaration",
    "Capability Declaration",
    "Files",
    "Benchmark Report",
    "Known Limitations",
)

REASONING_EFFORT_VALUES = ("low", "medium", "high", "xhigh")


def request_settings_from_args(args: argparse.Namespace) -> dict[str, Any]:
    settings: dict[str, Any] = {}
    reasoning_effort = getattr(args, "reasoning_effort", None)
    if reasoning_effort:
        settings["reasoning_effort"] = reasoning_effort
    max_output_tokens = getattr(args, "max_output_tokens", None)
    if max_output_tokens is not None:
        settings["max_output_tokens"] = max_output_tokens
    return settings


def normalize_usage_payload(usage: dict[str, Any] | None) -> dict[str, int] | None:
    if not isinstance(usage, dict):
        return None

    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0
    total_tokens = usage.get("total_tokens")
    if total_tokens is None:
        total_tokens = input_tokens + output_tokens

    input_details = usage.get("input_tokens_details", {})
    output_details = usage.get("output_tokens_details", {})
    cached_input_tokens = (
        usage.get("cached_input_tokens")
        or input_details.get("cached_tokens")
        or 0
    )
    reasoning_tokens = (
        usage.get("reasoning_tokens")
        or output_details.get("reasoning_tokens")
        or 0
    )
    billable_input_tokens = max(int(input_tokens) - int(cached_input_tokens), 0)

    return {
        "input_tokens": int(input_tokens),
        "cached_input_tokens": int(cached_input_tokens),
        "billable_input_tokens": int(billable_input_tokens),
        "output_tokens": int(output_tokens),
        "reasoning_tokens": int(reasoning_tokens),
        "total_tokens": int(total_tokens),
    }


def pricing_entry_for_model(
    pricing_manifest: dict[str, Any],
    *,
    model_id: str,
    provider_model: str | None,
) -> dict[str, Any] | None:
    for entry in pricing_manifest.get("models", []):
        if entry.get("model_id") == model_id:
            return entry
        if provider_model and entry.get("provider_model") == provider_model:
            return entry
    return None


def source_entry_for_pricing(
    pricing_manifest: dict[str, Any],
    source_id: str | None,
) -> dict[str, Any] | None:
    if not source_id:
        return None
    for source in pricing_manifest.get("sources", []):
        if source.get("id") == source_id:
            return source
    return None


def estimate_cost_from_usage(
    usage: dict[str, int] | None,
    pricing_entry: dict[str, Any] | None,
    pricing_source: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if usage is None or pricing_entry is None:
        return None

    input_cost = (usage["billable_input_tokens"] / 1_000_000) * float(pricing_entry["input_per_million_usd"])
    cached_input_cost = (usage["cached_input_tokens"] / 1_000_000) * float(pricing_entry.get("cached_input_per_million_usd", 0.0))
    output_cost = (usage["output_tokens"] / 1_000_000) * float(pricing_entry["output_per_million_usd"])
    total_cost = input_cost + cached_input_cost + output_cost

    estimate = {
        "currency": "USD",
        "estimated_total_usd": round(total_cost, 8),
        "estimated_input_usd": round(input_cost, 8),
        "estimated_cached_input_usd": round(cached_input_cost, 8),
        "estimated_output_usd": round(output_cost, 8),
        "pricing": {
            "model_id": pricing_entry.get("model_id"),
            "provider_model": pricing_entry.get("provider_model"),
            "effective_date": pricing_entry.get("effective_date"),
            "input_per_million_usd": pricing_entry.get("input_per_million_usd"),
            "cached_input_per_million_usd": pricing_entry.get("cached_input_per_million_usd"),
            "output_per_million_usd": pricing_entry.get("output_per_million_usd"),
        },
    }
    if pricing_source is not None:
        estimate["pricing_source"] = {
            "id": pricing_source.get("id"),
            "url": pricing_source.get("url"),
            "retrieved_at": pricing_source.get("retrieved_at"),
        }
    return estimate


def normalize_heading_candidate(line: str) -> str:
    candidate = line.strip()
    candidate = re.sub(r"^#{1,6}\s*", "", candidate)
    candidate = re.sub(r"^\d+[\.\)]\s*", "", candidate)
    candidate = re.sub(r"^[-*+]\s*", "", candidate)
    candidate = candidate.strip()
    if candidate.startswith("**") and candidate.endswith("**") and len(candidate) >= 4:
        candidate = candidate[2:-2]
    candidate = candidate.strip().strip("`").strip().rstrip(":").strip()
    return candidate.casefold()


def split_markdown_sections(text: str, section_titles: tuple[str, ...] = REQUIRED_GENERATION_SECTIONS) -> dict[str, str]:
    title_map = {title.casefold(): title for title in section_titles}
    buckets = {title: [] for title in section_titles}
    current: str | None = None
    in_code_fence = False

    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if not in_code_fence:
                normalized = normalize_heading_candidate(line)
                if normalized in title_map:
                    current = title_map[normalized]
                    continue
            in_code_fence = not in_code_fence
            if current is not None:
                buckets[current].append(line)
            continue

        if not in_code_fence:
            normalized = normalize_heading_candidate(line)
            if normalized in title_map:
                current = title_map[normalized]
                continue

        if current is not None:
            buckets[current].append(line)

    return {title: "\n".join(lines).strip() for title, lines in buckets.items()}


def parse_markdown_list(body: str) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^[-*+]\s+", stripped):
            items.append(re.sub(r"^[-*+]\s+", "", stripped))
        else:
            items.append(stripped)
    return items


def sanitize_generated_relative_path(raw: str) -> str:
    candidate = raw.strip().strip("`").replace("\\", "/")
    candidate = re.sub(r"^(?:\./)+", "", candidate)
    if candidate.startswith("generated/"):
        candidate = candidate.split("/", 1)[1]
    candidate = candidate.strip("/")
    if not candidate:
        raise ValueError("Empty generated file path is not allowed.")

    path = PurePosixPath(candidate)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe generated file path: {raw}")
    return path.as_posix()


def looks_like_relative_file_path(candidate: str) -> bool:
    value = candidate.strip().strip("`")
    if not value or value.endswith(":"):
        return False
    if any(char in value for char in "<>|"):
        return False
    filename = PurePosixPath(value).name
    return "/" in value or "." in filename or filename in {
        "README",
        "README.md",
        "Dockerfile",
        "Makefile",
        "package.json",
        "index.html",
    }


def extract_declared_file_path(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        return None

    candidate = re.sub(r"^#{1,6}\s*", "", stripped)
    candidate = re.sub(r"^[-*+]\s*", "", candidate)
    match = re.match(r"^(?:file|path)\s*:\s*`?([^`]+?)`?$", candidate, re.IGNORECASE)
    if match:
        return sanitize_generated_relative_path(match.group(1))

    if looks_like_relative_file_path(candidate):
        return sanitize_generated_relative_path(candidate)
    return None


def extract_file_path_from_fence_info(info: str) -> str | None:
    match = re.search(r"(?:file|filename|path|title)\s*=\s*[\"']?([^\"'\s]+)", info, re.IGNORECASE)
    if match:
        return sanitize_generated_relative_path(match.group(1))

    tokens = [token for token in info.split() if token]
    for token in tokens[:2]:
        if looks_like_relative_file_path(token):
            return sanitize_generated_relative_path(token)
    return None


def extract_language_from_fence_info(info: str) -> str | None:
    tokens = [token for token in info.split() if token]
    if not tokens:
        return None
    first = tokens[0]
    if looks_like_relative_file_path(first) or "=" in first:
        return None
    return first


def extract_fenced_file_entries(body: str) -> tuple[list[dict[str, str | None]], list[str]]:
    entries: list[dict[str, str | None]] = []
    warnings: list[str] = []
    pending_path: str | None = None
    lines = body.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        declared_path = extract_declared_file_path(line)
        if declared_path is not None:
            pending_path = declared_path
            index += 1
            continue

        if line.lstrip().startswith("```"):
            info = line.lstrip()[3:].strip()
            block_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].lstrip().startswith("```"):
                block_lines.append(lines[index])
                index += 1

            resolved_path = pending_path or extract_file_path_from_fence_info(info)
            if resolved_path is None:
                warnings.append("Skipped unnamed code fence in Files section.")
            else:
                entries.append(
                    {
                        "path": resolved_path,
                        "language": extract_language_from_fence_info(info),
                        "content": "\n".join(block_lines).rstrip() + "\n",
                    }
                )
            pending_path = None
            if index < len(lines):
                index += 1
            continue

        index += 1

    seen_paths: set[str] = set()
    deduped_entries: list[dict[str, str | None]] = []
    for entry in reversed(entries):
        path = str(entry["path"])
        if path in seen_paths:
            warnings.append(f"Duplicate generated file path encountered; kept last occurrence for {path}.")
            continue
        seen_paths.add(path)
        deduped_entries.append(entry)
    deduped_entries.reverse()
    warnings = unique_strings(warnings)
    return deduped_entries, warnings


def extract_first_json_code_block(body: str) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    lines = body.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].lstrip()
        if not line.startswith("```"):
            index += 1
            continue
        info = line[3:].strip().casefold()
        block_lines: list[str] = []
        index += 1
        while index < len(lines) and not lines[index].lstrip().startswith("```"):
            block_lines.append(lines[index])
            index += 1
        if info in {"json", "application/json", ""}:
            raw = "\n".join(block_lines).strip()
            if not raw:
                warnings.append("Encountered an empty JSON code block in Benchmark Report.")
                return None, warnings
            try:
                return json.loads(raw), warnings
            except json.JSONDecodeError as exc:
                warnings.append(f"Could not parse benchmark report JSON block: {exc}")
                return None, warnings
        index += 1
    warnings.append("No JSON code block found in Benchmark Report.")
    return None, warnings


def flatten_text_segments(value: Any) -> list[str]:
    segments: list[str] = []
    if value is None:
        return segments
    if isinstance(value, str):
        if value.strip():
            segments.append(value)
        return segments
    if isinstance(value, list):
        for item in value:
            segments.extend(flatten_text_segments(item))
        return segments
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            text = value["text"]
            if text.strip():
                segments.append(text)
        if isinstance(value.get("output_text"), str):
            text = value["output_text"]
            if text.strip():
                segments.append(text)
        if isinstance(value.get("value"), str) and value.get("type") in {"text", "output_text"}:
            text = value["value"]
            if text.strip():
                segments.append(text)
        for key in ("content", "message", "output", "choices"):
            if key in value:
                segments.extend(flatten_text_segments(value[key]))
        return segments
    return segments


def extract_assistant_text_from_payload(payload: dict[str, Any], transport: str) -> tuple[str | None, list[str]]:
    warnings: list[str] = []

    if transport == "responses-api":
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text, warnings
        output = payload.get("output")
        segments = flatten_text_segments(output)
        if segments:
            return "\n\n".join(segment.strip() for segment in segments if segment.strip()), warnings
        warnings.append("No assistant text found in Responses API payload.")
        return None, warnings

    if transport == "openai-compatible":
        choices = payload.get("choices", [])
        for choice in choices:
            message = choice.get("message", {})
            content = message.get("content")
            segments = flatten_text_segments(content)
            if segments:
                return "\n\n".join(segment.strip() for segment in segments if segment.strip()), warnings
        warnings.append("No assistant text found in chat completions payload.")
        return None, warnings

    if transport == "messages-api":
        segments = flatten_text_segments(payload.get("content"))
        if segments:
            return "\n\n".join(segment.strip() for segment in segments if segment.strip()), warnings
        warnings.append("No assistant text found in Messages API payload.")
        return None, warnings

    segments = flatten_text_segments(payload)
    if segments:
        return "\n\n".join(segment.strip() for segment in segments if segment.strip()), warnings
    warnings.append("No assistant text found in provider payload.")
    return None, warnings


def extract_response_metadata(payload: dict[str, Any], transport: str) -> dict[str, Any]:
    metadata = {
        "response_id": payload.get("id"),
        "provider_model": payload.get("model"),
        "status": payload.get("status"),
        "usage": payload.get("usage"),
        "finish_reasons": [],
    }

    if transport == "openai-compatible":
        finish_reasons = [
            choice.get("finish_reason")
            for choice in payload.get("choices", [])
            if isinstance(choice, dict) and choice.get("finish_reason")
        ]
        metadata["finish_reasons"] = unique_strings([str(value) for value in finish_reasons])
        metadata["status"] = payload.get("object")
        return metadata

    if transport == "messages-api":
        stop_reason = payload.get("stop_reason")
        metadata["finish_reasons"] = [str(stop_reason)] if stop_reason else []
        metadata["status"] = stop_reason
        return metadata

    if transport == "responses-api":
        finish_reasons = [
            item.get("status")
            for item in payload.get("output", [])
            if isinstance(item, dict) and item.get("status")
        ]
        metadata["finish_reasons"] = unique_strings([str(value) for value in finish_reasons])
        return metadata

    return metadata


def plan_path_for(model_id: str, plan_id: str, suffix: str) -> Path:
    serial = plan_id.split("--", 1)[1]
    return execution_plan_dir_for_model(model_id) / f"{serial}.{suffix}"


def result_path_for(model_id: str, result_id: str, suffix: str) -> Path:
    serial = result_id.split("--", 1)[1]
    return execution_result_dir_for_model(model_id) / f"{serial}.{suffix}"


def output_root_for(model_id: str, result_id: str) -> Path:
    serial = result_id.split("--", 1)[1]
    return execution_output_dir_for_model(model_id) / serial


def dispatch_path_for(model_id: str, dispatch_id: str, suffix: str) -> Path:
    serial = dispatch_id.split("--", 1)[1]
    return execution_dispatch_dir_for_model(model_id) / f"{serial}.{suffix}"


def request_bundle_root_for(model_id: str, dispatch_id: str) -> Path:
    serial = dispatch_id.split("--", 1)[1]
    return execution_request_bundle_dir_for_model(model_id) / serial


def load_packet(packet_path: Path) -> dict[str, Any]:
    return load_json(packet_path)


def semantic_packet_payload(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "benchmark_id": packet["benchmark_id"],
        "model_id": packet["model_id"],
        "recipe_id": packet["recipe_id"],
        "scene_id": packet["scene_id"],
        "generation_kind": packet["generation_kind"],
        "target": packet["target"],
        "selected_capabilities": packet["selected_capabilities"],
        "selected_locales": packet["selected_locales"],
        "variables": packet["variables"],
        "messages": {
            "system_prompt": packet["messages"]["system_prompt"],
            "scene_prompt": packet["messages"]["scene_prompt"],
            "user_prompt": packet["messages"]["user_prompt"],
        },
    }


def resolve_profile_set(model: dict[str, Any], provider_registry: dict[str, Any]) -> dict[str, Any]:
    profiles = provider_map(provider_registry)
    resolved = {
        "primary": profiles[model["provider_profile"]],
        "tools": [profiles[profile_id] for profile_id in model.get("tool_profiles", [])],
    }
    return resolved


def auth_status_for_profile(profile: dict[str, Any]) -> dict[str, Any]:
    requirements = evaluate_env_requirements(profile)
    return {
        "profile_id": profile["id"],
        "label": profile["label"],
        "provider": profile["provider"],
        "transport": profile["transport"],
        "docs_url": profile["docs_url"],
        "requirements": requirements,
        "satisfied": requirements["satisfied"],
    }


def auth_status_for_model(model: dict[str, Any], provider_registry: dict[str, Any]) -> dict[str, Any]:
    profile_set = resolve_profile_set(model, provider_registry)
    primary = auth_status_for_profile(profile_set["primary"])
    tools = [auth_status_for_profile(profile) for profile in profile_set["tools"]]
    return {
        "model_id": model["id"],
        "primary": primary,
        "tools": tools,
    }


def render_profile_config(
    profile: dict[str, Any],
    config_format: str,
    include_secrets: bool,
) -> str:
    derived = dict(profile.get("derived_env", {}))
    defaults = dict(profile.get("defaults", {}))
    required = {name: "" for name in profile.get("required_env", [])}
    optional = {name: "" for name in profile.get("optional_env", [])}

    resolved_env: dict[str, str] = {}
    resolved_env.update(required)
    resolved_env.update(optional)
    for key, value in defaults.items():
        env_key = {
            "base_url": profile["optional_env"][0] if profile.get("optional_env") else "BASE_URL"
        }.get(key, key.upper())
        resolved_env[env_key] = value
    resolved_env.update(derived)

    for key in list(resolved_env):
        value = resolved_env[key]
        if isinstance(value, str) and value.startswith("$"):
            source = value[1:]
            resolved_env[key] = read_env(source) if include_secrets and read_env(source) else f"${source}"
        elif include_secrets and read_env(key):
            resolved_env[key] = read_env(key) or ""

    if config_format == "claude-settings":
        claude_env = dict(derived)
        if "API_TIMEOUT_MS" in resolved_env:
            claude_env["API_TIMEOUT_MS"] = resolved_env["API_TIMEOUT_MS"]
        for key in list(claude_env):
            value = claude_env[key]
            if isinstance(value, str) and value.startswith("$"):
                source = value[1:]
                claude_env[key] = read_env(source) if include_secrets and read_env(source) else f"${source}"
        return json.dumps({"env": claude_env}, indent=2, ensure_ascii=False)

    if config_format == "json":
        return json.dumps({"env": resolved_env}, indent=2, ensure_ascii=False)

    lines = [f'export {key}="{value}"' for key, value in resolved_env.items()]
    return "\n".join(lines)


def build_steps(
    model: dict[str, Any],
    mode: str,
    auth_status: dict[str, Any],
) -> list[dict[str, Any]]:
    primary = auth_status["primary"]
    auth_details = (
        f"Primary profile `{primary['profile_id']}` "
        f"is {'ready' if primary['satisfied'] else 'not ready'}."
    )
    return [
        {
            "id": "validate-inputs",
            "title": "Validate packet and model compatibility",
            "status": "pending",
            "details": "Confirm the packet target, model id, and benchmark id are internally consistent.",
        },
        {
            "id": "prepare-context",
            "title": "Assemble DSPy/OpenSpec planning context",
            "status": "pending",
            "details": "Prepare model profile, prompt packet, provider auth state, and relevant OpenSpec references for execution.",
        },
        {
            "id": "credential-check",
            "title": "Check provider credentials",
            "status": "pending",
            "details": auth_details,
        },
        {
            "id": "dispatch",
            "title": "Dispatch execution",
            "status": "pending",
            "details": f"Dispatch using execution channel `{model['execution_channel']}` in mode `{mode}`.",
        },
        {
            "id": "collect-output",
            "title": "Collect output and benchmark report",
            "status": "pending",
            "details": "Capture generated files, benchmark report fields, and capability declarations.",
        },
        {
            "id": "register-artifacts",
            "title": "Register output artifacts and eventual run",
            "status": "pending",
            "details": "Attach packet, execution plan, generated output, and benchmark run into the SSOT catalog.",
        },
    ]


def build_markdown_plan(plan: dict[str, Any]) -> str:
    steps = "\n".join(
        f"- `{step['id']}`: {step['title']} — {step['details']}"
        for step in plan["steps"]
    )
    artifacts = "\n".join(f"- `{artifact['path']}`" for artifact in plan["artifacts"])
    openspec_refs = "\n".join(f"- `{path}`" for path in plan["openspec_refs"])

    return f"""# Execution Plan: {plan['plan_id']}

## Metadata
- Model: `{plan['model_id']}`
- Packet: `{plan['packet_id']}`
- Planner Engine: `{plan['planner_engine']}`
- Execution Mode: `{plan['execution_mode']}`
- Status: `{plan['status']}`
- Created At: `{plan['created_at']}`

## Model Profile
```json
{json.dumps(plan['model_profile'], indent=2, ensure_ascii=False)}
```

## Auth Status
```json
{json.dumps(plan['auth_status'], indent=2, ensure_ascii=False)}
```

## Packet Reference
Source: `{plan['packet_path']}`

## DSPy Status
```json
{json.dumps(plan['dspy_status'], indent=2, ensure_ascii=False)}
```

## Steps
{steps}

## OpenSpec References
{openspec_refs}

## Planned Artifacts
{artifacts}
"""


def build_markdown_result(result: dict[str, Any]) -> str:
    artifacts = "\n".join(f"- `{artifact['path']}` ({artifact['type']})" for artifact in result["artifacts"])
    openspec_refs = "\n".join(f"- `{path}`" for path in result["openspec_refs"])
    notes = "\n".join(f"- {note}" for note in result["notes"])

    return f"""# Execution Result: {result['result_id']}

## Metadata
- Model: `{result['model_id']}`
- Plan: `{result['plan_id']}`
- Packet: `{result['packet_id']}`
- Execution Mode: `{result['execution_mode']}`
- Status: `{result['status']}`
- Output Root: `{result['output_root']}`
- Created At: `{result['created_at']}`

## Summary
{result['summary']}

## Benchmark Report
```json
{json.dumps(result['benchmark_report'], indent=2, ensure_ascii=False)}
```

## Review State
```json
{json.dumps(result['review_state'], indent=2, ensure_ascii=False)}
```

## Artifacts
{artifacts}

## OpenSpec References
{openspec_refs}

## Notes
{notes}
"""


def build_markdown_dispatch(dispatch: dict[str, Any]) -> str:
    dispatch = dispatch_with_defaults(dispatch)
    request_artifacts = "\n".join(
        f"- `{artifact['path']}` ({artifact['type']})" for artifact in dispatch["request_artifacts"]
    )
    tool_profiles = ", ".join(dispatch["tool_profile_ids"]) or "-"
    response_capture_block = ""
    if dispatch.get("response_capture"):
        response_capture_block = f"""

## Response Capture
```json
{json.dumps(dispatch['response_capture'], indent=2, ensure_ascii=False)}
```
"""
    request_settings_block = ""
    if dispatch.get("request_settings"):
        request_settings_block = f"""

## Request Settings
```json
{json.dumps(dispatch['request_settings'], indent=2, ensure_ascii=False)}
```
"""
    request_execution_block = ""
    if dispatch.get("request_execution"):
        request_execution_block = f"""

## Request Execution
```json
{json.dumps(dispatch['request_execution'], indent=2, ensure_ascii=False)}
```
"""
    return f"""# Provider Dispatch: {dispatch['dispatch_id']}

## Metadata
- Model: `{dispatch['model_id']}`
- Result: `{dispatch['result_id']}`
- Provider Profile: `{dispatch['provider_profile_id']}`
- Tool Profiles: `{tool_profiles}`
- Execution Channel: `{dispatch['execution_channel']}`
- Transport: `{dispatch['transport']}`
- Status: `{dispatch['status']}`
- Request Bundle: `{dispatch['request_bundle_root']}`
- Created At: `{dispatch['created_at']}`

## Invocation
```json
{json.dumps(dispatch['invocation'], indent=2, ensure_ascii=False)}
```

## Request Contract
```json
{json.dumps(dispatch['request_contract'], indent=2, ensure_ascii=False)}
```
{request_settings_block}
{request_execution_block}

## Response Contract
```json
{json.dumps(dispatch['response_contract'], indent=2, ensure_ascii=False)}
```
{response_capture_block}

## Request Artifacts
{request_artifacts}
"""


def build_result_benchmark_report(
    benchmark_manifest: dict[str, Any],
    packet: dict[str, Any],
    result_id: str,
) -> dict[str, Any]:
    recommended_conditions = dict(benchmark_manifest["recommended_conditions"])
    recommended_conditions.update(
        {
            "generation_kind": packet["generation_kind"],
            "target_id": packet["target"]["id"],
            "prompt_packet_id": packet["packet_id"],
            "wasm_enabled": "wasm" in packet["selected_capabilities"],
            "multilingual_scope": ",".join(packet["selected_locales"]),
        }
    )
    return {
        "report_version": 1,
        "result_id": result_id,
        "benchmark_id": packet["benchmark_id"],
        "generation_kind": packet["generation_kind"],
        "target_id": packet["target"]["id"],
        "target_language": packet["target"]["language"],
        "runtime": packet["target"]["runtime"],
        "lane": packet["target"]["lane"],
        "used_capabilities": packet["selected_capabilities"],
        "requested_locales": packet["selected_locales"],
        "wasm_used": "wasm" in packet["selected_capabilities"],
        "webgpu_used": "webgpu" in packet["selected_capabilities"],
        "fallback_path": "undeclared",
        "known_gaps": [
            "Generated implementation files have not been attached yet.",
            "Benchmark scoring has not been completed yet.",
        ],
        "hypothesis": (
            "This prompt packet should produce a browser-native hypertesseract scene "
            "that is valid for later benchmark scoring."
        ),
        "method": (
            "Use the execution plan as the authoritative dispatch contract, store the raw "
            "output bundle here, and score only after review."
        ),
        "result_summary": "Scaffolded result bundle created. Awaiting generated files and review.",
        "limitations": [
            "This is a scaffolded artifact, not a scored benchmark run.",
            "Provider execution has not been captured in this record yet.",
        ],
        "next_steps": [
            "Run the linked dispatch bundle and ingest the provider response via benchmark_execute.py ingest-response.",
            "Capture screenshots or recordings under executions/output/.../captures/.",
            "Update this report after review, then create a scored benchmark run if warranted.",
        ],
        "score_ready": False,
        "scoring_status": "pending-review",
        "recommended_run_conditions": recommended_conditions,
    }


def build_result_bundle_manifest(result: dict[str, Any]) -> dict[str, Any]:
    review_state = result.get("review_state", {})
    manifest = {
        "version": 1,
        "result_id": result["result_id"],
        "model_id": result["model_id"],
        "plan_id": result["plan_id"],
        "packet_id": result["packet_id"],
        "status": result["status"],
        "created_at": result["created_at"],
        "output_root": result["output_root"],
        "expected_children": [
            "README.md",
            "bundle_manifest.json",
            "benchmark_report.json",
            "generated/README.md",
            "captures/README.md",
        ],
    }
    if review_state.get("linked_run_id"):
        manifest["linked_run_id"] = review_state["linked_run_id"]
    if review_state.get("linked_run_path"):
        manifest["linked_run_path"] = review_state["linked_run_path"]
    return manifest


def stringify_report_field(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    if isinstance(value, dict):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value)


def append_unique_notes(existing: list[str], additions: list[str]) -> list[str]:
    return unique_strings([*existing, *[note for note in additions if note]])


def result_bundle_paths(result: dict[str, Any]) -> dict[str, Path]:
    root = ROOT / result["output_root"]
    return {
        "root": root,
        "readme": root / "README.md",
        "manifest": root / "bundle_manifest.json",
        "report": root / "benchmark_report.json",
        "generated_readme": root / "generated" / "README.md",
        "captures_readme": root / "captures" / "README.md",
    }


def infer_output_artifact_type(output_root: Path, path: Path) -> str:
    rel = path.relative_to(output_root).as_posix()
    if rel == "README.md":
        return "output-bundle-doc"
    if rel == "bundle_manifest.json":
        return "output-bundle-manifest"
    if rel == "benchmark_report.json":
        return "benchmark-report"
    if rel == "generated/README.md":
        return "generated-output-slot"
    if rel == "generated/generation_manifest.json":
        return "generated-manifest"
    if rel == "generated/response.md":
        return "generated-response-markdown"
    if rel.startswith("generated/"):
        return "generated-file"
    if rel == "captures/README.md":
        return "capture-output-slot"
    if rel.startswith("captures/"):
        return "capture-file"
    return "bundle-file"


def result_artifact_inventory(result: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = [
        {
            "path": relative_path(result_path_for(result["model_id"], result["result_id"], "json")),
            "type": "execution-result",
        },
        {
            "path": relative_path(result_path_for(result["model_id"], result["result_id"], "md")),
            "type": "execution-result-doc",
        },
    ]

    output_root = ROOT / result["output_root"]
    if output_root.exists():
        for path in sorted(item for item in output_root.rglob("*") if item.is_file()):
            artifacts.append(
                {
                    "path": relative_path(path),
                    "type": infer_output_artifact_type(output_root, path),
                }
            )

    dispatch_dir = execution_dispatch_dir_for_model(result["model_id"])
    if dispatch_dir.exists():
        for path in sorted(dispatch_dir.glob("*.json")):
            dispatch = load_json(path)
            if dispatch["result_id"] != result["result_id"]:
                continue
            artifacts.extend(dispatch_artifact_inventory(dispatch))

    review_state = result.get("review_state", {})
    linked_run_path = review_state.get("linked_run_path")
    if linked_run_path and (ROOT / linked_run_path).exists():
        artifacts.append({"path": linked_run_path, "type": "linked-run"})

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for artifact in artifacts:
        path = artifact["path"]
        if path in seen:
            continue
        seen.add(path)
        deduped.append(artifact)
    return deduped


def write_result_files(result: dict[str, Any], *, sync_bundle_report: bool) -> None:
    json_path = result_path_for(result["model_id"], result["result_id"], "json")
    md_path = result_path_for(result["model_id"], result["result_id"], "md")
    bundle_paths = result_bundle_paths(result)

    write_text_if_changed(json_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    write_text_if_changed(md_path, build_markdown_result(result))
    write_text_if_changed(
        bundle_paths["manifest"],
        json.dumps(build_result_bundle_manifest(result), indent=2, ensure_ascii=False) + "\n",
    )
    if sync_bundle_report:
        write_text_if_changed(
            bundle_paths["report"],
            json.dumps(result["benchmark_report"], indent=2, ensure_ascii=False) + "\n",
        )


def sync_result_record(result_path: Path, note: str | None = None) -> None:
    result = load_json(result_path)
    result["artifacts"] = result_artifact_inventory(result)
    if note:
        result["notes"] = append_unique_notes(result.get("notes", []), [note])
    write_result_files(result, sync_bundle_report=False)


def auto_response_source_for_dispatch(dispatch: dict[str, Any]) -> Path | None:
    bundle_paths = dispatch_bundle_paths(dispatch)
    for key in ("response_raw_json", "response_raw_text"):
        candidate = bundle_paths[key]
        if candidate.exists():
            return candidate
    return None


def detect_response_source_format(path: Path, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    suffix = path.suffix.casefold()
    if suffix == ".json":
        return "json"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    return "text"


def read_response_source(
    dispatch: dict[str, Any],
    source_reference: str | None,
    source_format: str,
    *,
    persist: bool,
) -> dict[str, Any]:
    bundle_paths = dispatch_bundle_paths(dispatch)
    source_path = (
        (ROOT / source_reference).resolve()
        if source_reference and not Path(source_reference).is_absolute()
        else Path(source_reference).resolve()
        if source_reference
        else auto_response_source_for_dispatch(dispatch)
    )
    if source_path is None:
        raise ValueError("No response source found. Write response.raw.json or pass --source.")
    if not source_path.exists():
        raise ValueError(f"Response source does not exist: {source_path}")

    detected_format = detect_response_source_format(source_path, source_format)
    warnings: list[str] = []
    payload: dict[str, Any] | None = None
    raw_text: str | None = None
    assistant_text: str | None = None

    if detected_format == "json":
        payload = load_json(source_path)
        if payload.get("status") == "pending" and set(payload) <= {"dispatch_id", "status", "notes"}:
            raise ValueError(
                f"Response source {display_path(source_path)} is still the placeholder, not a real provider response."
            )
        assistant_text, extract_warnings = extract_assistant_text_from_payload(payload, dispatch["transport"])
        warnings.extend(extract_warnings)
        metadata = extract_response_metadata(payload, dispatch["transport"])
        canonical_path = bundle_paths["response_raw_json"]
    else:
        raw_text = source_path.read_text(encoding="utf-8")
        assistant_text = raw_text
        metadata = {
            "response_id": None,
            "provider_model": None,
            "status": None,
            "usage": None,
            "finish_reasons": [],
        }
        canonical_path = bundle_paths["response_raw_text"]

    if assistant_text is None or not assistant_text.strip():
        raise ValueError("Could not extract assistant text from the provider response.")

    if persist and source_path != canonical_path:
        if detected_format == "json":
            write_json_if_changed(canonical_path, payload)
        else:
            text = raw_text or assistant_text
            write_text_if_changed(canonical_path, text if text.endswith("\n") else text + "\n")
    elif persist and source_path == canonical_path:
        if detected_format == "json":
            write_json_if_changed(canonical_path, payload)
        else:
            text = raw_text or assistant_text
            write_text_if_changed(canonical_path, text if text.endswith("\n") else text + "\n")

    return {
        "source_path": source_path,
        "canonical_path": canonical_path,
        "source_format": detected_format,
        "payload": payload,
        "metadata": metadata,
        "assistant_text": assistant_text.rstrip() + "\n",
        "warnings": unique_strings(warnings),
    }


def summarize_implementation(body: str) -> str:
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    if not lines:
        return ""
    return " ".join(lines[:2]).strip()


def parse_generation_response_text(assistant_text: str) -> dict[str, Any]:
    sections = split_markdown_sections(assistant_text)
    present_sections = [title for title in REQUIRED_GENERATION_SECTIONS if sections.get(title)]
    missing_sections = [title for title in REQUIRED_GENERATION_SECTIONS if not sections.get(title)]
    file_entries, file_warnings = extract_fenced_file_entries(sections.get("Files", ""))
    benchmark_report, report_warnings = extract_first_json_code_block(sections.get("Benchmark Report", ""))
    limitations = parse_markdown_list(sections.get("Known Limitations", ""))
    warnings = [
        *file_warnings,
        *report_warnings,
        *[f"Missing required response section: {title}" for title in missing_sections],
    ]
    return {
        "sections": sections,
        "present_sections": present_sections,
        "missing_sections": missing_sections,
        "file_entries": file_entries,
        "benchmark_report": benchmark_report,
        "limitations": limitations,
        "summary": summarize_implementation(sections.get("Implementation Summary", "")),
        "warnings": unique_strings([warning for warning in warnings if warning]),
    }


def merge_ingested_benchmark_report(
    base_report: dict[str, Any],
    parsed: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    merged = dict(base_report)
    warnings: list[str] = []
    parsed_report = parsed.get("benchmark_report") or {}
    authoritative_keys = {
        "report_version",
        "result_id",
        "benchmark_id",
        "generation_kind",
        "target_id",
        "target_language",
        "runtime",
        "lane",
    }

    for key, value in parsed_report.items():
        if key in authoritative_keys:
            if key in merged and merged[key] != value:
                warnings.append(f"Ignored benchmark report field `{key}` from model output; result metadata is authoritative.")
            continue
        merged[key] = value

    if parsed.get("summary"):
        merged["result_summary"] = parsed["summary"]

    if parsed.get("limitations"):
        merged["limitations"] = parsed["limitations"]

    if isinstance(merged.get("known_gaps"), str):
        merged["known_gaps"] = [merged["known_gaps"]]
    if isinstance(merged.get("limitations"), str):
        merged["limitations"] = [merged["limitations"]]

    if parsed.get("file_entries"):
        merged["generated_files"] = [entry["path"] for entry in parsed["file_entries"]]
        merged["known_gaps"] = [
            gap
            for gap in merged.get("known_gaps", [])
            if "Generated implementation files have not been attached yet." not in gap
        ]
    else:
        merged["known_gaps"] = unique_strings(
            [
                *merged.get("known_gaps", []),
                "Files section did not contain any parseable FILE entries.",
            ]
        )

    merged["limitations"] = [
        item
        for item in merged.get("limitations", [])
        if "Provider execution has not been captured in this record yet." not in item
        and "This is a scaffolded artifact, not a scored benchmark run." not in item
    ]
    merged["limitations"] = unique_strings(
        [
            *merged.get("limitations", []),
            "Benchmark scoring and visual evaluation are still pending.",
        ]
    )
    merged["delivery_sections_found"] = parsed.get("present_sections", [])
    return merged, unique_strings(warnings)


def write_ingested_generation_artifacts(
    dispatch: dict[str, Any],
    result: dict[str, Any],
    captured_response: dict[str, Any],
    parsed_response: dict[str, Any],
    captured_at: str,
) -> dict[str, Any]:
    bundle_paths = dispatch_bundle_paths(dispatch)
    result_paths = result_bundle_paths(result)
    generated_root = result_paths["root"] / "generated"

    assistant_text = captured_response["assistant_text"]
    write_text_if_changed(bundle_paths["response_text"], assistant_text)

    response_normalized = {
        "version": 1,
        "dispatch_id": dispatch["dispatch_id"],
        "result_id": result["result_id"],
        "captured_at": captured_at,
        "source_format": captured_response["source_format"],
        "source_path": relative_path(captured_response["canonical_path"]),
        "transport": dispatch["transport"],
        "provider_response": captured_response["metadata"],
        "present_sections": parsed_response["present_sections"],
        "missing_sections": parsed_response["missing_sections"],
        "warnings": unique_strings([*captured_response["warnings"], *parsed_response["warnings"]]),
        "extracted_files": [entry["path"] for entry in parsed_response["file_entries"]],
    }
    write_json_if_changed(bundle_paths["response_normalized"], response_normalized)

    assistant_response_path = generated_root / "response.md"
    write_text_if_changed(assistant_response_path, assistant_text)

    extracted_files: list[str] = []
    for entry in parsed_response["file_entries"]:
        relative_generated_path = str(entry["path"])
        destination = generated_root / relative_generated_path
        write_text_if_changed(destination, str(entry["content"]))
        extracted_files.append(relative_generated_path)

    generation_manifest = {
        "version": 1,
        "dispatch_id": dispatch["dispatch_id"],
        "result_id": result["result_id"],
        "captured_at": captured_at,
        "assistant_response_path": relative_path(assistant_response_path),
        "captured_response_path": relative_path(captured_response["canonical_path"]),
        "response_text_path": relative_path(bundle_paths["response_text"]),
        "response_normalized_path": relative_path(bundle_paths["response_normalized"]),
        "generated_files": extracted_files,
        "generated_file_count": len(extracted_files),
        "provider_response": captured_response["metadata"],
        "warnings": unique_strings([*captured_response["warnings"], *parsed_response["warnings"]]),
    }
    generation_manifest_path = generated_root / "generation_manifest.json"
    write_json_if_changed(generation_manifest_path, generation_manifest)
    return generation_manifest


def combined_user_message(packet: dict[str, Any]) -> str:
    scene_prompt = packet["messages"]["scene_prompt"].strip()
    user_prompt = packet["messages"]["user_prompt"].strip()
    return f"{scene_prompt}\n\n{user_prompt}".strip()

def prompt_bundle_markdown(
    packet: dict[str, Any],
    model: dict[str, Any],
    provider_profile: dict[str, Any],
    tool_profiles: list[dict[str, Any]],
    result: dict[str, Any],
) -> str:
    tool_list = ", ".join(profile["id"] for profile in tool_profiles) or "-"
    return f"""# Prompt Bundle: {result['result_id']}

## Dispatch Context
- Model: `{model['id']}`
- Provider Model: `{model['provider_model']}`
- Provider Profile: `{provider_profile['id']}`
- Tool Profiles: `{tool_list}`
- Result: `{result['result_id']}`
- Plan: `{result['plan_id']}`
- Packet: `{packet['packet_id']}`
- Target: `{packet['target']['id']}`
- Capabilities: `{", ".join(packet['selected_capabilities'])}`
- Locales: `{", ".join(packet['selected_locales'])}`

## System Prompt

```text
{packet['messages']['system_prompt'].rstrip()}
```

## Scene Prompt

```text
{packet['messages']['scene_prompt'].rstrip()}
```

## User Prompt

```text
{packet['messages']['user_prompt'].rstrip()}
```
"""


def profile_base_url(profile: dict[str, Any]) -> str:
    defaults = profile.get("defaults", {})
    if "base_url" in defaults:
        return defaults["base_url"]

    if profile["transport"] == "responses-api":
        return "https://api.openai.com/v1"
    if profile["transport"] == "messages-api":
        return "https://api.anthropic.com"
    if profile["transport"] == "claude-code-bridge":
        return "https://api.z.ai/api/anthropic"
    if profile["optional_env"]:
        return f"${profile['optional_env'][0]}"
    return ""


def preferred_dispatch_profile_id(
    model: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> str:
    if model["execution_channel"] == "workspace-agent":
        for profile_id in model.get("tool_profiles", []):
            profile = profiles.get(profile_id)
            if profile and profile["transport"] == "workspace-agent":
                return profile_id
    return model["provider_profile"]


def api_key_placeholder(profile: dict[str, Any]) -> str:
    if profile.get("required_env"):
        return f"${profile['required_env'][0]}"
    required_any = profile.get("required_any_env", [])
    if required_any:
        return " or ".join(f"${name}" for name in required_any[0])
    return ""


def build_request_payload(
    model: dict[str, Any],
    provider_profile: dict[str, Any],
    packet: dict[str, Any],
    request_settings: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    system_prompt = packet["messages"]["system_prompt"]
    user_content = combined_user_message(packet)
    request_settings = request_settings or {}
    metadata = {
        "benchmark_id": packet["benchmark_id"],
        "packet_id": packet["packet_id"],
        "target_id": packet["target"]["id"],
        "generation_kind": packet["generation_kind"],
        "model_id": model["id"],
    }
    if request_settings:
        metadata["request_settings"] = request_settings

    transport = provider_profile["transport"]
    if transport == "responses-api":
        payload = {
            "model": model["provider_model"],
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_content}]},
            ],
            "metadata": metadata,
        }
        reasoning_effort = request_settings.get("reasoning_effort")
        if reasoning_effort:
            payload["reasoning"] = {"effort": reasoning_effort}
        max_output_tokens = request_settings.get("max_output_tokens")
        if max_output_tokens is not None:
            payload["max_output_tokens"] = max_output_tokens
        return payload
    if transport == "openai-compatible":
        payload = {
            "model": model["provider_model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "metadata": metadata,
        }
        max_output_tokens = request_settings.get("max_output_tokens")
        if max_output_tokens is not None:
            payload["max_tokens"] = max_output_tokens
        return payload
    if transport == "messages-api":
        payload = {
            "model": model["provider_model"],
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_content},
            ],
            "metadata": metadata,
        }
        max_output_tokens = request_settings.get("max_output_tokens")
        if max_output_tokens is not None:
            payload["max_tokens"] = max_output_tokens
        return payload
    return None


def dispatch_bundle_paths(dispatch: dict[str, Any]) -> dict[str, Path]:
    root = ROOT / dispatch["request_bundle_root"]
    return {
        "root": root,
        "prompt_bundle": root / "prompt_bundle.md",
        "request_json": root / "request.json",
        "curl_script": root / "curl.sh",
        "invocation": root / "invocation.md",
        "manifest": root / "dispatch_manifest.json",
        "response_placeholder": root / "response.placeholder.json",
        "response_raw_json": root / "response.raw.json",
        "response_raw_text": root / "response.raw.txt",
        "response_normalized": root / "response.normalized.json",
        "response_text": root / "response.text.md",
    }


def response_contract_for_dispatch(dispatch: dict[str, Any]) -> dict[str, Any]:
    if dispatch.get("response_contract"):
        return dispatch["response_contract"]

    result = load_json(ROOT / dispatch["result_path"])
    request_bundle_root = dispatch["request_bundle_root"]
    return {
        "raw_response_path": f"{request_bundle_root}/response.raw.json",
        "fallback_text_response_path": f"{request_bundle_root}/response.raw.txt",
        "normalized_response_path": f"{request_bundle_root}/response.normalized.json",
        "extracted_text_path": f"{request_bundle_root}/response.text.md",
        "generated_manifest_path": f"{result['output_root']}/generated/generation_manifest.json",
        "ingest_command": (
            "python benchmark_execute.py ingest-response "
            f"--dispatch executions/dispatches/{dispatch['model_id']}/{dispatch['dispatch_id'].split('--', 1)[1]}.json"
        ),
    }


def dispatch_with_defaults(dispatch: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(dispatch)
    normalized["response_contract"] = response_contract_for_dispatch(normalized)
    normalized.setdefault("request_settings", {})
    return normalized


def invocation_kind_for_transport(transport: str) -> str:
    if transport in {"responses-api", "openai-compatible", "messages-api"}:
        return "http-api"
    return "manual-handoff"


def endpoint_for_transport(provider_profile: dict[str, Any]) -> str | None:
    base_url = profile_base_url(provider_profile).rstrip("/")
    transport = provider_profile["transport"]
    if not base_url:
        return None
    if transport == "responses-api":
        return f"{base_url}/responses"
    if transport == "openai-compatible":
        return f"{base_url}/chat/completions"
    if transport == "messages-api":
        return f"{base_url}/v1/messages"
    return None


def auth_header_lines(provider_profile: dict[str, Any]) -> list[str]:
    required_env = provider_profile.get("required_env", [])
    api_key_name = required_env[0] if required_env else None
    if provider_profile["transport"] == "messages-api":
        return [
            f"x-api-key: {read_env(api_key_name) if api_key_name else ''}",
            "anthropic-version: 2023-06-01",
            "content-type: application/json",
        ]
    return [
        f"Authorization: Bearer {read_env(api_key_name) if api_key_name else ''}",
        "content-type: application/json",
    ]


def request_execution_payload(
    dispatch: dict[str, Any],
    provider_profile: dict[str, Any],
    *,
    started_at: str,
    finished_at: str,
    duration_ms: int,
    http_status: int,
    request_bytes: int,
    response_bytes: int,
    response_content_type: str | None,
) -> dict[str, Any]:
    return {
        "runner": "benchmark_execute.py run-dispatch",
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "http_status": http_status,
        "endpoint": endpoint_for_transport(provider_profile),
        "request_payload_path": dispatch["request_contract"].get("request_payload_path"),
        "request_payload_hash": dispatch["request_contract"].get("request_payload_hash"),
        "prompt_bundle_path": dispatch["request_contract"].get("prompt_bundle_path"),
        "prompt_bundle_hash": dispatch["request_contract"].get("prompt_bundle_hash"),
        "request_bytes": request_bytes,
        "response_bytes": response_bytes,
        "response_content_type": response_content_type,
    }


def agent_capture_request_execution_payload(
    dispatch: dict[str, Any],
    *,
    started_at: str,
    finished_at: str,
    response_text: str,
    runner: str,
) -> dict[str, Any]:
    started = parse_timestamp(started_at)
    finished = parse_timestamp(finished_at)
    duration_ms = max(int((finished - started).total_seconds() * 1000), 0)
    prompt_bundle_path = dispatch["request_contract"].get("prompt_bundle_path")
    request_bytes = 0
    if prompt_bundle_path:
        prompt_bundle_abs = ROOT / prompt_bundle_path
        if prompt_bundle_abs.exists():
            request_bytes = prompt_bundle_abs.stat().st_size

    return {
        "runner": runner,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": duration_ms,
        "endpoint": dispatch["transport"],
        "request_payload_path": dispatch["request_contract"].get("request_payload_path"),
        "request_payload_hash": dispatch["request_contract"].get("request_payload_hash"),
        "prompt_bundle_path": prompt_bundle_path,
        "prompt_bundle_hash": dispatch["request_contract"].get("prompt_bundle_hash"),
        "request_bytes": request_bytes,
        "response_bytes": len(response_text.encode("utf-8")),
        "response_content_type": "text/markdown",
        "agent_transport": dispatch["transport"],
        "workspace_reasoning_effort": dispatch.get("request_settings", {}).get("reasoning_effort"),
        "token_usage_available": False,
        "cost_available": False,
        "notes": [
            "Agent-captured execution does not expose provider token usage or billing telemetry in this environment.",
        ],
    }


def curl_script_for_dispatch(dispatch: dict[str, Any], provider_profile: dict[str, Any]) -> str | None:
    endpoint = endpoint_for_transport(provider_profile)
    if not endpoint:
        return None

    api_key = api_key_placeholder(provider_profile)
    request_rel = f"{dispatch['request_bundle_root']}/request.json"
    response_rel = f"{dispatch['request_bundle_root']}/response.raw.json"
    required_env = provider_profile.get("required_env", [])
    if provider_profile["transport"] == "messages-api":
        header_lines = [
            f'-H "x-api-key: {api_key}"',
            '-H "anthropic-version: 2023-06-01"',
            '-H "content-type: application/json"',
        ]
    else:
        header_lines = [
            f'-H "Authorization: Bearer {api_key}"',
            '-H "content-type: application/json"',
        ]

    headers = " \\\n  ".join(header_lines)
    env_prelude = """script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../../.." && pwd)"

if [ -f "$repo_root/.env.local" ]; then
  set -a
  . "$repo_root/.env.local"
  set +a
elif [ -f "$repo_root/.env" ]; then
  set -a
  . "$repo_root/.env"
  set +a
fi
"""
    env_checks = "\n".join(
        [
            f'if [ -z "${{{name}:-}}" ]; then echo "Missing {name}. Set it in the environment or $repo_root/.env.local" >&2; exit 1; fi'
            for name in required_env
        ]
    )
    return f"""#!/usr/bin/env bash
set -euo pipefail

{env_prelude}
{env_checks}

request_path="$repo_root/{request_rel}"
response_path="$repo_root/{response_rel}"

curl -sS '{endpoint}' \\
  {headers} \\
  --data "@$request_path" \\
  --output "$response_path"

printf 'Wrote raw response to %s\\n' "$response_path"
"""


def invocation_markdown(
    dispatch: dict[str, Any],
    model: dict[str, Any],
    provider_profile: dict[str, Any],
    tool_profiles: list[dict[str, Any]],
) -> str:
    tool_list = "\n".join(f"- `{profile['id']}`: {profile['notes']}" for profile in tool_profiles) or "- none"
    endpoint = endpoint_for_transport(provider_profile)
    api_key = api_key_placeholder(provider_profile) or "provider-specific auth"
    kind = invocation_kind_for_transport(provider_profile["transport"])

    if kind == "http-api":
        command_hint = f"`bash {dispatch['request_bundle_root']}/curl.sh`"
        endpoint_line = f"- Endpoint: `{endpoint}`"
        request_payload_line = f"- Request payload: `{dispatch['request_bundle_root']}/request.json`"
        response_line = f"- Raw response target: `{dispatch['response_contract']['raw_response_path']}`"
    else:
        command_hint = "Use the prompt bundle plus provider/tool config in your preferred client."
        endpoint_line = "- Endpoint: not portable across clients; use the configured tool or workspace bridge."
        request_payload_line = "- Request payload: not emitted for this transport; use the prompt bundle plus invocation notes."
        response_line = "- Raw response target: place the provider output in a text or JSON file, then pass it to `ingest-response --source`."

    return f"""# Invocation: {dispatch['dispatch_id']}

## Transport
- Kind: `{kind}`
- Provider Profile: `{provider_profile['id']}`
- Transport: `{provider_profile['transport']}`
- Model: `{model['provider_model']}`
{endpoint_line}
- Auth: `{api_key}`

## Tool Profiles
{tool_list}

## Recommended Execution
- Prompt bundle: `{dispatch['request_bundle_root']}/prompt_bundle.md`
{request_payload_line}
{response_line}
- Suggested command: {command_hint}
- After generation, run `python benchmark_execute.py ingest-response --dispatch {relative_path(dispatch_path_for(dispatch['model_id'], dispatch['dispatch_id'], 'json'))}`.
"""


def dispatch_manifest_payload(dispatch: dict[str, Any]) -> dict[str, Any]:
    dispatch = dispatch_with_defaults(dispatch)
    payload = {
        "version": 1,
        "dispatch_id": dispatch["dispatch_id"],
        "model_id": dispatch["model_id"],
        "provider_profile_id": dispatch["provider_profile_id"],
        "tool_profile_ids": dispatch["tool_profile_ids"],
        "result_id": dispatch["result_id"],
        "request_bundle_root": dispatch["request_bundle_root"],
        "status": dispatch["status"],
        "request_settings": dispatch.get("request_settings", {}),
        "request_contract": dispatch["request_contract"],
        "response_contract": dispatch["response_contract"],
    }
    if dispatch.get("request_execution"):
        payload["request_execution"] = dispatch["request_execution"]
    return payload


def infer_request_artifact_type(bundle_root: Path, path: Path) -> str:
    rel = path.relative_to(bundle_root).as_posix()
    mapping = {
        "prompt_bundle.md": "prompt-bundle",
        "request.json": "request-payload",
        "curl.sh": "curl-script",
        "invocation.md": "invocation-doc",
        "dispatch_manifest.json": "dispatch-manifest",
        "response.placeholder.json": "response-placeholder",
        "response.raw.json": "response-raw-json",
        "response.raw.txt": "response-raw-text",
        "response.normalized.json": "response-normalized",
        "response.text.md": "response-text",
    }
    return mapping.get(rel, "request-bundle-file")


def dispatch_artifact_inventory(dispatch: dict[str, Any]) -> list[dict[str, Any]]:
    artifacts = [
        {
            "path": relative_path(dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "json")),
            "type": "dispatch-record",
        },
        {
            "path": relative_path(dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "md")),
            "type": "dispatch-record-doc",
        },
    ]
    bundle_root = ROOT / dispatch["request_bundle_root"]
    if bundle_root.exists():
        for path in sorted(item for item in bundle_root.rglob("*") if item.is_file()):
            artifacts.append(
                {
                    "path": relative_path(path),
                    "type": infer_request_artifact_type(bundle_root, path),
                }
            )
    return artifacts


def scaffold_result_bundle(result: dict[str, Any]) -> None:
    paths = result_bundle_paths(result)
    bundle_manifest = build_result_bundle_manifest(result)

    write_text_if_changed(
        paths["readme"],
        f"""# Output Bundle: {result['result_id']}

This directory is the single-source output bundle for `{result['result_id']}`.

## References
- Model: `{result['model_id']}`
- Plan: `{result['plan_id']}`
- Packet: `{result['packet_id']}`
- Result Record: `executions/results/{result['model_id']}/{result['result_id'].split('--', 1)[1]}.json`
- Status: `{result['status']}`

## Conventions
- Put generated source files under `generated/`.
- Put screenshots, video captures, or visual evidence under `captures/`.
- Keep benchmark report updates synchronized in `benchmark_report.json` and the result record.
- Prefer using `benchmark_execute.py ingest-response` so dispatch, response, and output artifacts stay aligned.
- Promote this bundle into a scored run only after review.
""",
    )
    write_text_if_changed(
        paths["manifest"],
        json.dumps(bundle_manifest, indent=2, ensure_ascii=False) + "\n",
    )
    write_text_if_changed(
        paths["report"],
        json.dumps(result["benchmark_report"], indent=2, ensure_ascii=False) + "\n",
    )
    write_text_if_changed(
        paths["generated_readme"],
        """# Generated Files

Place provider-produced source files, code responses, or stitched workspace outputs in this directory.
""",
    )
    write_text_if_changed(
        paths["captures_readme"],
        """# Captures

Place screenshots, screen recordings, benchmark stills, or other visual evidence in this directory.
""",
    )


def write_dispatch_bundle(dispatch: dict[str, Any]) -> None:
    dispatch = dispatch_with_defaults(dispatch)
    bundle_paths = dispatch_bundle_paths(dispatch)
    provider_registry = load_provider_registry()
    model_registry = load_model_registry()
    provider_profiles = provider_map(provider_registry)
    models = index_by_id(model_registry["models"])
    result = load_json(ROOT / dispatch["result_path"])
    packet = load_packet(ROOT / dispatch["packet_path"])

    provider_profile = provider_profiles[dispatch["provider_profile_id"]]
    tool_profiles = [provider_profiles[profile_id] for profile_id in dispatch["tool_profile_ids"]]
    model = models[dispatch["model_id"]]

    prompt_bundle_text = prompt_bundle_markdown(packet, model, provider_profile, tool_profiles, result)
    request_payload = build_request_payload(model, provider_profile, packet, dispatch.get("request_settings"))
    request_payload_text = (
        json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n"
        if request_payload is not None
        else ""
    )
    curl_script = curl_script_for_dispatch(dispatch, provider_profile)
    invocation_text = invocation_markdown(dispatch, model, provider_profile, tool_profiles)
    manifest_text = json.dumps(dispatch_manifest_payload(dispatch), indent=2, ensure_ascii=False) + "\n"
    response_placeholder = json.dumps(
        {
            "dispatch_id": dispatch["dispatch_id"],
            "status": "pending",
            "notes": (
                "Write raw provider output to response.raw.json or provide --source to ingest-response. "
                "This placeholder is not the canonical raw response artifact."
            ),
        },
        indent=2,
        ensure_ascii=False,
    ) + "\n"

    write_text_if_changed(bundle_paths["prompt_bundle"], prompt_bundle_text)
    if request_payload is not None:
        write_text_if_changed(bundle_paths["request_json"], request_payload_text)
    elif bundle_paths["request_json"].exists():
        bundle_paths["request_json"].unlink()
    if curl_script is not None:
        write_text_if_changed(bundle_paths["curl_script"], curl_script)
    elif bundle_paths["curl_script"].exists():
        bundle_paths["curl_script"].unlink()
    write_text_if_changed(bundle_paths["invocation"], invocation_text)
    write_text_if_changed(bundle_paths["manifest"], manifest_text)
    write_text_if_changed(bundle_paths["response_placeholder"], response_placeholder)


def write_dispatch_files(dispatch: dict[str, Any]) -> None:
    dispatch = dispatch_with_defaults(dispatch)
    json_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "json")
    md_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "md")
    write_dispatch_bundle(dispatch)
    dispatch["request_artifacts"] = dispatch_artifact_inventory(dispatch)
    write_text_if_changed(json_path, json.dumps(dispatch, indent=2, ensure_ascii=False) + "\n")
    write_text_if_changed(md_path, build_markdown_dispatch(dispatch))


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    execution_manifest = load_execution_manifest()
    model_registry = load_model_registry()

    models = index_by_id(model_registry["models"])
    plan_path = (ROOT / args.plan).resolve() if not Path(args.plan).is_absolute() else Path(args.plan)
    plan = load_json(plan_path)
    model_id = args.model or plan["model_id"]

    if model_id not in track_ids(benchmark_manifest):
        raise ValueError(f"Unknown benchmark model: {model_id}")
    if model_id not in models:
        raise ValueError(f"Model missing from registry: {model_id}")
    if plan["model_id"] != model_id:
        raise ValueError(
            f"Plan model_id {plan['model_id']} does not match requested model {model_id}"
        )
    if args.status not in execution_manifest["result_status_values"]:
        raise ValueError(f"Unsupported execution result status: {args.status}")

    packet_path = ROOT / plan["packet_path"]
    packet = load_packet(packet_path)
    if packet["model_id"] != model_id:
        raise ValueError(
            f"Packet model_id {packet['model_id']} does not match requested model {model_id}"
        )

    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    timestamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    result_slug = args.slug or plan["plan_id"].split("--", 2)[2]
    result_id = f"{model_id}--{timestamp}--{result_slug}"
    result_rel = relative_path(result_path_for(model_id, result_id, "json"))
    result_md_rel = relative_path(result_path_for(model_id, result_id, "md"))
    output_root_rel = relative_path(output_root_for(model_id, result_id))
    benchmark_report = build_result_benchmark_report(benchmark_manifest, packet, result_id)
    openspec_refs = unique_strings(
        [
            *plan["openspec_refs"],
            "openspec/specs/execution-results/spec.md",
            f"openspec/changes/{args.openspec_change}",
        ]
    )

    notes = [
        "Execution results are the durable layer between plans and scored benchmark runs.",
        "This artifact is scaffold-first so provider-backed generations can be attached later without losing provenance.",
        *args.note,
    ]

    result = {
        "result_id": result_id,
        "created_at": recorded_at.isoformat().replace("+00:00", "Z"),
        "model_id": model_id,
        "plan_id": plan["plan_id"],
        "plan_path": relative_path(plan_path),
        "packet_id": plan["packet_id"],
        "packet_path": plan["packet_path"],
        "execution_mode": plan["execution_mode"],
        "status": args.status,
        "summary": args.summary or f"Scaffolded output bundle for execution plan {plan['plan_id']}.",
        "generation_target": plan["generation_target"],
        "output_root": output_root_rel,
        "openspec_refs": openspec_refs,
        "review_state": {
            "score_ready": False,
            "linked_run_id": None,
            "linked_run_path": None,
        },
        "artifacts": [
            {"path": result_rel, "type": "execution-result"},
            {"path": result_md_rel, "type": "execution-result-doc"},
            {"path": f"{output_root_rel}/README.md", "type": "output-bundle-doc"},
            {"path": f"{output_root_rel}/bundle_manifest.json", "type": "output-bundle-manifest"},
            {"path": f"{output_root_rel}/benchmark_report.json", "type": "benchmark-report"},
            {"path": f"{output_root_rel}/generated/README.md", "type": "generated-output-slot"},
            {"path": f"{output_root_rel}/captures/README.md", "type": "capture-output-slot"},
        ],
        "benchmark_report": benchmark_report,
        "notes": notes,
    }
    return result


def build_dispatch(args: argparse.Namespace) -> dict[str, Any]:
    execution_manifest = load_execution_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()

    models = index_by_id(model_registry["models"])
    provider_profiles = provider_map(provider_registry)
    result_path, result, benchmark_manifest, _execution_manifest, _model_registry, _provider_registry = load_result_with_context(args.result)
    model = models[result["model_id"]]

    provider_profile_id = args.profile or model["provider_profile"]
    if provider_profile_id not in provider_profiles:
        raise ValueError(f"Unknown provider profile: {provider_profile_id}")
    allowed_profiles = {model["provider_profile"], *model.get("tool_profiles", [])}
    if provider_profile_id not in allowed_profiles:
        raise ValueError(
            f"Profile {provider_profile_id} is not configured for model {result['model_id']}. "
            f"Allowed profiles: {sorted(allowed_profiles)}"
        )
    tool_profile_ids = args.tool_profile or model.get("tool_profiles", [])
    for profile_id in tool_profile_ids:
        if profile_id not in provider_profiles:
            raise ValueError(f"Unknown tool profile: {profile_id}")
    if args.status not in execution_manifest["dispatch_status_values"]:
        raise ValueError(f"Unsupported dispatch status: {args.status}")

    provider_profile = provider_profiles[provider_profile_id]
    tool_profiles = [provider_profiles[profile_id] for profile_id in tool_profile_ids]
    request_settings = request_settings_from_args(args)

    packet = load_packet(ROOT / result["packet_path"])
    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    timestamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    dispatch_slug = args.slug or result["result_id"].split("--", 2)[2]
    dispatch_id = f"{result['model_id']}--{timestamp}--{dispatch_slug}"
    request_bundle_root = relative_path(request_bundle_root_for(result["model_id"], dispatch_id))

    prompt_bundle_text = prompt_bundle_markdown(packet, model, provider_profile, tool_profiles, result)
    request_payload = build_request_payload(model, provider_profile, packet, request_settings)
    request_payload_text = (
        json.dumps(request_payload, indent=2, ensure_ascii=False) + "\n"
        if request_payload is not None
        else None
    )
    invocation = {
        "kind": invocation_kind_for_transport(provider_profile["transport"]),
        "endpoint": endpoint_for_transport(provider_profile),
        "api_key_hint": api_key_placeholder(provider_profile),
        "suggested_command": (
            f"bash {request_bundle_root}/curl.sh"
            if request_payload is not None
            else f"open {request_bundle_root}/invocation.md"
        ),
    }

    request_contract = {
        "prompt_bundle_path": f"{request_bundle_root}/prompt_bundle.md",
        "prompt_bundle_hash": content_hash(prompt_bundle_text),
        "request_payload_path": f"{request_bundle_root}/request.json" if request_payload_text else None,
        "request_payload_hash": content_hash(request_payload) if request_payload is not None else None,
        "response_placeholder_path": f"{request_bundle_root}/response.placeholder.json",
    }
    response_contract = {
        "raw_response_path": f"{request_bundle_root}/response.raw.json",
        "fallback_text_response_path": f"{request_bundle_root}/response.raw.txt",
        "normalized_response_path": f"{request_bundle_root}/response.normalized.json",
        "extracted_text_path": f"{request_bundle_root}/response.text.md",
        "generated_manifest_path": f"{result['output_root']}/generated/generation_manifest.json",
        "ingest_command": (
            "python benchmark_execute.py ingest-response "
            f"--dispatch executions/dispatches/{result['model_id']}/{dispatch_id.split('--', 1)[1]}.json"
        ),
    }

    dispatch = {
        "dispatch_id": dispatch_id,
        "created_at": recorded_at.isoformat().replace("+00:00", "Z"),
        "model_id": result["model_id"],
        "result_id": result["result_id"],
        "result_path": relative_path(result_path),
        "plan_id": result["plan_id"],
        "plan_path": result["plan_path"],
        "packet_id": result["packet_id"],
        "packet_path": result["packet_path"],
        "provider_profile_id": provider_profile_id,
        "tool_profile_ids": tool_profile_ids,
        "execution_channel": model["execution_channel"],
        "transport": provider_profile["transport"],
        "status": args.status,
        "request_settings": request_settings,
        "request_bundle_root": request_bundle_root,
        "request_contract": request_contract,
        "response_contract": response_contract,
        "auth_status": {
            "primary": auth_status_for_profile(provider_profile),
            "tools": [auth_status_for_profile(profile) for profile in tool_profiles],
        },
        "invocation": invocation,
        "request_artifacts": [],
    }
    dispatch["request_artifacts"] = dispatch_artifact_inventory(dispatch)
    return dispatch


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    execution_manifest = load_execution_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()

    model_map = index_by_id(model_registry["models"])
    packet_path = (ROOT / args.packet).resolve() if not Path(args.packet).is_absolute() else Path(args.packet)
    packet = load_packet(packet_path)
    model_id = args.model or packet["model_id"]

    if model_id not in track_ids(benchmark_manifest):
        raise ValueError(f"Unknown benchmark model: {model_id}")
    if model_id not in model_map:
        raise ValueError(f"Model missing from registry: {model_id}")
    if packet["model_id"] != model_id:
        raise ValueError(
            f"Packet model_id {packet['model_id']} does not match requested model {model_id}"
        )
    if args.mode not in execution_manifest["execution_modes"]:
        raise ValueError(f"Unsupported execution mode: {args.mode}")

    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    timestamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    plan_slug = args.slug or packet["packet_id"].split("--", 2)[2]
    plan_id = f"{model_id}--{timestamp}--{plan_slug}"

    model = model_map[model_id]
    packet_rel = relative_path(packet_path)
    auth_status = auth_status_for_model(model, provider_registry)
    openspec_refs = [
        "openspec/specs/model-registry/spec.md",
        "openspec/specs/prompt-packet-lifecycle/spec.md",
        "openspec/specs/execution-orchestration/spec.md",
        "openspec/specs/provider-auth/spec.md",
        f"openspec/changes/{args.openspec_change}",
    ]

    plan = {
        "plan_id": plan_id,
        "created_at": recorded_at.isoformat().replace("+00:00", "Z"),
        "model_id": model_id,
        "packet_id": packet["packet_id"],
        "packet_path": packet_rel,
        "planner_engine": args.planner_engine,
        "execution_mode": args.mode,
        "status": args.status,
        "model_profile": model,
        "auth_status": auth_status,
        "generation_target": packet["target"],
        "openspec_refs": openspec_refs,
        "dspy_status": dspy_status(),
        "dspy_contract": {
            "signature": "BenchmarkExecutionPlanSignature",
            "module": "BenchmarkExecutionPlanner",
            "available": dspy is not None,
        },
        "steps": build_steps(model, args.mode, auth_status),
        "artifacts": [
            {"path": packet_rel, "type": "prompt-packet"},
            {"path": f"executions/plans/{model_id}/{plan_id.split('--', 1)[1]}.json", "type": "execution-plan"},
            {"path": f"executions/plans/{model_id}/{plan_id.split('--', 1)[1]}.md", "type": "execution-plan-doc"},
        ],
        "notes": [
            "This plan is planning-first and can remain dry until prompt and evaluation architecture stabilizes.",
            "DSPy availability is recorded even if no model call is executed yet.",
        ],
    }
    return plan


def validate_plan(
    path: Path,
    execution_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    model_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    plan = load_json(path)
    required_keys = set(execution_manifest["plan_required_fields"]) | {
        "packet_path",
        "model_profile",
        "generation_target",
        "openspec_refs",
        "auth_status",
        "dspy_status",
        "dspy_contract",
        "notes",
    }
    missing = sorted(required_keys - set(plan))
    if missing:
        errors.append(f"{relative_path(path)}: missing keys {', '.join(missing)}")
        return errors

    if plan["model_id"] not in track_ids(benchmark_manifest):
        errors.append(f"{relative_path(path)}: unknown model id {plan['model_id']}")
    if plan["model_id"] not in index_by_id(model_registry["models"]):
        errors.append(f"{relative_path(path)}: missing model registry entry {plan['model_id']}")
    if plan["execution_mode"] not in execution_manifest["execution_modes"]:
        errors.append(f"{relative_path(path)}: unsupported execution mode {plan['execution_mode']}")

    packet_path = ROOT / plan["packet_path"]
    if not packet_path.exists():
        errors.append(f"{relative_path(path)}: missing packet path {plan['packet_path']}")

    md_pair = path.with_suffix(".md")
    if not md_pair.exists():
        errors.append(f"{relative_path(path)}: missing markdown pair {relative_path(md_pair)}")

    return errors


def validate_result(
    path: Path,
    execution_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    model_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    result = load_json(path)
    required_keys = set(execution_manifest["result_required_fields"]) | {
        "plan_path",
        "packet_path",
        "generation_target",
        "output_root",
        "openspec_refs",
        "review_state",
        "notes",
    }
    missing = sorted(required_keys - set(result))
    if missing:
        errors.append(f"{relative_path(path)}: missing keys {', '.join(missing)}")
        return errors

    if result["model_id"] not in track_ids(benchmark_manifest):
        errors.append(f"{relative_path(path)}: unknown model id {result['model_id']}")
    if result["model_id"] not in index_by_id(model_registry["models"]):
        errors.append(f"{relative_path(path)}: missing model registry entry {result['model_id']}")
    if result["execution_mode"] not in execution_manifest["execution_modes"]:
        errors.append(f"{relative_path(path)}: unsupported execution mode {result['execution_mode']}")
    if result["status"] not in execution_manifest["result_status_values"]:
        errors.append(f"{relative_path(path)}: unsupported result status {result['status']}")

    plan_path = ROOT / result["plan_path"]
    if not plan_path.exists():
        errors.append(f"{relative_path(path)}: missing plan path {result['plan_path']}")
    else:
        plan = load_json(plan_path)
        if plan["plan_id"] != result["plan_id"]:
            errors.append(f"{relative_path(path)}: plan id mismatch with {result['plan_path']}")
        if plan["packet_id"] != result["packet_id"]:
            errors.append(f"{relative_path(path)}: packet id mismatch with {result['plan_path']}")

    packet_path = ROOT / result["packet_path"]
    if not packet_path.exists():
        errors.append(f"{relative_path(path)}: missing packet path {result['packet_path']}")
    else:
        packet = load_json(packet_path)
        if packet["packet_id"] != result["packet_id"]:
            errors.append(f"{relative_path(path)}: packet id mismatch with {result['packet_path']}")

    md_pair = path.with_suffix(".md")
    if not md_pair.exists():
        errors.append(f"{relative_path(path)}: missing markdown pair {relative_path(md_pair)}")

    output_root = ROOT / result["output_root"]
    if not output_root.exists():
        errors.append(f"{relative_path(path)}: missing output root {result['output_root']}")
    else:
        bundle_paths = result_bundle_paths(result)
        for expected in ("readme", "manifest", "report", "generated_readme", "captures_readme"):
            bundle_path = bundle_paths[expected]
            if not bundle_path.exists():
                errors.append(
                    f"{relative_path(path)}: missing scaffolded bundle file {relative_path(bundle_path)}"
                )

        manifest_path = bundle_paths["manifest"]
        if manifest_path.exists():
            bundle_manifest = load_json(manifest_path)
            if bundle_manifest.get("result_id") != result["result_id"]:
                errors.append(f"{relative_path(path)}: bundle manifest result_id mismatch")
            if bundle_manifest.get("output_root") != result["output_root"]:
                errors.append(f"{relative_path(path)}: bundle manifest output_root mismatch")

        report_path = bundle_paths["report"]
        if report_path.exists():
            benchmark_report = load_json(report_path)
            if benchmark_report != result["benchmark_report"]:
                errors.append(f"{relative_path(path)}: benchmark_report.json is out of sync with result record")

    linked_run_path = result.get("review_state", {}).get("linked_run_path")
    if linked_run_path and not (ROOT / linked_run_path).exists():
        errors.append(f"{relative_path(path)}: linked run path does not exist: {linked_run_path}")

    report_required = set(execution_manifest.get("benchmark_report_required_fields", []))
    report_missing = sorted(report_required - set(result["benchmark_report"]))
    if report_missing:
        errors.append(
            f"{relative_path(path)}: benchmark_report missing keys {', '.join(report_missing)}"
        )
    errors.extend(validate_result_consistency(result, benchmark_manifest, relative_path(path)))

    if not isinstance(result["artifacts"], list):
        errors.append(f"{relative_path(path)}: artifacts must be a list")
    else:
        for artifact in result["artifacts"]:
            artifact_path = artifact.get("path") if isinstance(artifact, dict) else None
            if not artifact_path:
                errors.append(f"{relative_path(path)}: each artifact must include a path")
                continue
            if not (ROOT / artifact_path).exists():
                errors.append(f"{relative_path(path)}: artifact path does not exist: {artifact_path}")

    return errors


def validate_result_consistency(
    result: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    result_label: str,
) -> list[str]:
    errors: list[str] = []
    report = result.get("benchmark_report", {})
    target = result.get("generation_target", {})

    if report.get("result_id") != result.get("result_id"):
        errors.append(f"{result_label}: benchmark_report.result_id must match result_id")
    if report.get("benchmark_id") != benchmark_manifest["benchmark_id"]:
        errors.append(f"{result_label}: benchmark_report.benchmark_id must match benchmark manifest")
    if target:
        if report.get("target_id") != target.get("id"):
            errors.append(f"{result_label}: benchmark_report.target_id must match generation_target.id")
        if report.get("target_language") != target.get("language"):
            errors.append(f"{result_label}: benchmark_report.target_language must match generation_target.language")
        if report.get("runtime") != target.get("runtime"):
            errors.append(f"{result_label}: benchmark_report.runtime must match generation_target.runtime")

    return errors


def validate_dispatch_consistency(
    dispatch: dict[str, Any],
    model_registry: dict[str, Any],
    provider_registry: dict[str, Any],
    dispatch_label: str,
) -> list[str]:
    errors: list[str] = []
    models = index_by_id(model_registry["models"])
    profiles = provider_map(provider_registry)
    model = models.get(dispatch["model_id"])
    profile = profiles.get(dispatch["provider_profile_id"])

    if model and dispatch["execution_channel"] != model["execution_channel"]:
        errors.append(f"{dispatch_label}: execution_channel must match model registry")
    if profile and dispatch["transport"] != profile["transport"]:
        errors.append(f"{dispatch_label}: transport must match provider profile")
    return errors


def validate_dispatch(
    path: Path,
    execution_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    model_registry: dict[str, Any],
    provider_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    dispatch = dispatch_with_defaults(load_json(path))
    required_keys = set(execution_manifest["dispatch_required_fields"]) | {"auth_status", "response_contract"}
    missing = sorted(required_keys - set(dispatch))
    if missing:
        errors.append(f"{relative_path(path)}: missing keys {', '.join(missing)}")
        return errors

    if dispatch["model_id"] not in track_ids(benchmark_manifest):
        errors.append(f"{relative_path(path)}: unknown model id {dispatch['model_id']}")
    models = index_by_id(model_registry["models"])
    if dispatch["model_id"] not in models:
        errors.append(f"{relative_path(path)}: missing model registry entry {dispatch['model_id']}")

    profiles = provider_map(provider_registry)
    if dispatch["provider_profile_id"] not in profiles:
        errors.append(f"{relative_path(path)}: unknown provider profile {dispatch['provider_profile_id']}")
    for profile_id in dispatch["tool_profile_ids"]:
        if profile_id not in profiles:
            errors.append(f"{relative_path(path)}: unknown tool profile {profile_id}")

    if dispatch["status"] not in execution_manifest["dispatch_status_values"]:
        errors.append(f"{relative_path(path)}: unsupported dispatch status {dispatch['status']}")

    for key in ("result_path", "plan_path", "packet_path"):
        ref_path = ROOT / dispatch[key]
        if not ref_path.exists():
            errors.append(f"{relative_path(path)}: missing referenced path {dispatch[key]}")

    md_pair = path.with_suffix(".md")
    if not md_pair.exists():
        errors.append(f"{relative_path(path)}: missing markdown pair {relative_path(md_pair)}")

    bundle_root = ROOT / dispatch["request_bundle_root"]
    if not bundle_root.exists():
        errors.append(f"{relative_path(path)}: missing request bundle root {dispatch['request_bundle_root']}")
    else:
        bundle_paths = dispatch_bundle_paths(dispatch)
        required_bundle_files = ("prompt_bundle", "invocation", "manifest", "response_placeholder")
        for key in required_bundle_files:
            if not bundle_paths[key].exists():
                errors.append(
                    f"{relative_path(path)}: missing dispatch bundle file {relative_path(bundle_paths[key])}"
                )

        contract = dispatch["request_contract"]
        prompt_bundle_path = ROOT / contract["prompt_bundle_path"]
        if not prompt_bundle_path.exists():
            errors.append(f"{relative_path(path)}: missing prompt bundle {contract['prompt_bundle_path']}")
        else:
            prompt_text = prompt_bundle_path.read_text(encoding="utf-8")
            if content_hash(prompt_text) != contract["prompt_bundle_hash"]:
                errors.append(f"{relative_path(path)}: prompt bundle hash mismatch")

        request_payload_path = contract.get("request_payload_path")
        request_payload_hash = contract.get("request_payload_hash")
        if request_payload_path:
            request_path = ROOT / request_payload_path
            if not request_path.exists():
                errors.append(f"{relative_path(path)}: missing request payload {request_payload_path}")
            else:
                request_payload = load_json(request_path)
                if content_hash(request_payload) != request_payload_hash:
                    errors.append(f"{relative_path(path)}: request payload hash mismatch")
        elif bundle_paths["request_json"].exists():
            errors.append(f"{relative_path(path)}: request.json exists but request_contract omits it")

        response_contract = dispatch["response_contract"]
        if not response_contract.get("ingest_command"):
            errors.append(f"{relative_path(path)}: response_contract missing ingest_command")
        for contract_key in (
            "raw_response_path",
            "fallback_text_response_path",
            "normalized_response_path",
            "extracted_text_path",
            "generated_manifest_path",
        ):
            response_path = response_contract.get(contract_key)
            if response_path and response_path.startswith(dispatch["request_bundle_root"]):
                expected = ROOT / response_path
                parent = expected.parent
                if not parent.exists():
                    errors.append(
                        f"{relative_path(path)}: parent directory missing for response contract path {response_path}"
                    )

        response_capture = dispatch.get("response_capture")
        if dispatch["status"] == "captured" and not response_capture:
            errors.append(f"{relative_path(path)}: captured dispatch must include response_capture")
        if response_capture:
            for contract_key in (
                "canonical_response_path",
                "normalized_response_path",
                "assistant_text_path",
                "generated_manifest_path",
            ):
                response_path = response_capture.get(contract_key)
                if response_path and not (ROOT / response_path).exists():
                    errors.append(f"{relative_path(path)}: missing response capture artifact {response_path}")

    errors.extend(
        validate_dispatch_consistency(
            dispatch,
            model_registry,
            provider_registry,
            relative_path(path),
        )
    )

    if not isinstance(dispatch["request_artifacts"], list):
        errors.append(f"{relative_path(path)}: request_artifacts must be a list")
    else:
        for artifact in dispatch["request_artifacts"]:
            artifact_path = artifact.get("path") if isinstance(artifact, dict) else None
            if not artifact_path:
                errors.append(f"{relative_path(path)}: each request artifact must include a path")
                continue
            if not (ROOT / artifact_path).exists():
                errors.append(f"{relative_path(path)}: request artifact path does not exist: {artifact_path}")

    return errors


def review_state_for_status(
    review_state: dict[str, Any],
    *,
    status: str,
    recorded_at: str,
    score_ready: bool | None = None,
) -> dict[str, Any]:
    next_state = dict(review_state)
    next_state.setdefault("score_ready", False)
    next_state.setdefault("linked_run_id", None)
    next_state.setdefault("linked_run_path", None)

    if score_ready is not None:
        next_state["score_ready"] = score_ready

    if status == "captured":
        next_state["captured_at"] = recorded_at
    elif status == "reviewed":
        next_state["reviewed_at"] = recorded_at
    elif status == "linked":
        next_state["linked_at"] = recorded_at

    return next_state


def load_result_with_context(
    result_reference: str,
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    benchmark_manifest = load_benchmark_manifest()
    execution_manifest = load_execution_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    result_path = (ROOT / result_reference).resolve() if not Path(result_reference).is_absolute() else Path(result_reference)
    result = load_json(result_path)
    return result_path, result, benchmark_manifest, execution_manifest, model_registry, provider_registry


def load_dispatch_with_context(
    dispatch_reference: str,
) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    benchmark_manifest = load_benchmark_manifest()
    execution_manifest = load_execution_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    dispatch_path = (
        (ROOT / dispatch_reference).resolve()
        if not Path(dispatch_reference).is_absolute()
        else Path(dispatch_reference)
    )
    dispatch = dispatch_with_defaults(load_json(dispatch_path))
    return dispatch_path, dispatch, benchmark_manifest, execution_manifest, model_registry, provider_registry


def persist_provider_response(
    dispatch: dict[str, Any],
    body: bytes,
    content_type: str | None,
) -> Path:
    bundle_paths = dispatch_bundle_paths(dispatch)
    lowered_content_type = (content_type or "").casefold()
    if "json" in lowered_content_type:
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            text = body.decode("utf-8", errors="replace")
            write_text_if_changed(bundle_paths["response_raw_text"], text if text.endswith("\n") else text + "\n")
            return bundle_paths["response_raw_text"]
        write_json_if_changed(bundle_paths["response_raw_json"], payload)
        return bundle_paths["response_raw_json"]

    text = body.decode("utf-8", errors="replace")
    write_text_if_changed(bundle_paths["response_raw_text"], text if text.endswith("\n") else text + "\n")
    return bundle_paths["response_raw_text"]


def execute_http_dispatch(
    dispatch: dict[str, Any],
    provider_profile: dict[str, Any],
    *,
    timeout_seconds: int,
) -> dict[str, Any]:
    endpoint = endpoint_for_transport(provider_profile)
    if not endpoint:
        raise ValueError(f"Provider profile {provider_profile['id']} does not expose an HTTP endpoint.")
    request_payload_path = dispatch["request_contract"].get("request_payload_path")
    if not request_payload_path:
        raise ValueError("Dispatch does not include a request payload.")

    request_path = ROOT / request_payload_path
    if not request_path.exists():
        raise ValueError(f"Request payload does not exist: {request_payload_path}")
    request_bytes = request_path.read_bytes()

    headers = {}
    for line in auth_header_lines(provider_profile):
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip()] = value.strip()

    started_at = now_utc()
    started_monotonic = time.perf_counter()
    request = urllib.request.Request(
        endpoint,
        data=request_bytes,
        headers=headers,
        method="POST",
    )

    body: bytes
    http_status: int
    content_type: str | None
    error_text: str | None = None

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read()
            http_status = response.status
            content_type = response.headers.get("content-type")
    except urllib.error.HTTPError as exc:
        body = exc.read()
        http_status = exc.code
        content_type = exc.headers.get("content-type") if exc.headers else None
        error_text = body.decode("utf-8", errors="replace")

    finished_at = now_utc()
    duration_ms = int((time.perf_counter() - started_monotonic) * 1000)
    response_path = persist_provider_response(dispatch, body, content_type)
    request_execution = request_execution_payload(
        dispatch,
        provider_profile,
        started_at=started_at.isoformat().replace("+00:00", "Z"),
        finished_at=finished_at.isoformat().replace("+00:00", "Z"),
        duration_ms=duration_ms,
        http_status=http_status,
        request_bytes=len(request_bytes),
        response_bytes=len(body),
        response_content_type=content_type,
    )
    if error_text:
        request_execution["error"] = error_text[:4000]

    return {
        "ok": 200 <= http_status < 300,
        "response_path": response_path,
        "request_execution": request_execution,
        "http_status": http_status,
        "content_type": content_type,
    }


def bundle_report_for_result(result: dict[str, Any]) -> dict[str, Any]:
    bundle_paths = result_bundle_paths(result)
    return load_json(bundle_paths["report"])


def build_run_from_result(
    result: dict[str, Any],
    result_path: Path,
    benchmark_manifest: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    metrics = parse_pairs(args.metric)
    conditions = dict(result["benchmark_report"].get("recommended_run_conditions", {}))
    provider_execution = result["benchmark_report"].get("provider_execution", {})
    reasoning_effort = provider_execution.get("request_settings", {}).get("reasoning_effort")
    if reasoning_effort:
        conditions["reasoning_effort"] = reasoning_effort
    conditions.update(parse_pairs(args.condition))
    conditions.update(
        {
            "execution_result_id": result["result_id"],
            "execution_mode": result["execution_mode"],
            "result_status": result["status"],
        }
    )

    artifact_paths = unique_strings(
        [
            result["packet_path"],
            result["plan_path"],
            relative_path(result_path),
            relative_path(result_path.with_suffix(".md")),
            *[artifact["path"] for artifact in result_artifact_inventory(result)],
        ]
    )

    title = args.title or f"{result['model_id']} {result['generation_target']['id']} benchmark result"
    summary = args.summary or result["summary"]
    scientific_report = {
        "hypothesis": stringify_report_field(result["benchmark_report"].get("hypothesis")),
        "method": stringify_report_field(result["benchmark_report"].get("method")),
        "result_summary": stringify_report_field(result["benchmark_report"].get("result_summary")),
        "limitations": stringify_report_field(result["benchmark_report"].get("limitations")),
        "next_steps": stringify_report_field(result["benchmark_report"].get("next_steps")),
    }

    run = build_run_payload(
        benchmark_manifest,
        model=result["model_id"],
        title=title,
        status=args.status,
        summary=summary,
        artifact_paths=artifact_paths,
        condition_values=conditions,
        metric_values=metrics,
        recorded_at=recorded_at,
        slug=args.slug,
        scientific_report=scientific_report,
    )
    run["_path"] = relative_path(run_path_for(benchmark_manifest, result["model_id"], run["run_id"]))
    run["_composite_score"] = compute_composite(run, benchmark_manifest)
    return run


def validate_model_provider_links(model_registry: dict[str, Any], provider_registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    profiles = provider_map(provider_registry)
    for model in model_registry["models"]:
        primary = model["provider_profile"]
        if primary not in profiles:
            errors.append(f"models/registry.json: unknown provider_profile `{primary}` for model `{model['id']}`")
        for profile_id in model.get("tool_profiles", []):
            if profile_id not in profiles:
                errors.append(f"models/registry.json: unknown tool profile `{profile_id}` for model `{model['id']}`")
    return errors


def find_matching_packet(candidate_packet: dict[str, Any]) -> Path | None:
    candidate_hash = content_hash(semantic_packet_payload(candidate_packet))
    packet_dir = packet_path_for(candidate_packet["model_id"], candidate_packet["packet_id"], "json").parent
    for path in sorted(packet_dir.glob("*.json")):
        existing = load_json(path)
        if content_hash(semantic_packet_payload(existing)) == candidate_hash:
            return path
    return None


def find_existing_plan(model_id: str, packet_id: str, mode: str) -> Path | None:
    plan_dir = execution_plan_dir_for_model(model_id)
    for path in sorted(plan_dir.glob("*.json")):
        plan = load_json(path)
        if plan["packet_id"] == packet_id and plan["execution_mode"] == mode:
            return path
    return None


def find_existing_result(
    model_id: str,
    plan_id: str,
    *,
    allowed_statuses: set[str] | None = None,
) -> Path | None:
    result_dir = execution_result_dir_for_model(model_id)
    matches: list[tuple[str, str, Path]] = []
    for path in sorted(result_dir.glob("*.json")):
        result = load_json(path)
        if result["plan_id"] != plan_id:
            continue
        if allowed_statuses is not None and result["status"] not in allowed_statuses:
            continue
        matches.append((result["created_at"], result["result_id"], path))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][2]


def find_existing_dispatch(
    model_id: str,
    result_id: str,
    provider_profile_id: str,
    *,
    tool_profile_ids: list[str] | None = None,
    allowed_statuses: set[str] | None = None,
) -> Path | None:
    dispatch_dir = execution_dispatch_dir_for_model(model_id)
    matches: list[tuple[str, str, Path]] = []
    for path in sorted(dispatch_dir.glob("*.json")):
        dispatch = load_json(path)
        if dispatch["result_id"] != result_id or dispatch["provider_profile_id"] != provider_profile_id:
            continue
        if tool_profile_ids is not None and dispatch.get("tool_profile_ids", []) != tool_profile_ids:
            continue
        if allowed_statuses is not None and dispatch["status"] not in allowed_statuses:
            continue
        matches.append((dispatch["created_at"], dispatch["dispatch_id"], path))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][2]


def latest_json_artifact(
    directory: Path,
    *,
    predicate: Any | None = None,
) -> Path | None:
    latest: tuple[str, str, Path] | None = None
    for path in sorted(directory.glob("*.json")):
        data = load_json(path)
        if predicate is not None and not predicate(data):
            continue
        artifact_id = (
            data.get("packet_id")
            or data.get("plan_id")
            or data.get("result_id")
            or data.get("dispatch_id")
            or relative_path(path)
        )
        candidate = (data.get("created_at", ""), artifact_id, path)
        if latest is None or candidate > latest:
            latest = candidate
    return latest[2] if latest else None


def bootstrap_model_set() -> list[str]:
    return [
        "o3",
        "glm-5.1",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.3-codex",
        "gpt-5.3-codex-spark",
        "gpt-5.2-codex",
        "gpt-5.1-codex-max",
        "gpt-5.1-codex-mini",
        "gpt-5-codex",
        "claude-opus-4.1",
        "claude-opus-4",
    ]


def create_packet_for_model(model_id: str, args: argparse.Namespace) -> tuple[Path, bool]:
    packet_args = SimpleNamespace(
        model=model_id,
        track=None,
        recipe=args.recipe,
        kind=args.kind,
        target=args.target,
        slug=args.slug,
        recorded_at=args.recorded_at,
        capability=args.capability,
        locale=args.locale,
        var=args.var,
        dry_run=False,
    )
    packet = build_packet(packet_args)
    existing = find_matching_packet(packet)
    if existing is not None:
        return existing, False

    json_path = packet_path_for(packet["model_id"], packet["packet_id"], "json")
    md_path = packet_path_for(packet["model_id"], packet["packet_id"], "md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown_packet(packet), encoding="utf-8")
    return json_path, True


def create_plan_for_packet(packet_path: Path, model_id: str, args: argparse.Namespace) -> tuple[Path, bool]:
    packet = load_json(packet_path)
    existing = find_existing_plan(model_id, packet["packet_id"], args.mode)
    if existing is not None:
        return existing, False

    plan_args = SimpleNamespace(
        packet=relative_path(packet_path),
        model=model_id,
        mode=args.mode,
        planner_engine=args.planner_engine,
        status=args.status,
        slug=args.slug,
        recorded_at=args.recorded_at,
        openspec_change=args.openspec_change,
        dry_run=False,
    )
    plan = build_plan(plan_args)
    json_path = plan_path_for(plan["model_id"], plan["plan_id"], "json")
    md_path = plan_path_for(plan["model_id"], plan["plan_id"], "md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown_plan(plan), encoding="utf-8")
    return json_path, True


def create_result_for_plan(plan_path: Path, model_id: str, args: argparse.Namespace) -> tuple[Path, bool]:
    plan = load_json(plan_path)
    existing = find_existing_result(
        model_id,
        plan["plan_id"],
        allowed_statuses={"scaffolded", "captured", "reviewed"},
    )
    if existing is not None:
        return existing, False

    result_args = SimpleNamespace(
        plan=relative_path(plan_path),
        model=model_id,
        status=args.result_status,
        summary=args.result_summary,
        slug=args.slug,
        recorded_at=args.recorded_at,
        openspec_change=args.result_openspec_change,
        note=[],
        dry_run=False,
    )
    result = build_result(result_args)
    json_path = result_path_for(result["model_id"], result["result_id"], "json")
    md_path = result_path_for(result["model_id"], result["result_id"], "md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_if_changed(json_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    write_text_if_changed(md_path, build_markdown_result(result))
    scaffold_result_bundle(result)
    return json_path, True


def create_dispatch_for_result(result_path: Path, model_id: str, args: argparse.Namespace) -> tuple[Path, bool]:
    result = load_json(result_path)
    model_registry = load_model_registry()
    model = index_by_id(model_registry["models"])[model_id]
    provider_profile_id = args.profile or model["provider_profile"]
    existing = find_existing_dispatch(
        model_id,
        result["result_id"],
        provider_profile_id,
        tool_profile_ids=model.get("tool_profiles", []),
        allowed_statuses={"prepared", "ready"},
    )
    if existing is not None:
        return existing, False

    dispatch_args = SimpleNamespace(
        result=relative_path(result_path),
        profile=args.profile,
        tool_profile=[],
        status=args.dispatch_status,
        slug=args.slug,
        recorded_at=args.recorded_at,
        dry_run=False,
    )
    dispatch = build_dispatch(dispatch_args)
    json_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "json")
    md_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / dispatch["request_bundle_root"]).mkdir(parents=True, exist_ok=True)
    write_dispatch_files(dispatch)
    sync_result_record(result_path, f"Dispatch bundle created for profile {provider_profile_id}.")
    return json_path, True


def readiness_record_for_model(model_id: str) -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    model = index_by_id(model_registry["models"])[model_id]

    packet_path = latest_json_artifact(packet_path_for(model_id, f"{model_id}--placeholder", "json").parent)
    plan_path = latest_json_artifact(execution_plan_dir_for_model(model_id))
    result_path = latest_json_artifact(
        execution_result_dir_for_model(model_id),
        predicate=lambda data: data["status"] != "archived",
    )
    dispatch_path = latest_json_artifact(
        execution_dispatch_dir_for_model(model_id),
        predicate=lambda data: (
            data["status"] != "archived"
            and data["provider_profile_id"] == model["provider_profile"]
        ),
    )
    auth_status = auth_status_for_model(model, provider_registry)
    primary_ready = auth_status["primary"]["satisfied"]
    tools_ready = all(tool["satisfied"] for tool in auth_status["tools"])
    dispatch_record = load_json(dispatch_path) if dispatch_path else None
    result_record = load_json(result_path) if result_path else None
    plan_record = load_json(plan_path) if plan_path else None

    if dispatch_record is not None:
        result_path = ROOT / dispatch_record["result_path"]
        plan_path = ROOT / dispatch_record["plan_path"]
        packet_path = ROOT / dispatch_record["packet_path"]
        result_record = load_json(result_path)
        plan_record = load_json(plan_path)
    elif result_record is not None:
        plan_path = ROOT / result_record["plan_path"]
        packet_path = ROOT / result_record["packet_path"]
        plan_record = load_json(plan_path)
    elif plan_record is not None:
        packet_path = ROOT / plan_record["packet_path"]

    result_status = result_record["status"] if result_record else None
    dispatch_status = dispatch_record["status"] if dispatch_record else None
    missing_artifacts = [
        label
        for label, present in (
            ("packet", packet_path is not None),
            ("plan", plan_path is not None),
            ("result", result_path is not None),
            ("dispatch", dispatch_path is not None),
        )
        if not present
    ]

    def missing_env_names(payload: dict[str, Any]) -> list[str]:
        requirements = payload["requirements"]
        names = [entry["name"] for entry in requirements["required"] if not entry["present"]]
        for group in requirements.get("required_any", []):
            if not group["satisfied"]:
                names.extend(entry["name"] for entry in group["options"] if not entry["present"])
        return unique_strings(names)

    auth_missing = unique_strings(
        missing_env_names(auth_status["primary"])
        + [name for tool in auth_status["tools"] for name in missing_env_names(tool)]
    )

    if missing_artifacts:
        blocker_reason = f"missing {'+'.join(missing_artifacts)}"
    elif auth_missing:
        blocker_reason = f"missing env: {', '.join(auth_missing)}"
    else:
        blocker_reason = "ready"

    return {
        "benchmark_id": benchmark_manifest["benchmark_id"],
        "model_id": model_id,
        "provider": model["provider"],
        "execution_channel": model["execution_channel"],
        "execution_route": f"{model['execution_channel']} + {model['provider_profile']}",
        "packet_path": relative_path(packet_path) if packet_path else None,
        "plan_path": relative_path(plan_path) if plan_path else None,
        "result_path": relative_path(result_path) if result_path else None,
        "result_status": result_status,
        "dispatch_path": relative_path(dispatch_path) if dispatch_path else None,
        "dispatch_status": dispatch_status,
        "packet_plan_lineage": {
            "packet_path": relative_path(packet_path) if packet_path else None,
            "plan_path": relative_path(plan_path) if plan_path else None,
        },
        "primary_auth_ready": primary_ready,
        "tools_auth_ready": tools_ready,
        "auth_summary": {
            "primary_ready": primary_ready,
            "tools_ready": tools_ready,
            "missing_env": auth_missing,
        },
        "blocker_reason": blocker_reason,
        "ready_for_generation": bool(packet_path and plan_path and result_path and dispatch_path and primary_ready and tools_ready),
        "auth_status": auth_status,
    }


def render_readiness_table(records: list[dict[str, Any]]) -> str:
    lines = [
        "model\trunnable\troute\tprimary_auth\ttools_auth\tresult_status\tdispatch_status\tblocker",
    ]
    for record in records:
        lines.append(
            "\t".join(
                [
                    record["model_id"],
                    "yes" if record["ready_for_generation"] else "no",
                    record["execution_route"],
                    "ready" if record["primary_auth_ready"] else "missing",
                    "ready" if record["tools_auth_ready"] else "missing",
                    record["result_status"] or "-",
                    record["dispatch_status"] or "-",
                    record["blocker_reason"],
                ]
            )
        )
    return "\n".join(lines)


def cmd_readiness_report(args: argparse.Namespace) -> int:
    model_ids = args.model or bootstrap_model_set()
    records = [readiness_record_for_model(model_id) for model_id in model_ids]
    if args.format == "json":
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        print(render_readiness_table(records))
    if args.allow_partial:
        return 0
    return 0 if all(record["ready_for_generation"] for record in records) else 1


def cmd_bootstrap_readiness(args: argparse.Namespace) -> int:
    model_ids = args.model or bootstrap_model_set()
    results: list[str] = []

    for model_id in model_ids:
        packet_path, packet_created = create_packet_for_model(model_id, args)
        plan_path, plan_created = create_plan_for_packet(packet_path, model_id, args)
        result_path, result_created = create_result_for_plan(plan_path, model_id, args)
        dispatch_path, dispatch_created = create_dispatch_for_result(result_path, model_id, args)
        results.append(
            f"{model_id}\t"
            f"packet:{'created' if packet_created else 'reused'}:{relative_path(packet_path)}\t"
            f"plan:{'created' if plan_created else 'reused'}:{relative_path(plan_path)}\t"
            f"result:{'created' if result_created else 'reused'}:{relative_path(result_path)}\t"
            f"dispatch:{'created' if dispatch_created else 'reused'}:{relative_path(dispatch_path)}"
        )

    print("\n".join(results))
    return 0


def cmd_dspy_status(_: argparse.Namespace) -> int:
    print(json.dumps(dspy_status(), indent=2, ensure_ascii=False))
    return 0


def cmd_list_models(_: argparse.Namespace) -> int:
    registry = load_model_registry()
    for model in registry["models"]:
        profiles = ",".join([model["provider_profile"], *model.get("tool_profiles", [])])
        print(
            f"{model['id']}\t{model['provider']}\t{model['execution_channel']}\t{model['status']}\t{profiles}"
        )
    return 0


def cmd_list_profiles(_: argparse.Namespace) -> int:
    registry = load_provider_registry()
    for profile in registry["profiles"]:
        required = ",".join(profile.get("required_env", []))
        any_group = " | ".join(",".join(group) for group in profile.get("required_any_env", []))
        print(
            f"{profile['id']}\t{profile['provider']}\t{profile['transport']}\t{required}\t{any_group}"
        )
    return 0


def cmd_auth_status(args: argparse.Namespace) -> int:
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    models = index_by_id(model_registry["models"])
    profiles = provider_map(provider_registry)

    if args.profile:
        if args.profile not in provider_ids(provider_registry):
            raise SystemExit(f"Unknown profile: {args.profile}")
        payload = auth_status_for_profile(profiles[args.profile])
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0 if payload["satisfied"] or args.allow_missing else 1

    if args.model:
        if args.model not in models:
            raise SystemExit(f"Unknown model: {args.model}")
        payload = auth_status_for_model(models[args.model], provider_registry)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        all_satisfied = payload["primary"]["satisfied"] and all(
            tool["satisfied"] for tool in payload["tools"]
        )
        return 0 if all_satisfied or args.allow_missing else 1

    for model in model_registry["models"]:
        payload = auth_status_for_model(model, provider_registry)
        primary = payload["primary"]
        print(
            f"{model['id']}\t{primary['profile_id']}\t"
            f"{'ready' if primary['satisfied'] else 'missing'}"
        )
    return 0


def cmd_render_config(args: argparse.Namespace) -> int:
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    models = index_by_id(model_registry["models"])
    profiles = provider_map(provider_registry)

    if args.profile:
        profile = profiles[args.profile]
    elif args.model:
        model = models[args.model]
        if args.tool_profile:
            if args.tool_profile not in model.get("tool_profiles", []):
                raise SystemExit(f"Model {args.model} does not expose tool profile {args.tool_profile}")
            profile = profiles[args.tool_profile]
        else:
            profile = profiles[model["provider_profile"]]
    else:
        raise SystemExit("Provide either --profile or --model")

    print(render_profile_config(profile, args.format, args.include_secrets))
    return 0


def cmd_create_plan(args: argparse.Namespace) -> int:
    plan = build_plan(args)
    json_path = plan_path_for(plan["model_id"], plan["plan_id"], "json")
    md_path = plan_path_for(plan["model_id"], plan["plan_id"], "md")

    if json_path.exists() or md_path.exists():
        print(f"Execution plan already exists: {relative_path(json_path)}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(build_markdown_plan(plan), encoding="utf-8")
    print(relative_path(json_path))
    print(relative_path(md_path))
    return 0


def cmd_create_result(args: argparse.Namespace) -> int:
    result = build_result(args)
    json_path = result_path_for(result["model_id"], result["result_id"], "json")
    md_path = result_path_for(result["model_id"], result["result_id"], "md")

    if json_path.exists() or md_path.exists():
        print(f"Execution result already exists: {relative_path(json_path)}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    json_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_if_changed(json_path, json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    write_text_if_changed(md_path, build_markdown_result(result))
    scaffold_result_bundle(result)
    print(relative_path(json_path))
    print(relative_path(md_path))
    print(result["output_root"])
    return 0


def cmd_run_dispatch(args: argparse.Namespace) -> int:
    dispatch_path, dispatch, benchmark_manifest, execution_manifest, model_registry, provider_registry = load_dispatch_with_context(args.dispatch)
    dispatch_errors = validate_dispatch(
        dispatch_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
        provider_registry,
    )
    if dispatch_errors:
        print("\n".join(dispatch_errors), file=sys.stderr)
        return 1

    profiles = provider_map(provider_registry)
    provider_profile = profiles.get(dispatch["provider_profile_id"])
    if provider_profile is None:
        print(f"Unknown provider profile: {dispatch['provider_profile_id']}", file=sys.stderr)
        return 1
    if invocation_kind_for_transport(provider_profile["transport"]) != "http-api":
        print(
            f"Dispatch transport {provider_profile['transport']} is not directly runnable via run-dispatch.",
            file=sys.stderr,
        )
        return 1

    auth_status = auth_status_for_profile(provider_profile)
    if not auth_status["satisfied"]:
        print(
            f"Provider profile {provider_profile['id']} is not authenticated in the current environment.",
            file=sys.stderr,
        )
        return 1

    try:
        execution = execute_http_dispatch(
            dispatch,
            provider_profile,
            timeout_seconds=args.timeout_seconds,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    dispatch["request_execution"] = execution["request_execution"]
    dispatch["status"] = "sent"

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dispatch": dispatch,
                    "response_path": display_path(execution["response_path"]),
                    "http_status": execution["http_status"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    write_dispatch_files(dispatch)

    if not execution["ok"]:
        print(
            f"Provider request failed with HTTP {execution['http_status']}. "
            f"Raw response captured at {display_path(execution['response_path'])}.",
            file=sys.stderr,
        )
        return 1

    if args.no_ingest:
        print(relative_path(dispatch_path))
        print(display_path(execution["response_path"]))
        return 0

    ingest_args = SimpleNamespace(
        dispatch=relative_path(dispatch_path),
        source=display_path(execution["response_path"]),
        source_format="auto",
        status=args.status,
        dispatch_status=args.dispatch_status,
        summary=args.summary,
        recorded_at=args.recorded_at or execution["request_execution"]["finished_at"],
        note=args.note,
        dry_run=False,
    )
    return cmd_ingest_response(ingest_args)


def read_agent_response_text(args: argparse.Namespace) -> tuple[str, str]:
    source = getattr(args, "source", None)
    read_from_stdin = bool(getattr(args, "stdin", False))
    if bool(source) == read_from_stdin:
        raise ValueError("Choose exactly one of --source or --stdin.")

    if read_from_stdin:
        text = sys.stdin.read()
        if not text.strip():
            raise ValueError("No response text received on stdin.")
        return text, "stdin"

    assert source is not None
    source_path = (ROOT / source).resolve() if not Path(source).is_absolute() else Path(source).resolve()
    if not source_path.exists():
        raise ValueError(f"Response source does not exist: {source_path}")
    text = source_path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Response source is empty: {display_path(source_path)}")
    return text, display_path(source_path)


def cmd_capture_agent_response(args: argparse.Namespace) -> int:
    dispatch_path, dispatch, benchmark_manifest, execution_manifest, model_registry, provider_registry = load_dispatch_with_context(args.dispatch)
    dispatch_errors = validate_dispatch(
        dispatch_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
        provider_registry,
    )
    if dispatch_errors:
        print("\n".join(dispatch_errors), file=sys.stderr)
        return 1

    if dispatch["transport"] not in {"workspace-agent", "claude-code", "claude-code-bridge"}:
        print(
            f"capture-agent-response only supports agent transports, not {dispatch['transport']}.",
            file=sys.stderr,
        )
        return 1

    if args.status not in execution_manifest["result_status_values"]:
        print(f"Unsupported execution result status: {args.status}", file=sys.stderr)
        return 1
    if args.dispatch_status not in execution_manifest["dispatch_status_values"]:
        print(f"Unsupported dispatch status: {args.dispatch_status}", file=sys.stderr)
        return 1

    try:
        response_text, response_source = read_agent_response_text(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    finished_at = args.finished_at or (args.recorded_at or now_utc().isoformat().replace("+00:00", "Z"))
    started_at = args.started_at or dispatch["created_at"]
    try:
        request_execution = agent_capture_request_execution_payload(
            dispatch,
            started_at=started_at,
            finished_at=finished_at,
            response_text=response_text,
            runner=args.runner,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    canonical_text_path = ROOT / dispatch["response_contract"]["fallback_text_response_path"]
    dispatch["request_execution"] = request_execution
    if args.no_ingest and args.dispatch_status == "captured":
        print(
            "--no-ingest cannot leave the dispatch in captured state because response artifacts have not been normalized yet.",
            file=sys.stderr,
        )
        return 1
    dispatch["status"] = args.dispatch_status if args.no_ingest else "sent"

    if args.dry_run:
        preview = {
            "dispatch": dispatch,
            "response_path": dispatch["response_contract"]["fallback_text_response_path"],
            "response_bytes": len(response_text.encode("utf-8")),
        }
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return 0

    write_text_if_changed(
        canonical_text_path,
        response_text if response_text.endswith("\n") else response_text + "\n",
    )
    dispatch["request_artifacts"] = dispatch_artifact_inventory(dispatch)
    write_dispatch_files(dispatch)

    if args.no_ingest:
        print(relative_path(dispatch_path))
        print(relative_path(canonical_text_path))
        return 0

    ingest_args = SimpleNamespace(
        dispatch=relative_path(dispatch_path),
        source=relative_path(canonical_text_path),
        source_format="text",
        status=args.status,
        dispatch_status=args.dispatch_status,
        summary=args.summary,
        recorded_at=finished_at,
        note=[
            "Agent response captured through benchmark_execute.py capture-agent-response.",
            *args.note,
        ],
        dry_run=False,
    )
    return cmd_ingest_response(ingest_args)


def cmd_create_dispatch(args: argparse.Namespace) -> int:
    result_path, result, benchmark_manifest, execution_manifest, model_registry, provider_registry = load_result_with_context(args.result)
    errors = validate_result(result_path, execution_manifest, benchmark_manifest, model_registry)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    dispatch = build_dispatch(args)
    json_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "json")
    md_path = dispatch_path_for(dispatch["model_id"], dispatch["dispatch_id"], "md")

    if json_path.exists() or md_path.exists():
        print(f"Dispatch already exists: {relative_path(json_path)}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(dispatch, indent=2, ensure_ascii=False))
        return 0

    json_path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / dispatch["request_bundle_root"]).mkdir(parents=True, exist_ok=True)
    write_dispatch_files(dispatch)
    sync_result_record(result_path, f"Dispatch bundle created for profile {dispatch['provider_profile_id']}.")
    validation_errors = validate_dispatch(
        json_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
        provider_registry,
    )
    if validation_errors:
        print("\n".join(validation_errors), file=sys.stderr)
        return 1

    result["notes"] = append_unique_notes(
        result.get("notes", []),
        [f"Dispatch bundle prepared via {dispatch['provider_profile_id']}."],
    )
    result["artifacts"] = result_artifact_inventory(
        {
            **result,
            "artifacts": [
                *result.get("artifacts", []),
                *dispatch["request_artifacts"],
            ],
        }
    )
    write_result_files(result, sync_bundle_report=False)

    print(relative_path(json_path))
    print(relative_path(md_path))
    print(dispatch["request_bundle_root"])
    return 0


def cmd_prepare_dispatch(args: argparse.Namespace) -> int:
    alias_args = SimpleNamespace(
        result=args.result,
        profile=args.profile,
        tool_profile=[],
        status="prepared",
        slug=None,
        recorded_at=args.recorded_at,
        reasoning_effort=getattr(args, "reasoning_effort", None),
        max_output_tokens=getattr(args, "max_output_tokens", None),
        dry_run=args.dry_run,
    )

    if not args.allow_missing:
        provider_registry = load_provider_registry()
        model_registry = load_model_registry()
        profiles = provider_map(provider_registry)
        models = index_by_id(model_registry["models"])
        result_path, result, _benchmark_manifest, _execution_manifest, _model_registry, _provider_registry = load_result_with_context(args.result)
        _ = result_path
        model = models[result["model_id"]]
        profile_id = args.profile or model["provider_profile"]
        if profile_id in profiles:
            profile_status = auth_status_for_profile(profiles[profile_id])
            if not profile_status["satisfied"]:
                print(
                    f"Provider profile {profile_id} is not ready. Use --allow-missing to prepare the bundle anyway.",
                    file=sys.stderr,
                )
                return 1

    return cmd_create_dispatch(alias_args)


def cmd_ingest_response(args: argparse.Namespace) -> int:
    dispatch_path, dispatch, benchmark_manifest, execution_manifest, model_registry, provider_registry = load_dispatch_with_context(args.dispatch)
    dispatch_errors = validate_dispatch(
        dispatch_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
        provider_registry,
    )
    if dispatch_errors:
        print("\n".join(dispatch_errors), file=sys.stderr)
        return 1

    if args.status not in execution_manifest["result_status_values"]:
        print(f"Unsupported execution result status: {args.status}", file=sys.stderr)
        return 1
    if args.dispatch_status not in execution_manifest["dispatch_status_values"]:
        print(f"Unsupported dispatch status: {args.dispatch_status}", file=sys.stderr)
        return 1

    result_path = ROOT / dispatch["result_path"]
    result = load_json(result_path)
    result_errors = validate_result(result_path, execution_manifest, benchmark_manifest, model_registry)
    if result_errors:
        print("\n".join(result_errors), file=sys.stderr)
        return 1

    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    recorded_at_text = recorded_at.isoformat().replace("+00:00", "Z")

    try:
        captured_response = read_response_source(
            dispatch,
            args.source,
            args.source_format,
            persist=not args.dry_run,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parsed_response = parse_generation_response_text(captured_response["assistant_text"])
    merged_report, report_warnings = merge_ingested_benchmark_report(
        result["benchmark_report"],
        parsed_response,
    )

    result["benchmark_report"] = merged_report
    result["benchmark_report"]["score_ready"] = False
    result["benchmark_report"]["scoring_status"] = "pending-review"
    result["benchmark_report"]["next_steps"] = [
        "Review the generated files under executions/output/.../generated/.",
        "Add screenshots or recordings under executions/output/.../captures/ if needed.",
        "Mark the result reviewed or promote it into a scored run once evaluation is ready.",
    ]
    result["status"] = args.status
    if args.summary:
        result["summary"] = args.summary
    elif parsed_response["summary"]:
        result["summary"] = parsed_response["summary"]
    result["review_state"] = review_state_for_status(
        result.get("review_state", {}),
        status=args.status,
        recorded_at=recorded_at_text,
        score_ready=False,
    )
    result["openspec_refs"] = unique_strings(
        [
            *result.get("openspec_refs", []),
            "openspec/specs/response-ingestion/spec.md",
            "openspec/changes/add-response-ingestion-flow",
        ]
    )

    generation_manifest_preview = {
        "version": 1,
        "dispatch_id": dispatch["dispatch_id"],
        "result_id": result["result_id"],
        "captured_at": recorded_at_text,
        "assistant_response_path": f"{result['output_root']}/generated/response.md",
        "captured_response_path": display_path(captured_response["canonical_path"]),
        "response_text_path": dispatch["response_contract"]["extracted_text_path"],
        "response_normalized_path": dispatch["response_contract"]["normalized_response_path"],
        "generated_files": [entry["path"] for entry in parsed_response["file_entries"]],
        "generated_file_count": len(parsed_response["file_entries"]),
        "provider_response": captured_response["metadata"],
        "warnings": unique_strings([*captured_response["warnings"], *parsed_response["warnings"], *report_warnings]),
    }

    pricing_manifest = load_pricing_manifest()
    normalized_usage = normalize_usage_payload(captured_response["metadata"].get("usage"))
    pricing_entry = pricing_entry_for_model(
        pricing_manifest,
        model_id=result["model_id"],
        provider_model=captured_response["metadata"].get("provider_model"),
    )
    pricing_source = source_entry_for_pricing(
        pricing_manifest,
        pricing_entry.get("source_id") if pricing_entry else None,
    )
    cost_estimate = estimate_cost_from_usage(normalized_usage, pricing_entry, pricing_source)
    generation_manifest_preview["normalized_usage"] = normalized_usage
    generation_manifest_preview["cost_estimate"] = cost_estimate

    result["benchmark_report"]["provider_execution"] = {
        "dispatch_id": dispatch["dispatch_id"],
        "provider_profile_id": dispatch["provider_profile_id"],
        "transport": dispatch["transport"],
        "captured_at": recorded_at_text,
        "packet_id": result["packet_id"],
        "request_settings": dispatch.get("request_settings", {}),
        "request_execution": dispatch.get("request_execution"),
        "prompt_bundle_path": dispatch["request_contract"].get("prompt_bundle_path"),
        "prompt_bundle_hash": dispatch["request_contract"].get("prompt_bundle_hash"),
        "request_payload_path": dispatch["request_contract"].get("request_payload_path"),
        "request_payload_hash": dispatch["request_contract"].get("request_payload_hash"),
        "response_id": captured_response["metadata"].get("response_id"),
        "provider_model": captured_response["metadata"].get("provider_model"),
        "status": captured_response["metadata"].get("status"),
        "finish_reasons": captured_response["metadata"].get("finish_reasons", []),
        "usage": captured_response["metadata"].get("usage"),
        "normalized_usage": normalized_usage,
        "cost_estimate": cost_estimate,
        "generated_manifest_path": dispatch["response_contract"]["generated_manifest_path"],
        "generated_files": generation_manifest_preview["generated_files"],
    }

    dispatch["status"] = args.dispatch_status
    dispatch["response_capture"] = {
        "captured_at": recorded_at_text,
        "source_format": captured_response["source_format"],
        "source_path": display_path(captured_response["source_path"]),
        "canonical_response_path": display_path(captured_response["canonical_path"]),
        "normalized_response_path": dispatch["response_contract"]["normalized_response_path"],
        "assistant_text_path": dispatch["response_contract"]["extracted_text_path"],
        "generated_manifest_path": dispatch["response_contract"]["generated_manifest_path"],
        "extracted_file_count": len(parsed_response["file_entries"]),
        "request_settings": dispatch.get("request_settings", {}),
        "request_execution": dispatch.get("request_execution"),
        "provider_response": captured_response["metadata"],
        "normalized_usage": normalized_usage,
        "cost_estimate": cost_estimate,
        "warnings": generation_manifest_preview["warnings"],
    }

    note_lines = [
        f"Ingested provider response for dispatch {dispatch['dispatch_id']}.",
        *[f"Ingest warning: {warning}" for warning in generation_manifest_preview["warnings"]],
        *args.note,
    ]
    result["notes"] = append_unique_notes(result.get("notes", []), note_lines)

    if args.dry_run:
        preview = {
            "dispatch": dispatch,
            "result": result,
            "generation_manifest": generation_manifest_preview,
        }
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        return 0

    generation_manifest = write_ingested_generation_artifacts(
        dispatch,
        result,
        captured_response,
        parsed_response,
        recorded_at_text,
    )
    dispatch["response_capture"]["generated_manifest_path"] = dispatch["response_contract"]["generated_manifest_path"]
    dispatch["request_artifacts"] = dispatch_artifact_inventory(dispatch)
    write_dispatch_files(dispatch)
    result["artifacts"] = result_artifact_inventory(result)
    write_result_files(result, sync_bundle_report=True)

    dispatch_validation_errors = validate_dispatch(
        dispatch_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
        provider_registry,
    )
    result_validation_errors = validate_result(
        result_path,
        execution_manifest,
        benchmark_manifest,
        model_registry,
    )
    all_errors = [*dispatch_validation_errors, *result_validation_errors]
    if all_errors:
        print("\n".join(all_errors), file=sys.stderr)
        return 1

    print(relative_path(dispatch_path))
    print(relative_path(result_path))
    print(generation_manifest["assistant_response_path"])
    return 0


def cmd_capture_result(args: argparse.Namespace) -> int:
    if args.score_ready and args.clear_score_ready:
        print("Choose only one of --score-ready or --clear-score-ready.", file=sys.stderr)
        return 1

    result_path, result, benchmark_manifest, execution_manifest, model_registry, _provider_registry = load_result_with_context(args.result)
    if args.status not in execution_manifest["result_status_values"]:
        print(f"Unsupported execution result status: {args.status}", file=sys.stderr)
        return 1
    errors = validate_result(result_path, execution_manifest, benchmark_manifest, model_registry)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    recorded_at_text = recorded_at.isoformat().replace("+00:00", "Z")
    result["benchmark_report"] = bundle_report_for_result(result)
    result["status"] = args.status
    if args.summary:
        result["summary"] = args.summary

    score_ready_override: bool | None = None
    if args.score_ready:
        score_ready_override = True
    elif args.clear_score_ready:
        score_ready_override = False

    score_ready = score_ready_override
    if score_ready is None and "score_ready" in result["benchmark_report"]:
        score_ready = bool(result["benchmark_report"]["score_ready"])

    result["review_state"] = review_state_for_status(
        result.get("review_state", {}),
        status=args.status,
        recorded_at=recorded_at_text,
        score_ready=score_ready,
    )
    result["notes"] = append_unique_notes(
        result.get("notes", []),
        [
            "Result bundle synced from benchmark_report.json.",
            *args.note,
        ],
    )
    result["artifacts"] = result_artifact_inventory(result)
    consistency_errors = validate_result_consistency(
        result,
        benchmark_manifest,
        relative_path(result_path),
    )
    if consistency_errors:
        print("\n".join(consistency_errors), file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    write_result_files(result, sync_bundle_report=False)
    print(relative_path(result_path))
    return 0


def cmd_promote_result(args: argparse.Namespace) -> int:
    result_path, result, benchmark_manifest, execution_manifest, model_registry, _provider_registry = load_result_with_context(args.result)
    errors = validate_result(result_path, execution_manifest, benchmark_manifest, model_registry)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    if result["status"] == "scaffolded" and not (args.allow_scaffolded or args.dry_run):
        print(
            "Scaffolded results cannot be promoted directly. Capture or review the result first, or use --allow-scaffolded.",
            file=sys.stderr,
        )
        return 1

    run = build_run_from_result(result, result_path, benchmark_manifest, args)
    validation_target = dict(run)
    run_errors = validate_run(validation_target, benchmark_manifest)
    run.pop("_path", None)
    run.pop("_composite_score", None)

    if run_errors:
        print("\n".join(run_errors), file=sys.stderr)
        return 1

    run_target = run_path_for(benchmark_manifest, result["model_id"], run["run_id"])
    if run_target.exists():
        print(f"Run already exists: {relative_path(run_target)}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(json.dumps(run, indent=2, ensure_ascii=False))
        return 0

    run_target.parent.mkdir(parents=True, exist_ok=True)
    write_text_if_changed(run_target, json.dumps(run, indent=2, ensure_ascii=False) + "\n")

    promoted_at = now_utc().isoformat().replace("+00:00", "Z")
    result["status"] = "linked"
    result["review_state"] = review_state_for_status(
        result.get("review_state", {}),
        status="linked",
        recorded_at=promoted_at,
        score_ready=True,
    )
    result["review_state"]["linked_run_id"] = run["run_id"]
    result["review_state"]["linked_run_path"] = relative_path(run_target)
    result["review_state"]["promoted_at"] = promoted_at
    result["benchmark_report"]["score_ready"] = True
    result["benchmark_report"]["scoring_status"] = run["status"]
    result["notes"] = append_unique_notes(
        result.get("notes", []),
        [
            f"Promoted into benchmark run {run['run_id']}.",
            *args.note,
        ],
    )
    result["artifacts"] = result_artifact_inventory(result)
    write_result_files(result, sync_bundle_report=True)

    print(relative_path(run_target))
    print(relative_path(result_path))
    return 0


def cmd_bootstrap_comparison(args: argparse.Namespace) -> int:
    model_ids = args.model or bootstrap_model_set()
    results: list[str] = []

    for model_id in model_ids:
        packet_path, packet_created = create_packet_for_model(model_id, args)
        plan_path, plan_created = create_plan_for_packet(packet_path, model_id, args)
        results.append(
            f"{model_id}\tpacket:{'created' if packet_created else 'reused'}:{relative_path(packet_path)}\t"
            f"plan:{'created' if plan_created else 'reused'}:{relative_path(plan_path)}"
        )

    print("\n".join(results))
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    execution_manifest = load_execution_manifest()
    benchmark_manifest = load_benchmark_manifest()
    model_registry = load_model_registry()
    provider_registry = load_provider_registry()
    errors: list[str] = []

    errors.extend(validate_model_provider_links(model_registry, provider_registry))

    for model_id in track_ids(benchmark_manifest):
        for path in sorted(execution_plan_dir_for_model(model_id).glob("*.json")):
            errors.extend(validate_plan(path, execution_manifest, benchmark_manifest, model_registry))
        for path in sorted(execution_result_dir_for_model(model_id).glob("*.json")):
            errors.extend(validate_result(path, execution_manifest, benchmark_manifest, model_registry))
        for path in sorted(execution_dispatch_dir_for_model(model_id).glob("*.json")):
            errors.extend(
                validate_dispatch(
                    path,
                    execution_manifest,
                    benchmark_manifest,
                    model_registry,
                    provider_registry,
                )
            )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    plan_count = sum(
        len(list(execution_plan_dir_for_model(model_id).glob("*.json")))
        for model_id in track_ids(benchmark_manifest)
    )
    result_count = sum(
        len(list(execution_result_dir_for_model(model_id).glob("*.json")))
        for model_id in track_ids(benchmark_manifest)
    )
    dispatch_count = sum(
        len(list(execution_dispatch_dir_for_model(model_id).glob("*.json")))
        for model_id in track_ids(benchmark_manifest)
    )
    print(
        f"Validated {plan_count} execution plan(s), {result_count} execution result(s), "
        f"and {dispatch_count} dispatch bundle(s)."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesseract benchmark execution CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dspy_cmd = subparsers.add_parser("dspy-status", help="Report DSPy import/runtime status")
    dspy_cmd.set_defaults(func=cmd_dspy_status)

    list_models = subparsers.add_parser("list-models", help="List execution-capable models")
    list_models.set_defaults(func=cmd_list_models)

    list_profiles = subparsers.add_parser("list-profiles", help="List provider/tool profiles")
    list_profiles.set_defaults(func=cmd_list_profiles)

    auth = subparsers.add_parser("auth-status", help="Report provider credential readiness")
    auth.add_argument("--model", help="Model id")
    auth.add_argument("--profile", help="Provider profile id")
    auth.add_argument("--allow-missing", action="store_true", help="Return success even if credentials are missing")
    auth.set_defaults(func=cmd_auth_status)

    render = subparsers.add_parser("render-config", help="Render provider/tool configuration snippets")
    render.add_argument("--model", help="Model id")
    render.add_argument("--profile", help="Provider profile id")
    render.add_argument("--tool-profile", help="Tool profile to use for the given model")
    render.add_argument("--format", choices=["shell", "json", "claude-settings"], default="shell")
    render.add_argument("--include-secrets", action="store_true", help="Resolve env references using current environment")
    render.set_defaults(func=cmd_render_config)

    readiness = subparsers.add_parser("readiness-report", help="Report whether models are ready for actual generation")
    readiness.add_argument("--model", action="append", default=[], help="Model id to include. Repeat as needed.")
    readiness.add_argument("--format", choices=["table", "json"], default="table")
    readiness.add_argument("--allow-partial", action="store_true", help="Return success even if some models are not ready")
    readiness.set_defaults(func=cmd_readiness_report)

    validate = subparsers.add_parser("validate", help="Validate execution plans, results, dispatch bundles, and captured response artifacts")
    validate.set_defaults(func=cmd_validate)

    create = subparsers.add_parser("create-plan", help="Create an execution plan from a packet")
    create.add_argument("--packet", required=True, help="Path to a prompt packet JSON file")
    create.add_argument("--model", help="Optional explicit model id. Defaults to packet model_id.")
    create.add_argument("--mode", default="plan-only", help="Execution mode")
    create.add_argument("--planner-engine", default="dspy", help="Planner engine id")
    create.add_argument("--status", default="planned", help="Execution plan status")
    create.add_argument("--slug", help="Optional slug override")
    create.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create.add_argument(
        "--openspec-change",
        default="add-dspy-openspec-execution",
        help="OpenSpec change directory name",
    )
    create.add_argument("--dry-run", action="store_true", help="Print the plan JSON without writing files")
    create.set_defaults(func=cmd_create_plan)

    create_result = subparsers.add_parser("create-result", help="Create an execution result from a plan")
    create_result.add_argument("--plan", required=True, help="Path to an execution plan JSON file")
    create_result.add_argument("--model", help="Optional explicit model id. Defaults to plan model_id.")
    create_result.add_argument("--status", default="scaffolded", help="Execution result status")
    create_result.add_argument("--summary", help="Optional summary override")
    create_result.add_argument("--slug", help="Optional slug override")
    create_result.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create_result.add_argument(
        "--openspec-change",
        default="add-execution-results-layer",
        help="OpenSpec change directory name",
    )
    create_result.add_argument("--note", action="append", default=[], help="Additional note to append. Repeat as needed.")
    create_result.add_argument("--dry-run", action="store_true", help="Print the result JSON without writing files")
    create_result.set_defaults(func=cmd_create_result)

    create_dispatch = subparsers.add_parser("create-dispatch", help="Create a provider dispatch bundle from a result")
    create_dispatch.add_argument("--result", required=True, help="Path to an execution result JSON file")
    create_dispatch.add_argument("--profile", help="Optional provider profile override")
    create_dispatch.add_argument("--tool-profile", action="append", default=[], help="Optional tool profile override. Repeat as needed.")
    create_dispatch.add_argument("--status", default="prepared", help="Dispatch status")
    create_dispatch.add_argument("--slug", help="Optional slug override")
    create_dispatch.add_argument("--reasoning-effort", choices=REASONING_EFFORT_VALUES, help="Optional provider-neutral reasoning effort setting")
    create_dispatch.add_argument("--max-output-tokens", type=int, help="Optional max output tokens cap")
    create_dispatch.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create_dispatch.add_argument("--dry-run", action="store_true", help="Print the dispatch JSON without writing files")
    create_dispatch.set_defaults(func=cmd_create_dispatch)

    run_dispatch = subparsers.add_parser("run-dispatch", help="Execute an HTTP-backed dispatch bundle and optionally ingest the response")
    run_dispatch.add_argument("--dispatch", required=True, help="Path to a dispatch JSON file")
    run_dispatch.add_argument("--timeout-seconds", type=int, default=600, help="HTTP request timeout in seconds")
    run_dispatch.add_argument("--status", default="captured", help="Result status after ingestion")
    run_dispatch.add_argument("--dispatch-status", default="captured", help="Dispatch status after ingestion")
    run_dispatch.add_argument("--summary", help="Optional result summary override")
    run_dispatch.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    run_dispatch.add_argument("--note", action="append", default=[], help="Additional note to append after ingestion. Repeat as needed.")
    run_dispatch.add_argument("--no-ingest", action="store_true", help="Only execute the request and persist the raw response")
    run_dispatch.add_argument("--dry-run", action="store_true", help="Execute nothing and print the planned state transition")
    run_dispatch.set_defaults(func=cmd_run_dispatch)

    capture_agent = subparsers.add_parser(
        "capture-agent-response",
        help="Capture a Codex/Claude-style agent response into a dispatch bundle and ingest it",
    )
    capture_agent.add_argument("--dispatch", required=True, help="Path to a dispatch JSON file")
    capture_agent.add_argument("--source", help="Path to a text/markdown response file")
    capture_agent.add_argument("--stdin", action="store_true", help="Read the agent response from stdin")
    capture_agent.add_argument("--started-at", help="Approximate agent start timestamp in UTC")
    capture_agent.add_argument("--finished-at", help="Agent completion timestamp in UTC")
    capture_agent.add_argument("--recorded-at", help="Fallback capture timestamp in UTC")
    capture_agent.add_argument(
        "--runner",
        default="benchmark_execute.py capture-agent-response",
        help="Runner label to persist in provenance",
    )
    capture_agent.add_argument("--status", default="captured", help="Result status after ingestion")
    capture_agent.add_argument("--dispatch-status", default="captured", help="Dispatch status after capture")
    capture_agent.add_argument("--summary", help="Optional result summary override")
    capture_agent.add_argument("--note", action="append", default=[], help="Additional note")
    capture_agent.add_argument("--no-ingest", action="store_true", help="Persist the agent response but skip result ingestion")
    capture_agent.add_argument("--dry-run", action="store_true", help="Print the updated dispatch preview without writing files")
    capture_agent.set_defaults(func=cmd_capture_agent_response)

    ingest_response = subparsers.add_parser("ingest-response", help="Ingest a raw provider response into the linked result bundle")
    ingest_response.add_argument("--dispatch", required=True, help="Path to a dispatch JSON file")
    ingest_response.add_argument("--source", help="Optional raw response source path. Defaults to the dispatch bundle response files.")
    ingest_response.add_argument("--source-format", choices=["auto", "json", "markdown", "text"], default="auto")
    ingest_response.add_argument("--status", default="captured", help="Result status after ingestion")
    ingest_response.add_argument("--dispatch-status", default="captured", help="Dispatch status after ingestion")
    ingest_response.add_argument("--summary", help="Optional result summary override")
    ingest_response.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    ingest_response.add_argument("--note", action="append", default=[], help="Additional note to append. Repeat as needed.")
    ingest_response.add_argument("--dry-run", action="store_true", help="Print the updated dispatch/result payloads without writing files")
    ingest_response.set_defaults(func=cmd_ingest_response)

    bootstrap_ready = subparsers.add_parser("bootstrap-readiness", help="Bootstrap packet, plan, result, and dispatch artifacts for a model set")
    bootstrap_ready.add_argument("--model", action="append", default=[], help="Model id to include. Repeat as needed.")
    bootstrap_ready.add_argument("--recipe", default="baseline-webgpu-hypertesseract")
    bootstrap_ready.add_argument("--kind", default="one-liner")
    bootstrap_ready.add_argument("--target", default="ts-webgpu")
    bootstrap_ready.add_argument("--mode", default="plan-only")
    bootstrap_ready.add_argument("--planner-engine", default="dspy")
    bootstrap_ready.add_argument("--status", default="planned")
    bootstrap_ready.add_argument("--result-status", default="scaffolded")
    bootstrap_ready.add_argument("--dispatch-status", default="prepared")
    bootstrap_ready.add_argument("--result-summary", help="Optional summary override for created results")
    bootstrap_ready.add_argument("--profile", help="Optional provider profile override for dispatch creation")
    bootstrap_ready.add_argument("--slug", help="Optional shared slug override")
    bootstrap_ready.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    bootstrap_ready.add_argument("--openspec-change", default="add-dspy-openspec-execution")
    bootstrap_ready.add_argument("--result-openspec-change", default="add-execution-results-layer")
    bootstrap_ready.add_argument("--capability", action="append", default=[])
    bootstrap_ready.add_argument("--locale", action="append", default=[])
    bootstrap_ready.add_argument("--var", action="append", default=[])
    bootstrap_ready.set_defaults(func=cmd_bootstrap_readiness)

    capture_result = subparsers.add_parser("capture-result", help="Sync a result record from its output bundle")
    capture_result.add_argument("--result", required=True, help="Path to an execution result JSON file")
    capture_result.add_argument("--status", default="captured", help="Result status after sync")
    capture_result.add_argument("--summary", help="Optional summary override")
    capture_result.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    capture_result.add_argument("--score-ready", action="store_true", help="Mark the result as score-ready")
    capture_result.add_argument("--clear-score-ready", action="store_true", help="Clear the score-ready flag")
    capture_result.add_argument("--note", action="append", default=[], help="Additional note to append. Repeat as needed.")
    capture_result.add_argument("--dry-run", action="store_true", help="Print the updated result JSON without writing files")
    capture_result.set_defaults(func=cmd_capture_result)

    promote_result = subparsers.add_parser("promote-result", help="Create a benchmark run from a reviewed result")
    promote_result.add_argument("--result", required=True, help="Path to an execution result JSON file")
    promote_result.add_argument("--title", help="Optional run title override")
    promote_result.add_argument("--summary", help="Optional run summary override")
    promote_result.add_argument("--slug", help="Optional run slug override")
    promote_result.add_argument("--status", default="in-progress", help="Run status")
    promote_result.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    promote_result.add_argument("--condition", action="append", default=[], help="Additional run condition as KEY=VALUE")
    promote_result.add_argument("--metric", action="append", default=[], help="Run metric as KEY=VALUE")
    promote_result.add_argument("--note", action="append", default=[], help="Additional note to append to the result record")
    promote_result.add_argument("--allow-scaffolded", action="store_true", help="Allow promotion from a scaffolded result")
    promote_result.add_argument("--dry-run", action="store_true", help="Print the run JSON without writing files")
    promote_result.set_defaults(func=cmd_promote_result)

    prepare_dispatch = subparsers.add_parser("prepare-dispatch", help="Prepare a provider dispatch bundle from a result")
    prepare_dispatch.add_argument("--result", required=True, help="Path to an execution result JSON file")
    prepare_dispatch.add_argument("--profile", help="Provider or tool profile id to prepare")
    prepare_dispatch.add_argument("--reasoning-effort", choices=REASONING_EFFORT_VALUES, help="Optional provider-neutral reasoning effort setting")
    prepare_dispatch.add_argument("--max-output-tokens", type=int, help="Optional max output tokens cap")
    prepare_dispatch.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    prepare_dispatch.add_argument("--allow-missing", action="store_true", help="Prepare the bundle even if credentials are missing")
    prepare_dispatch.add_argument("--dry-run", action="store_true", help="Print the dispatch request JSON without writing files")
    prepare_dispatch.set_defaults(func=cmd_prepare_dispatch)

    bootstrap = subparsers.add_parser("bootstrap-comparison", help="Create comparable packet/plan pairs for a model set")
    bootstrap.add_argument("--model", action="append", default=[], help="Model id to include. Repeat as needed.")
    bootstrap.add_argument("--recipe", default="baseline-webgpu-hypertesseract")
    bootstrap.add_argument("--kind", default="one-liner")
    bootstrap.add_argument("--target", default="ts-webgpu")
    bootstrap.add_argument("--mode", default="plan-only")
    bootstrap.add_argument("--planner-engine", default="dspy")
    bootstrap.add_argument("--status", default="planned")
    bootstrap.add_argument("--slug", help="Optional shared slug override")
    bootstrap.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    bootstrap.add_argument("--openspec-change", default="add-dspy-openspec-execution")
    bootstrap.add_argument("--capability", action="append", default=[])
    bootstrap.add_argument("--locale", action="append", default=[])
    bootstrap.add_argument("--var", action="append", default=[])
    bootstrap.set_defaults(func=cmd_bootstrap_comparison)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
