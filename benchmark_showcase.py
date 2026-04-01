from __future__ import annotations

import argparse
import difflib
import html
import json
import mimetypes
import os
from pathlib import Path
from typing import Any

from benchmark_core import (
    ROOT,
    execution_result_dir_for_model,
    load_benchmark_manifest,
    load_showcase_manifest,
    now_utc,
    parse_timestamp,
    relative_path,
    showcase_comparison_dir,
    showcase_site_dir,
    slugify,
    unique_strings,
    write_json_if_changed,
    write_text_if_changed,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def comparison_path_for(comparison_id: str, suffix: str) -> Path:
    serial = comparison_id.split("--", 1)[1]
    return showcase_comparison_dir() / f"{serial}.{suffix}"


def site_root_for(comparison_id: str) -> Path:
    serial = comparison_id.split("--", 1)[1]
    return showcase_site_dir() / serial


def site_paths_for(comparison_id: str) -> dict[str, Path]:
    root = site_root_for(comparison_id)
    return {
        "root": root,
        "html": root / "index.html",
        "css": root / "styles.css",
        "js": root / "app.js",
        "data": root / "comparison.json",
    }


def showcase_index_paths() -> dict[str, Path]:
    root = showcase_site_dir()
    return {
        "root": root,
        "html": root / "index.html",
        "data": root / "index.json",
    }


def resolve_reference_path(reference: str) -> Path:
    path = Path(reference)
    resolved = path if path.is_absolute() else (ROOT / path).resolve()
    if not resolved.exists():
        raise ValueError(f"Reference does not exist: {reference}")
    return resolved


def infer_reference_kind(path: Path, payload: dict[str, Any]) -> str:
    if "result_id" in payload:
        return "result"
    if "run_id" in payload:
        return "run"
    raise ValueError(f"Unsupported comparison reference: {relative_path(path)}")


def classify_capture_device(name: str, showcase_manifest: dict[str, Any]) -> str | None:
    lowered = name.casefold()
    hints = showcase_manifest["capture_filename_hints"]
    for device_id, tokens in hints.items():
        if any(token in lowered for token in tokens):
            return device_id
    return None


def list_capture_assets(output_root: Path, showcase_manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any] | None]]:
    captures_root = output_root / "captures"
    capture_assets: list[dict[str, Any]] = []
    by_device: dict[str, dict[str, Any] | None] = {
        preset["id"]: None for preset in showcase_manifest["device_presets"]
    }

    if not captures_root.exists():
        return capture_assets, by_device

    for path in sorted(item for item in captures_root.rglob("*") if item.is_file()):
        if path.name == "README.md":
            continue
        device_id = classify_capture_device(path.name, showcase_manifest)
        mime_type, _ = mimetypes.guess_type(path.name)
        asset = {
            "path": relative_path(path),
            "filename": path.name,
            "device_id": device_id,
            "mime_type": mime_type or "application/octet-stream",
        }
        capture_assets.append(asset)
        if device_id and by_device.get(device_id) is None:
            by_device[device_id] = asset

    fallback = capture_assets[0] if capture_assets else None
    for device_id, asset in list(by_device.items()):
        if asset is None:
            by_device[device_id] = fallback

    return capture_assets, by_device


def is_generated_source_file(path: Path) -> bool:
    return path.name not in {"README.md", "generation_manifest.json", "response.md"}


BINARY_SOURCE_SUFFIXES = {
    ".avif",
    ".gif",
    ".gz",
    ".ico",
    ".jar",
    ".jpeg",
    ".jpg",
    ".otf",
    ".pdf",
    ".png",
    ".tar",
    ".ttf",
    ".wasm",
    ".webp",
    ".woff",
    ".woff2",
    ".zip",
}

TEXTUAL_GENERATED_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".css",
    ".ex",
    ".exs",
    ".glsl",
    ".h",
    ".hpp",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".lua",
    ".mjs",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".wgsl",
    ".xml",
    ".yaml",
    ".yml",
    ".zig",
}


