from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from benchmark_core import (
    ROOT,
    index_by_id,
    load_benchmark_manifest,
    load_generation_manifest,
    load_model_registry,
    model_ids,
    now_utc,
    packet_dir_for_model,
    parse_pairs,
    parse_timestamp,
    relative_path,
    slugify,
    track_ids,
    unique_strings,
)


def render_template(template: str, context: dict[str, str]) -> str:
    pattern = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in context:
            raise ValueError(f"Missing template key: {key}")
        return context[key]

    return pattern.sub(replace, template)


def load_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8").rstrip() + "\n"


def template_path_for(recipe: dict[str, Any], kind: str) -> Path:
    recipe_dir = ROOT / recipe["directory"]
    recipe_meta_path = recipe_dir / "recipe.json"
    recipe_meta = json.loads(recipe_meta_path.read_text(encoding="utf-8"))
    filename = recipe_meta["template_files"][kind]
    return recipe_dir / filename


def resolve_recipe_variables(recipe: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    defaults = {variable["id"]: variable["default"] for variable in recipe["variables"]}
    unknown = sorted(set(overrides) - set(defaults))
    if unknown:
        raise ValueError(f"Unknown recipe variables: {', '.join(unknown)}")
    defaults.update(overrides)
    return defaults


def validate_selected_capabilities(target: dict[str, Any], capabilities: list[str]) -> None:
    allowed = set(target["default_capabilities"]) | set(target["optional_capabilities"])
    invalid = [capability for capability in capabilities if capability not in allowed]
    if invalid:
        raise ValueError(
            f"Unsupported capabilities for {target['id']}: {', '.join(sorted(invalid))}"
        )


def build_context(
    scene: dict[str, Any],
    target: dict[str, Any],
    recipe: dict[str, Any],
    variables: dict[str, Any],
    locales: list[str],
    capabilities: list[str],
) -> dict[str, str]:
    context: dict[str, str] = {
        "scene_id": scene["id"],
        "scene_title": scene["title"],
        "scene_short_name": scene["short_name"],
        "target_id": target["id"],
        "target_label": target["label"],
        "target_language": target["language"],
        "target_runtime": target["runtime"],
        "target_lane": target["lane"],
        "selected_locales_csv": ", ".join(locales),
        "selected_capabilities_csv": ", ".join(capabilities),
        "recipe_label": recipe["label"],
    }
    for key, value in variables.items():
        context[key] = str(value)
    return context


def packet_path_for(model_id: str, packet_id: str, suffix: str) -> Path:
    serial = packet_id.split("--", 1)[1]
    return packet_dir_for_model(model_id) / f"{serial}.{suffix}"


def build_markdown_packet(packet: dict[str, Any]) -> str:
    checkpoint_lines = "\n".join(
        f"- `{checkpoint['id']}`: {checkpoint['description']}"
        for checkpoint in packet["checkpoints"]
    )
    required_sections = "\n".join(
        f"- `{section}`" for section in packet["delivery_contract"]["required_sections"]
    )
    report_fields = "\n".join(
        f"- `{field}`" for field in packet["delivery_contract"]["benchmark_report_fields"]
    )

    return f"""# Prompt Packet: {packet['packet_id']}

## Metadata
- Model: `{packet['model_id']}`
- Recipe: `{packet['recipe_id']}`
- Scene: `{packet['scene_id']}`
- Kind: `{packet['generation_kind']}`
- Target: `{packet['target']['id']}`
- Lane: `{packet['target']['lane']}`
- Created At: `{packet['created_at']}`
- Locales: `{', '.join(packet['selected_locales'])}`
- Capabilities: `{', '.join(packet['selected_capabilities'])}`

## System Prompt
Source: `{packet['messages']['system_prompt_path']}`

```md
{packet['messages']['system_prompt'].rstrip()}
```

## Scene Brief
Source: `{packet['messages']['scene_prompt_path']}`

```md
{packet['messages']['scene_prompt'].rstrip()}
```

## Compiled User Prompt
Source: `{packet['messages']['recipe_template_path']}`

```md
{packet['messages']['user_prompt'].rstrip()}
```

## Checkpoints
{checkpoint_lines}

## Delivery Contract
- Response format: {packet['delivery_contract']['response_format']}
- Required sections:
{required_sections}
- Benchmark report fields:
{report_fields}
"""


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    generation_manifest = load_generation_manifest()
    model_registry = load_model_registry()

    target_map = index_by_id(generation_manifest["targets"])
    recipe_map = index_by_id(generation_manifest["recipes"])
    scene_map = index_by_id(generation_manifest["scenes"])
    kind_map = index_by_id(generation_manifest["generation_kinds"])
    registry_ids = set(model_ids(model_registry))

    recipe = recipe_map[args.recipe or generation_manifest["default_recipe_id"]]
    kind = args.kind or recipe["default_kind"]
    target = target_map[args.target or recipe["default_target"]]
    scene = scene_map[recipe["scene_id"]]
    model_id = args.model or args.track or recipe["default_track"]

    if model_id not in track_ids(benchmark_manifest):
        raise ValueError(f"Unknown benchmark track: {model_id}")
    if model_id not in registry_ids:
        raise ValueError(f"Model id missing from models/registry.json: {model_id}")
    if kind not in kind_map:
        raise ValueError(f"Unknown generation kind: {kind}")
    if kind not in recipe["allowed_kinds"]:
        raise ValueError(f"Recipe {recipe['id']} does not support kind {kind}")
    if kind_map[kind]["status"] != "active":
        raise ValueError(f"Generation kind {kind} is not active yet")

    variable_overrides = parse_pairs(args.var)
    recipe_variables = resolve_recipe_variables(recipe, variable_overrides)

    locales = unique_strings(args.locale or recipe["default_locales"])
    capabilities = unique_strings(target["default_capabilities"] + (args.capability or []))
    validate_selected_capabilities(target, capabilities)

    template_path = template_path_for(recipe, kind)
    template_text = template_path.read_text(encoding="utf-8")
    context = build_context(scene, target, recipe, recipe_variables, locales, capabilities)
    user_prompt = render_template(template_text, context)

    created_at = parse_timestamp(args.recorded_at) if args.recorded_at else now_utc()
    timestamp = created_at.strftime("%Y%m%dT%H%M%SZ")
    default_slug = f"{recipe['id']}-{kind}-{target['id']}"
    packet_slug = args.slug or slugify(default_slug)
    packet_id = f"{model_id}--{timestamp}--{packet_slug}"

    system_prompt_path = generation_manifest["system_prompt_path"]
    scene_prompt_path = scene["path"]

    packet = {
        "packet_id": packet_id,
        "created_at": created_at.isoformat().replace("+00:00", "Z"),
        "benchmark_id": benchmark_manifest["benchmark_id"],
        "model_id": model_id,
        "recipe_id": recipe["id"],
        "scene_id": scene["id"],
        "generation_kind": kind,
        "generation_kind_status": kind_map[kind]["status"],
        "target": target,
        "selected_capabilities": capabilities,
        "selected_locales": locales,
        "variables": recipe_variables,
        "checkpoints": recipe["checkpoints"],
        "delivery_contract": recipe["delivery_contract"],
        "orchestration_strategy": generation_manifest["orchestration_strategy"],
        "messages": {
            "system_prompt_path": system_prompt_path,
            "scene_prompt_path": scene_prompt_path,
            "recipe_template_path": relative_path(template_path),
            "system_prompt": load_text(system_prompt_path),
            "scene_prompt": load_text(scene_prompt_path),
            "user_prompt": user_prompt.rstrip() + "\n",
        },
    }
    return packet


def validate_manifest_files(
    generation_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    model_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    if not (ROOT / generation_manifest["system_prompt_path"]).exists():
        errors.append(
            f"Missing system prompt: {generation_manifest['system_prompt_path']}"
        )

    kind_map = index_by_id(generation_manifest["generation_kinds"])
    target_map = index_by_id(generation_manifest["targets"])
    scene_map = index_by_id(generation_manifest["scenes"])
    valid_tracks = set(track_ids(benchmark_manifest))
    valid_models = set(model_ids(model_registry))

    if valid_tracks != valid_models:
        errors.append(
            "benchmark_manifest.json tracks and models/registry.json ids must match exactly"
        )

    if len(kind_map) != len(generation_manifest["generation_kinds"]):
        errors.append("Generation kinds must have unique ids")
    if len(target_map) != len(generation_manifest["targets"]):
        errors.append("Targets must have unique ids")
    if len(scene_map) != len(generation_manifest["scenes"]):
        errors.append("Scenes must have unique ids")

    lane_ids = {lane["id"] for lane in generation_manifest["lanes"]}
    for target in generation_manifest["targets"]:
        if target["lane"] not in lane_ids:
            errors.append(f"Target {target['id']} uses unknown lane {target['lane']}")
        invalid_overlap = set(target["default_capabilities"]) & set(
            target["optional_capabilities"]
        )
        if invalid_overlap:
            overlap = ", ".join(sorted(invalid_overlap))
            errors.append(f"Target {target['id']} overlaps default/optional capabilities: {overlap}")

    for scene in generation_manifest["scenes"]:
        if not (ROOT / scene["path"]).exists():
            errors.append(f"Missing scene prompt: {scene['path']}")

    for recipe in generation_manifest["recipes"]:
        if recipe["scene_id"] not in scene_map:
            errors.append(f"Recipe {recipe['id']} references unknown scene {recipe['scene_id']}")
        if recipe["default_kind"] not in kind_map:
            errors.append(f"Recipe {recipe['id']} references unknown default kind {recipe['default_kind']}")
        if recipe["default_target"] not in target_map:
            errors.append(
                f"Recipe {recipe['id']} references unknown default target {recipe['default_target']}"
            )
        if recipe["default_track"] not in valid_tracks:
            errors.append(
                f"Recipe {recipe['id']} references unknown default model/track {recipe['default_track']}"
            )
        for kind in recipe["allowed_kinds"]:
            if kind not in kind_map:
                errors.append(f"Recipe {recipe['id']} allows unknown kind {kind}")

        recipe_dir = ROOT / recipe["directory"]
        recipe_meta_path = recipe_dir / "recipe.json"
        if not recipe_meta_path.exists():
            errors.append(f"Recipe metadata missing: {relative_path(recipe_meta_path)}")
            continue

        recipe_meta = json.loads(recipe_meta_path.read_text(encoding="utf-8"))
        for kind in recipe["allowed_kinds"]:
            if kind not in recipe_meta["template_files"]:
                errors.append(f"Recipe {recipe['id']} missing template mapping for {kind}")
                continue
            template_path = recipe_dir / recipe_meta["template_files"][kind]
            if not template_path.exists():
                errors.append(f"Missing recipe template: {relative_path(template_path)}")

    return errors


def validate_packet(
    packet_path: Path,
    generation_manifest: dict[str, Any],
    benchmark_manifest: dict[str, Any],
    model_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    required_keys = {
        "packet_id",
        "created_at",
        "benchmark_id",
        "model_id",
        "recipe_id",
        "scene_id",
        "generation_kind",
        "target",
        "selected_capabilities",
        "selected_locales",
        "variables",
        "checkpoints",
        "delivery_contract",
        "messages",
    }
    missing = sorted(required_keys - set(packet))
    if missing:
        errors.append(f"{relative_path(packet_path)}: missing keys {', '.join(missing)}")
        return errors

    if packet["benchmark_id"] != benchmark_manifest["benchmark_id"]:
        errors.append(
            f"{relative_path(packet_path)}: benchmark_id must be {benchmark_manifest['benchmark_id']}"
        )

    if packet["model_id"] not in track_ids(benchmark_manifest):
        errors.append(f"{relative_path(packet_path)}: unknown model/track {packet['model_id']}")
    if packet["model_id"] not in model_ids(model_registry):
        errors.append(f"{relative_path(packet_path)}: missing model registry entry {packet['model_id']}")

    kind_map = index_by_id(generation_manifest["generation_kinds"])
    target_map = index_by_id(generation_manifest["targets"])
    recipe_map = index_by_id(generation_manifest["recipes"])
    scene_map = index_by_id(generation_manifest["scenes"])

    if packet["generation_kind"] not in kind_map:
        errors.append(
            f"{relative_path(packet_path)}: unknown generation kind {packet['generation_kind']}"
        )
    if packet["target"]["id"] not in target_map:
        errors.append(f"{relative_path(packet_path)}: unknown target {packet['target']['id']}")
    if packet["recipe_id"] not in recipe_map:
        errors.append(f"{relative_path(packet_path)}: unknown recipe {packet['recipe_id']}")
    if packet["scene_id"] not in scene_map:
        errors.append(f"{relative_path(packet_path)}: unknown scene {packet['scene_id']}")

    markdown_pair = packet_path.with_suffix(".md")
    if not markdown_pair.exists():
        errors.append(f"{relative_path(packet_path)}: missing markdown pair {relative_path(markdown_pair)}")

    return errors


def cmd_list_kinds(_: argparse.Namespace) -> int:
    manifest = load_generation_manifest()
    for kind in sorted(manifest["generation_kinds"], key=lambda item: item["complexity_rank"]):
        print(
            f"{kind['id']}\t{kind['status']}\t{kind['complexity_rank']}\t{kind['description']}"
        )
    return 0


def cmd_list_targets(_: argparse.Namespace) -> int:
    manifest = load_generation_manifest()
    for target in manifest["targets"]:
        capabilities = ",".join(target["default_capabilities"])
        print(
            f"{target['id']}\t{target['lane']}\t{target['language']}\t{target['runtime']}\t{capabilities}"
        )
    return 0


def cmd_list_recipes(_: argparse.Namespace) -> int:
    manifest = load_generation_manifest()
    for recipe in manifest["recipes"]:
        kinds = ",".join(recipe["allowed_kinds"])
        print(
            f"{recipe['id']}\t{recipe['default_track']}\t{recipe['default_target']}\t{kinds}\t{recipe['description']}"
        )
    return 0


def cmd_list_models(_: argparse.Namespace) -> int:
    registry = load_model_registry()
    for model in registry["models"]:
        print(
            f"{model['id']}\t{model['provider']}\t{model['family']}\t{model['execution_channel']}\t{model['status']}"
        )
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    benchmark_manifest = load_benchmark_manifest()
    generation_manifest = load_generation_manifest()
    model_registry = load_model_registry()
    errors = validate_manifest_files(generation_manifest, benchmark_manifest, model_registry)

    for model_id in track_ids(benchmark_manifest):
        for path in sorted(packet_dir_for_model(model_id).glob("*.json")):
            errors.extend(
                validate_packet(path, generation_manifest, benchmark_manifest, model_registry)
            )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1

    packet_count = sum(len(list(packet_dir_for_model(model_id).glob("*.json"))) for model_id in track_ids(benchmark_manifest))
    print(f"Validated generation manifest and {packet_count} packet(s).")
    return 0


def cmd_create_packet(args: argparse.Namespace) -> int:
    packet = build_packet(args)
    json_path = packet_path_for(packet["model_id"], packet["packet_id"], "json")
    md_path = packet_path_for(packet["model_id"], packet["packet_id"], "md")

    if json_path.exists() or md_path.exists():
        print(f"Packet already exists: {relative_path(json_path)}", file=sys.stderr)
        return 1

    markdown_text = build_markdown_packet(packet)

    if args.dry_run:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
        return 0

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(markdown_text, encoding="utf-8")
    print(relative_path(json_path))
    print(relative_path(md_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesseract benchmark generation CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_kinds = subparsers.add_parser("list-kinds", help="List generation kinds")
    list_kinds.set_defaults(func=cmd_list_kinds)

    list_targets = subparsers.add_parser("list-targets", help="List supported targets")
    list_targets.set_defaults(func=cmd_list_targets)

    list_recipes = subparsers.add_parser("list-recipes", help="List prompt recipes")
    list_recipes.set_defaults(func=cmd_list_recipes)

    list_models = subparsers.add_parser("list-models", help="List benchmarked models")
    list_models.set_defaults(func=cmd_list_models)

    validate = subparsers.add_parser("validate", help="Validate generation files and packets")
    validate.set_defaults(func=cmd_validate)

    create = subparsers.add_parser("create-packet", help="Create a prompt packet")
    create.add_argument("--model", help="Model id")
    create.add_argument("--track", help="Deprecated alias for --model")
    create.add_argument("--recipe", help="Recipe id")
    create.add_argument("--kind", help="Generation kind")
    create.add_argument("--target", help="Target id")
    create.add_argument("--slug", help="Optional slug override")
    create.add_argument("--recorded-at", help="Optional ISO-8601 timestamp in UTC")
    create.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Additional capability to add beyond the target defaults. Repeat as needed.",
    )
    create.add_argument(
        "--locale",
        action="append",
        default=[],
        help="Requested locale. Repeat as needed.",
    )
    create.add_argument(
        "--var",
        action="append",
        default=[],
        help="Recipe variable override as KEY=VALUE. Repeat as needed.",
    )
    create.add_argument("--dry-run", action="store_true", help="Print the packet JSON without writing files")
    create.set_defaults(func=cmd_create_packet)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