def scan_generated_files(output_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    generated_root = output_root / "generated"
    inventory: list[dict[str, Any]] = []
    contents: dict[str, str] = {}

    if not generated_root.exists():
        return inventory, contents

    for path in sorted(item for item in generated_root.rglob("*") if item.is_file()):
        if not is_generated_source_file(path):
            continue
        relative_generated_path = path.relative_to(generated_root).as_posix()
        raw = path.read_bytes()
        suffix = path.suffix.lower()
        if suffix in BINARY_SOURCE_SUFFIXES or (b"\x00" in raw and suffix not in TEXTUAL_GENERATED_SUFFIXES):
            inventory.append(
                {
                    "path": relative_generated_path,
                    "bytes": len(raw),
                    "line_count": None,
                    "binary": True,
                }
            )
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            inventory.append(
                {
                    "path": relative_generated_path,
                    "bytes": len(raw),
                    "line_count": None,
                    "binary": True,
                }
            )
            continue

        contents[relative_generated_path] = text
        inventory.append(
            {
                "path": relative_generated_path,
                "bytes": len(text.encode("utf-8")),
                "line_count": len(text.splitlines()),
                "binary": False,
            }
        )
    return inventory, contents


def side_variant_metadata(result: dict[str, Any]) -> tuple[str, str | None]:
    provider_execution = result.get("benchmark_report", {}).get("provider_execution", {})
    request_settings = provider_execution.get("request_settings", {})
    reasoning_effort = request_settings.get("reasoning_effort")
    if reasoning_effort:
        return f"{result['model_id']} ({reasoning_effort})", reasoning_effort
    return result["model_id"], None


def result_backing_payload(result_path: Path, showcase_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    result = load_json(result_path)
    output_root = ROOT / result["output_root"]
    capture_assets, captures_by_device = list_capture_assets(output_root, showcase_manifest)
    generated_files, file_contents = scan_generated_files(output_root)
    label, reasoning_effort = side_variant_metadata(result)
    comparison_key = result["model_id"]
    if reasoning_effort:
        comparison_key = f"{result['model_id']}[{reasoning_effort}]"

    side = {
        "kind": "result",
        "ref_id": result["result_id"],
        "ref_path": relative_path(result_path),
        "model_id": result["model_id"],
        "label": label,
        "comparison_key": comparison_key,
        "reasoning_effort": reasoning_effort,
        "status": result["status"],
        "summary": result["summary"],
        "target_id": result["benchmark_report"]["target_id"],
        "output_root": result["output_root"],
        "capture_assets": capture_assets,
        "captures_by_device": captures_by_device,
        "generated_files": generated_files,
        "benchmark_report": result["benchmark_report"],
    }
    return side, file_contents


def find_backing_result_for_run(run: dict[str, Any]) -> Path | None:
    conditions = run.get("conditions", {})
    result_id = conditions.get("execution_result_id")
    track = run.get("track")
    if result_id and track:
        candidate = execution_result_dir_for_model(track) / f"{result_id.split('--', 1)[1]}.json"
        if candidate.exists():
            return candidate

    for artifact in run.get("artifacts", []):
        artifact_path = artifact.get("path")
        if not artifact_path:
            continue
        path = ROOT / artifact_path
        if not path.exists() or path.suffix != ".json":
            continue
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        if "result_id" in payload:
            return path
    return None


def run_backing_payload(run_path: Path, showcase_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    run = load_json(run_path)
    backing_result_path = find_backing_result_for_run(run)
    if backing_result_path is not None:
        side, file_contents = result_backing_payload(backing_result_path, showcase_manifest)
        side.update(
            {
                "kind": "run",
                "ref_id": run["run_id"],
                "ref_path": relative_path(run_path),
                "label": run["track"],
                "run_title": run["title"],
                "run_status": run["status"],
                "linked_result_path": relative_path(backing_result_path),
                "metrics": run.get("metrics", {}),
                "conditions": run.get("conditions", {}),
            }
        )
        return side, file_contents

    side = {
        "kind": "run",
        "ref_id": run["run_id"],
        "ref_path": relative_path(run_path),
        "model_id": run["track"],
        "label": run["track"],
        "comparison_key": run["track"],
        "reasoning_effort": run.get("conditions", {}).get("reasoning_effort"),
        "status": run["status"],
        "summary": run["summary"],
        "target_id": run.get("conditions", {}).get("target_id"),
        "output_root": None,
        "capture_assets": [],
        "captures_by_device": {preset["id"]: None for preset in showcase_manifest["device_presets"]},
        "generated_files": [],
        "benchmark_report": {
            "target_id": run.get("conditions", {}).get("target_id"),
            "generation_kind": run.get("conditions", {}).get("generation_kind"),
            "requested_locales": run.get("conditions", {}).get("multilingual_scope"),
        },
        "run_title": run["title"],
        "run_status": run["status"],
        "metrics": run.get("metrics", {}),
        "conditions": run.get("conditions", {}),
    }
    return side, {}


def load_side(reference: str, showcase_manifest: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    path = resolve_reference_path(reference)
    payload = load_json(path)
    kind = infer_reference_kind(path, payload)
    if kind == "result":
        return result_backing_payload(path, showcase_manifest)
    return run_backing_payload(path, showcase_manifest)


def result_reasoning_effort(result: dict[str, Any]) -> str | None:
    provider_execution = result.get("benchmark_report", {}).get("provider_execution", {})
    request_settings = provider_execution.get("request_settings", {})
    return request_settings.get("reasoning_effort")


def result_recorded_at(result: dict[str, Any]) -> Any:
    provider_execution = result.get("benchmark_report", {}).get("provider_execution", {})
    for candidate in (
        provider_execution.get("captured_at"),
        result.get("review_state", {}).get("captured_at"),
        result.get("review_state", {}).get("reviewed_at"),
        result.get("review_state", {}).get("promoted_at"),
        result.get("created_at"),
    ):
        if candidate:
            return parse_timestamp(candidate)
    return parse_timestamp("1970-01-01T00:00:00Z")


def resolve_latest_result_reference(
    *,
    model_id: str,
    target_id: str,
    reasoning_effort: str | None = None,
    allow_scaffolded: bool = False,
) -> str:
    candidates: list[tuple[Any, Path]] = []
    root = execution_result_dir_for_model(model_id)
    if not root.exists():
        raise ValueError(f"No result directory exists for model {model_id}.")

    for path in sorted(root.glob("*.json")):
        result = load_json(path)
        if result.get("benchmark_report", {}).get("target_id") != target_id:
            continue
        if not allow_scaffolded and result.get("status") == "scaffolded":
            continue
        if reasoning_effort is not None and reasoning_effort != result_reasoning_effort(result):
            continue
        candidates.append((result_recorded_at(result), path))

    if not candidates:
        variant_suffix = f" with reasoning_effort={reasoning_effort}" if reasoning_effort else ""
        scaffolded_hint = " including scaffolded results" if allow_scaffolded else ""
        raise ValueError(
            f"No result found for model {model_id}, target {target_id}{variant_suffix}{scaffolded_hint}."
        )

    candidates.sort(key=lambda item: item[0])
    return relative_path(candidates[-1][1])


def code_summary(
    left_files: dict[str, str],
    right_files: dict[str, str],
    showcase_manifest: dict[str, Any],
) -> dict[str, Any]:
    config = showcase_manifest["code_preview"]
    left_paths = set(left_files)
    right_paths = set(right_files)
    shared = sorted(left_paths & right_paths)
    shared_identical = [path for path in shared if left_files[path] == right_files[path]]
    shared_changed = [path for path in shared if left_files[path] != right_files[path]]
    left_only = sorted(left_paths - right_paths)
    right_only = sorted(right_paths - left_paths)

    diff_entries: list[dict[str, Any]] = []
    for path in shared_changed[: config["max_changed_files"]]:
        diff_lines = list(
            difflib.unified_diff(
                left_files[path].splitlines(),
                right_files[path].splitlines(),
                fromfile=f"left/{path}",
                tofile=f"right/{path}",
                lineterm="",
            )
        )
        truncated = len(diff_lines) > config["max_diff_lines"]
        if truncated:
            diff_lines = diff_lines[: config["max_diff_lines"]] + ["... diff truncated ..."]
        diff_entries.append(
            {
                "path": path,
                "line_count": len(diff_lines),
                "truncated": truncated,
                "diff": "\n".join(diff_lines),
            }
        )

    return {
        "left_file_count": len(left_paths),
        "right_file_count": len(right_paths),
        "shared_identical": shared_identical,
        "shared_changed": shared_changed,
        "left_only": left_only,
        "right_only": right_only,
        "diff_entries": diff_entries,
    }


def summary_line_for_side(side: dict[str, Any]) -> str:
    parts = [
        side["label"],
        side.get("kind"),
        side.get("target_id") or "unknown-target",
        side.get("status") or "unknown-status",
    ]
    return " | ".join(str(part) for part in parts if part)


def build_comparison_markdown(comparison: dict[str, Any]) -> str:
    artifacts = "\n".join(f"- `{artifact['path']}` ({artifact['type']})" for artifact in comparison["artifacts"])
    device_presets = "\n".join(
        f"- `{preset['label']}` {preset['width']}x{preset['height']}" for preset in comparison["device_presets"]
    )
    return f"""# Showcase Comparison: {comparison['comparison_id']}

## Title
{comparison['title']}

## Summary
{comparison['summary']}

## Left
- {summary_line_for_side(comparison['left'])}

## Right
- {summary_line_for_side(comparison['right'])}

## Device Presets
{device_presets}

## Code Summary
```json
{json.dumps(comparison['code_summary'], indent=2, ensure_ascii=False)}
```

## Artifacts
{artifacts}
"""


def relative_to_site(site_root: Path, artifact_path: str | None) -> str | None:
    if not artifact_path:
        return None
    path = Path(artifact_path)
    absolute = path if path.is_absolute() else (ROOT / path)
    return absolute.relative_to(site_root).as_posix() if absolute.is_relative_to(site_root) else Path(
        os.path.relpath(absolute, start=site_root)
    ).as_posix()


def html_text(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def json_pretty(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def render_capture_panel(
    site_root: Path,
    side: dict[str, Any],
    device_preset: dict[str, Any],
) -> str:
    asset = side["captures_by_device"].get(device_preset["id"])
    if asset is None:
        return (
            '<div class="capture-empty">'
            f'<strong>No {html_text(device_preset["label"])} capture</strong>'
            f'<span>{html_text(side["label"])} has no capture artifact yet.</span>'
            "</div>"
        )

    source = relative_to_site(site_root, asset["path"])
    mime_type = asset["mime_type"]
    if mime_type.startswith("image/"):
        return (
            '<figure class="capture-figure">'
            f'<img src="{html.escape(source or "")}" alt="{html_text(side["label"])} {html_text(device_preset["label"])} capture">'
            f'<figcaption>{html_text(asset["filename"])}</figcaption>'
            "</figure>"
        )
    return (
        '<div class="capture-empty">'
        f'<strong>{html_text(asset["filename"])}</strong>'
        f'<span>Open artifact: <a href="{html.escape(source or "")}">{html_text(asset["path"])}</a></span>'
        "</div>"
    )


def render_report_card(side: dict[str, Any]) -> str:
    report = side.get("benchmark_report", {})
    rows = [
        ("Target", report.get("target_id")),
        ("Generation", report.get("generation_kind")),
        ("WebGPU", report.get("webgpu_used")),
        ("WASM", report.get("wasm_used")),
        ("Locales", ", ".join(report.get("requested_locales", [])) if isinstance(report.get("requested_locales"), list) else report.get("requested_locales")),
        ("Fallback", report.get("fallback_path")),
        ("Files", len(side.get("generated_files", []))),
        ("Captures", len(side.get("capture_assets", []))),
    ]
    row_html = "".join(
        f'<div class="report-row"><span>{html_text(label)}</span><strong>{html_text(value)}</strong></div>'
        for label, value in rows
    )
    return (
        '<section class="report-card">'
        f'<h3>{html_text(side["label"])}</h3>'
        f'<div class="report-grid">{row_html}</div>'
        '<details class="json-block"><summary>Benchmark Report JSON</summary>'
        f'<pre>{html_text(json_pretty(report))}</pre>'
        '</details>'
        '</section>'
    )


def render_code_list(title: str, items: list[str], empty_text: str) -> str:
    if not items:
        return (
            '<section class="code-list">'
            f'<h3>{html_text(title)}</h3>'
            f'<p class="muted">{html_text(empty_text)}</p>'
            '</section>'
        )
    body = "".join(f"<li><code>{html_text(item)}</code></li>" for item in items)
    return (
        '<section class="code-list">'
        f'<h3>{html_text(title)}</h3>'
        f'<ul>{body}</ul>'
        '</section>'
    )


def render_diff_entries(diff_entries: list[dict[str, Any]]) -> str:
    if not diff_entries:
        return '<p class="muted">No changed common files yet.</p>'
    chunks = []
    for entry in diff_entries:
        chunks.append(
            '<details class="diff-entry" open>'
            f'<summary><code>{html_text(entry["path"])}</code></summary>'
            f'<pre class="diff-block">{html_text(entry["diff"])}</pre>'
            '</details>'
        )
    return "".join(chunks)


def render_site_html(comparison: dict[str, Any]) -> str:
    site_root = ROOT / comparison["site_root"]
    device_buttons = "".join(
        f'<button type="button" class="device-button{" is-active" if index == 0 else ""}" '
        f'data-device-select="{html_text(preset["id"])}">{html_text(preset["label"])}</button>'
        for index, preset in enumerate(comparison["device_presets"])
    )

    device_sections = []
    for index, preset in enumerate(comparison["device_presets"]):
        device_sections.append(
            '<section class="device-stage{active}" data-device-stage="{device}">'.format(
                active=" is-active" if index == 0 else "",
                device=html_text(preset["id"]),
            )
            + '<div class="device-meta">'
            + f'<h2>{html_text(preset["label"])}</h2>'
            + f'<p>{html_text(preset["width"])} x {html_text(preset["height"])} · {html_text(preset["notes"])}</p>'
            + '</div>'
            + '<div class="visual-grid">'
            + f'<article class="visual-card"><header><h3>{html_text(comparison["left"]["label"])}</h3></header>{render_capture_panel(site_root, comparison["left"], preset)}</article>'
            + f'<article class="visual-card"><header><h3>{html_text(comparison["right"]["label"])}</h3></header>{render_capture_panel(site_root, comparison["right"], preset)}</article>'
            + '</div>'
            + '</section>'
        )

    summary_cards = "".join(
        [
            f'<article class="summary-card"><span>Target</span><strong>{html_text(comparison["target_id"])}</strong></article>',
            f'<article class="summary-card"><span>Left</span><strong>{html_text(comparison["left"]["model_id"])}</strong></article>',
            f'<article class="summary-card"><span>Right</span><strong>{html_text(comparison["right"]["model_id"])}</strong></article>',
            f'<article class="summary-card"><span>Changed Files</span><strong>{html_text(len(comparison["code_summary"]["shared_changed"]))}</strong></article>',
        ]
    )

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html_text(comparison["title"])}</title>
    <link rel="stylesheet" href="styles.css">
  </head>
  <body>
    <main class="page-shell">
      <section class="hero">
        <p class="eyebrow">Tesseract Benchmark Showcase</p>
        <h1>{html_text(comparison["title"])}</h1>
        <p class="lede">{html_text(comparison["summary"])}</p>
        <div class="summary-grid">{summary_cards}</div>
      </section>

      <section class="device-switcher">
        <div class="device-toolbar">{device_buttons}</div>
        {"".join(device_sections)}
      </section>

      <section class="report-section">
        <div class="section-heading">
          <p class="eyebrow">Benchmark Reports</p>
          <h2>Side-by-side contract snapshot</h2>
        </div>
        <div class="report-columns">
          {render_report_card(comparison["left"])}
          {render_report_card(comparison["right"])}
        </div>
      </section>

      <section class="code-section">
        <div class="section-heading">
          <p class="eyebrow">Generated Code</p>
          <h2>Common changes and unique files</h2>
        </div>
        <div class="code-columns">
          {render_code_list("Left Only", comparison["code_summary"]["left_only"], "No left-only generated files.")}
          {render_code_list("Right Only", comparison["code_summary"]["right_only"], "No right-only generated files.")}
        </div>
        <section class="diff-section">
          <h3>Changed Common Files</h3>
          {render_diff_entries(comparison["code_summary"]["diff_entries"])}
        </section>
      </section>

      <section class="footnote">
        <details>
          <summary>Canonical Comparison JSON</summary>
          <pre>{html_text(json_pretty(comparison))}</pre>
        </details>
      </section>
    </main>
    <script src="app.js"></script>
  </body>
</html>
"""


def render_site_css() -> str:
    return """* {
  box-sizing: border-box;
}

:root {
  --bg: #f4efe6;
  --bg-strong: #eadfcf;
  --panel: rgba(255, 255, 255, 0.86);
  --panel-strong: #fffaf2;
  --ink: #172033;
  --muted: #5e6472;
  --accent: #d45f3a;
  --accent-soft: rgba(212, 95, 58, 0.16);
  --border: rgba(23, 32, 51, 0.12);
  --shadow: 0 24px 60px rgba(23, 32, 51, 0.12);
  --radius: 24px;
  --mono: "IBM Plex Mono", "SFMono-Regular", "Menlo", monospace;
  --sans: "Space Grotesk", "Avenir Next", "Segoe UI", sans-serif;
}

body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(212, 95, 58, 0.18), transparent 32%),
    radial-gradient(circle at right center, rgba(21, 104, 168, 0.14), transparent 24%),
    linear-gradient(180deg, #faf5ed 0%, var(--bg) 44%, #ebe4d9 100%);
  font-family: var(--sans);
}

.page-shell {
  width: min(1440px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 32px 0 64px;
}

.hero,
.device-switcher,
.report-section,
.code-section,
.footnote {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  backdrop-filter: blur(18px);
  padding: 24px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  margin: 0;
}

.lede,
.muted,
.device-meta p,
.capture-empty span,
.report-row span,
.footnote summary {
  color: var(--muted);
}

.summary-grid,
.report-columns,
.code-columns,
.visual-grid {
  display: grid;
  gap: 16px;
}

.summary-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 20px;
}

.summary-card,
.visual-card,
.report-card,
.code-list,
.diff-section {
  background: var(--panel-strong);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
}

.summary-card span,
.report-row span {
  display: block;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-card strong {
  display: block;
  margin-top: 10px;
  font-size: 1.15rem;
}

.device-toolbar {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 8px;
  background: rgba(23, 32, 51, 0.04);
  border-radius: 999px;
}

.device-button {
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
  font: inherit;
  font-weight: 700;
  padding: 10px 16px;
}

.device-button.is-active {
  background: var(--ink);
  color: white;
}

.device-stage {
  display: none;
  margin-top: 22px;
}

.device-stage.is-active {
  display: block;
}

.device-meta {
  margin-bottom: 16px;
}

.visual-grid,
.report-columns {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.visual-card header,
.report-card h3,
.code-list h3,
.diff-section h3 {
  margin-bottom: 12px;
}

.capture-figure {
  margin: 0;
}

.capture-figure img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 16px;
  border: 1px solid var(--border);
  background: linear-gradient(145deg, rgba(23, 32, 51, 0.04), rgba(23, 32, 51, 0.1));
}

.capture-figure figcaption {
  margin-top: 10px;
  color: var(--muted);
  font-size: 0.86rem;
}

.capture-empty {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;
  border: 1px dashed rgba(23, 32, 51, 0.2);
  border-radius: 16px;
  padding: 18px;
  background: linear-gradient(135deg, rgba(212, 95, 58, 0.08), rgba(21, 104, 168, 0.04));
}

.report-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.report-row strong {
  display: block;
  margin-top: 4px;
  word-break: break-word;
}

.json-block,
.diff-entry,
.footnote details {
  margin-top: 16px;
}

pre,
code {
  font-family: var(--mono);
}

pre {
  margin: 0;
  overflow-x: auto;
  background: #111826;
  color: #eef3ff;
  border-radius: 16px;
  padding: 16px;
  font-size: 0.82rem;
}

ul {
  margin: 0;
  padding-left: 18px;
}

.section-heading {
  margin-bottom: 16px;
}

@media (max-width: 1080px) {
  .summary-grid,
  .report-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 860px) {
  .visual-grid,
  .report-columns,
  .code-columns,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-shell {
    width: min(100vw - 20px, 100%);
    padding-top: 16px;
  }

  .hero,
  .device-switcher,
  .report-section,
  .code-section,
  .footnote {
    padding: 18px;
    border-radius: 20px;
  }
}
"""


def render_site_js() -> str:
    return """const buttons = Array.from(document.querySelectorAll('[data-device-select]'));
const stages = Array.from(document.querySelectorAll('[data-device-stage]'));

function activateDevice(deviceId) {
  buttons.forEach((button) => {
    button.classList.toggle('is-active', button.dataset.deviceSelect === deviceId);
  });
  stages.forEach((stage) => {
    stage.classList.toggle('is-active', stage.dataset.deviceStage === deviceId);
  });
}

buttons.forEach((button) => {
  button.addEventListener('click', () => activateDevice(button.dataset.deviceSelect));
});
"""


def load_comparison_inventory() -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in sorted(showcase_comparison_dir().glob("*.json")):
        comparison = load_json(path)
        inventory.append(
            {
                "comparison_id": comparison["comparison_id"],
                "created_at": comparison["created_at"],
                "title": comparison["title"],
                "summary": comparison["summary"],
                "status": comparison["status"],
                "target_id": comparison["target_id"],
                "pair_key": comparison["pair_key"],
                "left_model_id": comparison["left"]["model_id"],
                "right_model_id": comparison["right"]["model_id"],
                "site_root": comparison["site_root"],
                "site_href": f"{Path(comparison['site_root']).name}/index.html",
                "path": relative_path(path),
            }
        )
    inventory.sort(key=lambda item: (item["created_at"], item["pair_key"], item["path"]), reverse=True)
    return inventory


def showcase_index_payload() -> dict[str, Any]:
    comparisons = load_comparison_inventory()
    return {
        "source_snapshot_at": comparisons[0]["created_at"] if comparisons else None,
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
    }


def render_index_html(payload: dict[str, Any]) -> str:
    cards = []
    for comparison in payload["comparisons"]:
        cards.append(
            '<article class="index-card">'
            f'<p class="eyebrow">{html_text(comparison["status"])}</p>'
            f'<h2><a href="{html.escape(comparison["site_href"])}">{html_text(comparison["title"])}</a></h2>'
            f'<p class="muted">{html_text(comparison["summary"])}</p>'
            '<div class="summary-grid">'
            f'<article class="summary-card"><span>Pair</span><strong>{html_text(comparison["left_model_id"])} vs {html_text(comparison["right_model_id"])}</strong></article>'
            f'<article class="summary-card"><span>Target</span><strong>{html_text(comparison["target_id"])}</strong></article>'
            f'<article class="summary-card"><span>Created</span><strong>{html_text(comparison["created_at"])}</strong></article>'
            '</div>'
            '</article>'
        )

    empty_state = (
        '<section class="hero">'
        '<p class="eyebrow">Tesseract Benchmark Showcase</p>'
        '<h1>No comparisons yet</h1>'
        '<p class="lede">Create a comparison with benchmark_showcase.py create-comparison to populate this index.</p>'
        '</section>'
    )
    body = "".join(cards) if cards else empty_state
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Tesseract Benchmark Showcase</title>
    <link rel="stylesheet" href="index.css">
  </head>
  <body>
    <main class="page-shell">
      <section class="hero">
        <p class="eyebrow">Tesseract Benchmark Showcase</p>
        <h1>Responsive Comparison Index</h1>
        <p class="lede">Browse the latest side-by-side comparison surfaces for visual evidence, generated code, and benchmark metadata.</p>
      </section>
      <section class="report-section">
        <div class="section-heading">
          <p class="eyebrow">Comparisons</p>
          <h2>{html_text(payload["comparison_count"])} generated site(s)</h2>
        </div>
        <div class="index-grid">
          {body}
        </div>
      </section>
      <section class="footnote">
        <details>
          <summary>Index JSON</summary>
          <pre>{html_text(json_pretty(payload))}</pre>
        </details>
      </section>
    </main>
  </body>
</html>
"""


def render_index_css() -> str:
    return render_site_css() + """

.index-grid {
  display: grid;
  gap: 16px;
}

.index-card {
  background: var(--panel-strong);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 20px;
}

.index-card h2 {
  margin-bottom: 10px;
}

.index-card a {
  color: inherit;
  text-decoration: none;
}

.index-card a:hover {
  color: var(--accent);
}
"""


def write_showcase_index() -> None:
    paths = showcase_index_paths()
    payload = showcase_index_payload()
    write_text_if_changed(paths["html"], render_index_html(payload))
    write_text_if_changed(paths["root"] / "index.css", render_index_css())
    write_json_if_changed(paths["data"], payload)


def validate_showcase_index() -> list[str]:
    errors: list[str] = []
    paths = showcase_index_paths()
    payload = showcase_index_payload()
    expected = {
        "html": render_index_html(payload),
        "css": render_index_css(),
        "data": json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    }
    actual_paths = {
        "html": paths["html"],
        "css": paths["root"] / "index.css",
        "data": paths["data"],
    }
    for key, path in actual_paths.items():
        if not path.exists():
            errors.append(f"missing showcase index artifact {relative_path(path)}")
            continue
        if path.read_text(encoding="utf-8") != expected[key]:
            errors.append(f"stale showcase index artifact {relative_path(path)}")
    return errors


def site_payload(comparison: dict[str, Any]) -> dict[str, Any]:
    return {
        "comparison_id": comparison["comparison_id"],
        "title": comparison["title"],
        "summary": comparison["summary"],
        "target_id": comparison["target_id"],
        "left": comparison["left"],
        "right": comparison["right"],
        "device_presets": comparison["device_presets"],
        "code_summary": comparison["code_summary"],
        "notes": comparison.get("notes", []),
    }


def write_site_files(comparison: dict[str, Any]) -> None:
    paths = site_paths_for(comparison["comparison_id"])
    write_text_if_changed(paths["html"], render_site_html(comparison))
    write_text_if_changed(paths["css"], render_site_css())
    write_text_if_changed(paths["js"], render_site_js())
    write_json_if_changed(paths["data"], site_payload(comparison))


def comparison_artifacts(comparison_id: str) -> list[dict[str, str]]:
    json_path = comparison_path_for(comparison_id, "json")
    md_path = comparison_path_for(comparison_id, "md")
    site_paths = site_paths_for(comparison_id)
    return [
        {"path": relative_path(json_path), "type": "comparison-record"},
        {"path": relative_path(md_path), "type": "comparison-record-doc"},
        {"path": relative_path(site_paths["html"]), "type": "comparison-site-html"},
        {"path": relative_path(site_paths["css"]), "type": "comparison-site-css"},
        {"path": relative_path(site_paths["js"]), "type": "comparison-site-js"},
        {"path": relative_path(site_paths["data"]), "type": "comparison-site-data"},
    ]


def build_comparison(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    showcase_manifest = load_showcase_manifest()

    left, left_contents = load_side(args.left, showcase_manifest)
    right, right_contents = load_side(args.right, showcase_manifest)

    recorded_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    left_target_id = left.get("target_id")
    right_target_id = right.get("target_id")
    if left_target_id and right_target_id and left_target_id != right_target_id:
        raise ValueError(
            "Comparison sides must target the same benchmark lane: "
            f"{left_target_id} != {right_target_id}"
        )

    timestamp = recorded_at.strftime("%Y%m%dT%H%M%SZ")
    target_id = left_target_id or right_target_id or "unknown-target"
    slug = slugify(args.slug or f"{left['model_id']}-vs-{right['model_id']}-{target_id}")
    comparison_id = f"comparison--{timestamp}--{slug}"
    site_root = relative_path(site_root_for(comparison_id))
    status = args.status or showcase_manifest["default_status"]
    if status not in showcase_manifest["status_values"]:
        raise ValueError(f"Unsupported showcase status: {status}")

    comparison = {
        "comparison_id": comparison_id,
        "created_at": recorded_at.isoformat().replace("+00:00", "Z"),
        "benchmark_id": benchmark_manifest["benchmark_id"],
        "title": args.title or f"{left['model_id']} vs {right['model_id']} · {target_id}",
        "status": status,
        "summary": args.summary or (
            f"Responsive side-by-side showcase comparing {left['model_id']} and {right['model_id']} "
            f"for target {target_id}."
        ),
        "target_id": target_id,
        "pair_key": f"{left.get('comparison_key', left['model_id'])}__vs__{right.get('comparison_key', right['model_id'])}__{target_id}",
        "left": left,
        "right": right,
        "site_root": site_root,
        "device_presets": showcase_manifest["device_presets"],
        "code_summary": code_summary(left_contents, right_contents, showcase_manifest),
        "notes": unique_strings(
            [
                *args.note,
                "Comparison records are canonical; showcase site files are derived artifacts.",
            ]
        ),
        "artifacts": comparison_artifacts(comparison_id),
    }
    return comparison


def validate_comparison(
    path: Path,
    showcase_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    comparison = load_json(path)
    missing = sorted(set(showcase_manifest["comparison_required_fields"]) - set(comparison))
    if missing:
        errors.append(f"{relative_path(path)}: missing keys {', '.join(missing)}")
        return errors

    if comparison["benchmark_id"] != benchmark_manifest["benchmark_id"]:
        errors.append(f"{relative_path(path)}: benchmark_id mismatch")
    if comparison["status"] not in showcase_manifest["status_values"]:
        errors.append(f"{relative_path(path)}: unsupported status {comparison['status']}")
    if comparison["device_presets"] != showcase_manifest["device_presets"]:
        errors.append(f"{relative_path(path)}: device presets differ from showcase manifest")
    if not (ROOT / comparison["site_root"]).exists():
        errors.append(f"{relative_path(path)}: missing site root {comparison['site_root']}")

    for side_name in ("left", "right"):
        side = comparison[side_name]
        if not (ROOT / side["ref_path"]).exists():
            errors.append(f"{relative_path(path)}: missing {side_name} reference {side['ref_path']}")
        output_root = side.get("output_root")
        if output_root and not (ROOT / output_root).exists():
            errors.append(f"{relative_path(path)}: missing {side_name} output root {output_root}")
        side_target_id = side.get("target_id")
        if side_target_id and side_target_id != comparison["target_id"]:
            errors.append(
                f"{relative_path(path)}: {side_name} target_id {side_target_id} "
                f"does not match comparison target_id {comparison['target_id']}"
            )

    markdown_path = path.with_suffix(".md")
    if not markdown_path.exists():
        errors.append(f"{relative_path(path)}: missing markdown pair {relative_path(markdown_path)}")

    for artifact in comparison["artifacts"]:
        artifact_path = artifact["path"]
        if not (ROOT / artifact_path).exists():
            errors.append(f"{relative_path(path)}: missing artifact {artifact_path}")
    return errors


def write_comparison_files(comparison: dict[str, Any]) -> None:
    json_path = comparison_path_for(comparison["comparison_id"], "json")
    md_path = comparison_path_for(comparison["comparison_id"], "md")
    write_json_if_changed(json_path, comparison)
    write_text_if_changed(md_path, build_comparison_markdown(comparison))
    write_site_files(comparison)
    write_showcase_index()


def load_comparison(reference: str) -> tuple[Path, dict[str, Any]]:
    path = resolve_reference_path(reference)
    return path, load_json(path)


def cmd_create_comparison(args: argparse.Namespace) -> int:
    comparison = build_comparison(args)
    json_path = comparison_path_for(comparison["comparison_id"], "json")
    md_path = comparison_path_for(comparison["comparison_id"], "md")
    if json_path.exists() or md_path.exists():
        print(f"Comparison already exists: {relative_path(json_path)}")
        return 1
    if args.dry_run:
        print(json.dumps(comparison, indent=2, ensure_ascii=False))
        return 0
    write_comparison_files(comparison)
    print(relative_path(json_path))
    print(relative_path(site_paths_for(comparison["comparison_id"])["html"]))
    return 0


def cmd_create_latest_comparison(args: argparse.Namespace) -> int:
    try:
        left = resolve_latest_result_reference(
            model_id=args.left_model,
            target_id=args.target_id,
            reasoning_effort=args.left_reasoning_effort,
            allow_scaffolded=args.allow_scaffolded,
        )
        right = resolve_latest_result_reference(
            model_id=args.right_model,
            target_id=args.target_id,
            reasoning_effort=args.right_reasoning_effort,
            allow_scaffolded=args.allow_scaffolded,
        )
    except ValueError as exc:
        print(str(exc))
        return 1

    delegated_args = argparse.Namespace(
        left=left,
        right=right,
        title=args.title,
        summary=args.summary,
        slug=args.slug,
        status=args.status,
        recorded_at=args.recorded_at,
        note=args.note,
        dry_run=args.dry_run,
    )
    return cmd_create_comparison(delegated_args)


def cmd_build_site(args: argparse.Namespace) -> int:
    comparison_path, comparison = load_comparison(args.comparison)
    if args.dry_run:
        print(render_site_html(comparison))
        return 0
    write_comparison_files(comparison)
    print(relative_path(comparison_path))
    print(relative_path(site_paths_for(comparison["comparison_id"])["html"]))
    return 0


def cmd_build_index(_: argparse.Namespace) -> int:
    write_showcase_index()
    print(relative_path(showcase_index_paths()["html"]))
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    showcase_manifest = load_showcase_manifest()
    benchmark_manifest = load_benchmark_manifest()
    errors: list[str] = []
    count = 0
    for path in sorted(showcase_comparison_dir().glob("*.json")):
        count += 1
        errors.extend(validate_comparison(path, showcase_manifest, benchmark_manifest))
    if count:
        errors.extend(validate_showcase_index())
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {count} showcase comparison(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesseract benchmark showcase CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-comparison", help="Create a responsive comparison from two results or runs")
    create.add_argument("--left", required=True, help="Left result/run JSON path")
    create.add_argument("--right", required=True, help="Right result/run JSON path")
    create.add_argument("--title", help="Optional comparison title")
    create.add_argument("--summary", help="Optional comparison summary")
    create.add_argument("--slug", help="Optional slug override")
    create.add_argument("--status", help="Optional status override")
    create.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create.add_argument("--note", action="append", default=[], help="Additional note to append")
    create.add_argument("--dry-run", action="store_true", help="Print JSON without writing files")
    create.set_defaults(func=cmd_create_comparison)

    create_latest = subparsers.add_parser(
        "create-latest-comparison",
        help="Create a comparison from the latest results for two model/variant selectors",
    )
    create_latest.add_argument("--left-model", required=True, help="Left model id")
    create_latest.add_argument("--right-model", required=True, help="Right model id")
    create_latest.add_argument("--target-id", required=True, help="Shared benchmark target id")
    create_latest.add_argument("--left-reasoning-effort", help="Optional left reasoning effort filter")
    create_latest.add_argument("--right-reasoning-effort", help="Optional right reasoning effort filter")
    create_latest.add_argument("--allow-scaffolded", action="store_true", help="Allow scaffolded results when resolving latest references")
    create_latest.add_argument("--title", help="Optional comparison title")
    create_latest.add_argument("--summary", help="Optional comparison summary")
    create_latest.add_argument("--slug", help="Optional slug override")
    create_latest.add_argument("--status", help="Optional status override")
    create_latest.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create_latest.add_argument("--note", action="append", default=[], help="Additional note to append")
    create_latest.add_argument("--dry-run", action="store_true", help="Print JSON without writing files")
    create_latest.set_defaults(func=cmd_create_latest_comparison)

    build = subparsers.add_parser("build-site", help="Rebuild a showcase site from a comparison record")
    build.add_argument("--comparison", required=True, help="Comparison JSON path")
    build.add_argument("--dry-run", action="store_true", help="Print HTML instead of writing files")
    build.set_defaults(func=cmd_build_site)

    build_index = subparsers.add_parser("build-index", help="Build the showcase index from all comparisons")
    build_index.set_defaults(func=cmd_build_index)

    validate = subparsers.add_parser("validate", help="Validate showcase comparisons")
    validate.set_defaults(func=cmd_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
