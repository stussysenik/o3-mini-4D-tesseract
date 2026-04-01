from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from benchmark_core import (
    ROOT,
    content_hash,
    execution_dispatch_dir_for_model,
    execution_plan_dir_for_model,
    execution_result_dir_for_model,
    load_benchmark_manifest,
    load_execution_manifest,
    load_showcase_manifest,
    packet_dir_for_model,
    relative_path,
    run_dir_for_track,
    showcase_comparison_dir,
    track_ids,
    write_text_if_changed,
)

CATALOG_PATH = ROOT / "benchmark_catalog.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def scan_packets(benchmark_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for model_id in track_ids(benchmark_manifest):
        for path in sorted(packet_dir_for_model(model_id).glob("*.json")):
            packet = load_json(path)
            semantic_hash = content_hash(semantic_packet_payload(packet))
            exact_hash = content_hash(packet)
            packets.append(
                {
                    "packet_id": packet["packet_id"],
                    "model_id": packet["model_id"],
                    "recipe_id": packet["recipe_id"],
                    "scene_id": packet["scene_id"],
                    "generation_kind": packet["generation_kind"],
                    "target_id": packet["target"]["id"],
                    "created_at": packet["created_at"],
                    "path": relative_path(path),
                    "markdown_path": relative_path(path.with_suffix(".md")),
                    "exact_hash": exact_hash,
                    "semantic_hash": semantic_hash,
                }
            )
    packets.sort(key=lambda item: (item["model_id"], item["created_at"], item["path"]), reverse=True)
    return packets


def scan_runs(benchmark_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for model_id in track_ids(benchmark_manifest):
        for path in sorted(run_dir_for_track(benchmark_manifest, model_id).glob("*.json")):
            run = load_json(path)
            runs.append(
                {
                    "run_id": run["run_id"],
                    "model_id": run["track"],
                    "title": run["title"],
                    "status": run["status"],
                    "created_at": run["created_at"],
                    "path": relative_path(path),
                }
            )
    runs.sort(key=lambda item: (item["model_id"], item["created_at"], item["path"]), reverse=True)
    return runs


def scan_plans(benchmark_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for model_id in track_ids(benchmark_manifest):
        for path in sorted(execution_plan_dir_for_model(model_id).glob("*.json")):
            plan = load_json(path)
            plans.append(
                {
                    "plan_id": plan["plan_id"],
                    "model_id": plan["model_id"],
                    "packet_id": plan["packet_id"],
                    "status": plan["status"],
                    "execution_mode": plan["execution_mode"],
                    "created_at": plan["created_at"],
                    "path": relative_path(path),
                    "markdown_path": relative_path(path.with_suffix(".md")),
                }
            )
    plans.sort(key=lambda item: (item["model_id"], item["created_at"], item["path"]), reverse=True)
    return plans


def semantic_result_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_id": result["model_id"],
        "plan_id": result["plan_id"],
        "packet_id": result["packet_id"],
        "execution_mode": result["execution_mode"],
        "status": result["status"],
        "summary": result["summary"],
        "generation_target": result["generation_target"],
        "benchmark_report": result["benchmark_report"],
        "review_state": result["review_state"],
    }


def scan_results(benchmark_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for model_id in track_ids(benchmark_manifest):
        for path in sorted(execution_result_dir_for_model(model_id).glob("*.json")):
            result = load_json(path)
            semantic_hash = content_hash(semantic_result_payload(result))
            exact_hash = content_hash(result)
            results.append(
                {
                    "result_id": result["result_id"],
                    "model_id": result["model_id"],
                    "plan_id": result["plan_id"],
                    "packet_id": result["packet_id"],
                    "status": result["status"],
                    "execution_mode": result["execution_mode"],
                    "created_at": result["created_at"],
                    "summary": result["summary"],
                    "path": relative_path(path),
                    "markdown_path": relative_path(path.with_suffix(".md")),
                    "output_root": result["output_root"],
                    "linked_run_id": result.get("review_state", {}).get("linked_run_id"),
                    "linked_run_path": result.get("review_state", {}).get("linked_run_path"),
                    "exact_hash": exact_hash,
                    "semantic_hash": semantic_hash,
                }
            )
    results.sort(key=lambda item: (item["model_id"], item["created_at"], item["path"]), reverse=True)
    return results


def semantic_dispatch_payload(dispatch: dict[str, Any]) -> dict[str, Any]:
    return {
        "model_id": dispatch["model_id"],
        "result_id": dispatch["result_id"],
        "plan_id": dispatch["plan_id"],
        "packet_id": dispatch["packet_id"],
        "provider_profile_id": dispatch["provider_profile_id"],
        "tool_profile_ids": dispatch["tool_profile_ids"],
        "execution_channel": dispatch["execution_channel"],
        "transport": dispatch["transport"],
        "status": dispatch["status"],
        "request_contract": dispatch["request_contract"],
        "invocation": dispatch["invocation"],
    }


def scan_dispatches(benchmark_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    dispatches: list[dict[str, Any]] = []
    for model_id in track_ids(benchmark_manifest):
        for path in sorted(execution_dispatch_dir_for_model(model_id).glob("*.json")):
            dispatch = load_json(path)
            semantic_hash = content_hash(semantic_dispatch_payload(dispatch))
            exact_hash = content_hash(dispatch)
            dispatches.append(
                {
                    "dispatch_id": dispatch["dispatch_id"],
                    "model_id": dispatch["model_id"],
                    "result_id": dispatch["result_id"],
                    "provider_profile_id": dispatch["provider_profile_id"],
                    "transport": dispatch["transport"],
                    "status": dispatch["status"],
                    "created_at": dispatch["created_at"],
                    "path": relative_path(path),
                    "markdown_path": relative_path(path.with_suffix(".md")),
                    "request_bundle_root": dispatch["request_bundle_root"],
                    "exact_hash": exact_hash,
                    "semantic_hash": semantic_hash,
                }
            )
    dispatches.sort(key=lambda item: (item["model_id"], item["created_at"], item["path"]), reverse=True)
    return dispatches


def scan_comparisons() -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    comparison_dir = showcase_comparison_dir()
    if not comparison_dir.exists():
        return comparisons
    for path in sorted(comparison_dir.glob("*.json")):
        comparison = load_json(path)
        comparisons.append(
            {
                "comparison_id": comparison["comparison_id"],
                "created_at": comparison["created_at"],
                "title": comparison["title"],
                "status": comparison["status"],
                "target_id": comparison["target_id"],
                "pair_key": comparison["pair_key"],
                "left_model_id": comparison["left"]["model_id"],
                "right_model_id": comparison["right"]["model_id"],
                "path": relative_path(path),
                "markdown_path": relative_path(path.with_suffix(".md")),
                "site_root": comparison["site_root"],
            }
        )
    comparisons.sort(key=lambda item: (item["pair_key"], item["created_at"], item["path"]), reverse=True)
    return comparisons


def group_duplicates(items: list[dict[str, Any]], hash_key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        groups.setdefault(item[hash_key], []).append(item)

    duplicates = []
    for key, group in groups.items():
        if len(group) < 2:
            continue
        group_sorted = sorted(group, key=lambda item: (item["created_at"], item["path"]), reverse=True)
        duplicates.append(
            {
                hash_key: key,
                "keep": group_sorted[0]["path"],
                "members": [entry["path"] for entry in group_sorted],
            }
        )
    duplicates.sort(key=lambda item: item[hash_key])
    return duplicates


def latest_by_model(items: list[dict[str, Any]], path_key: str = "path") -> dict[str, str]:
    latest: dict[str, str] = {}
    for item in sorted(items, key=lambda entry: (entry["model_id"], entry["created_at"], entry[path_key]), reverse=True):
        latest.setdefault(item["model_id"], item[path_key])
    return latest


def latest_by_identity(items: list[dict[str, Any]], identity_key: str, path_key: str = "path") -> dict[str, str]:
    latest: dict[str, str] = {}
    for item in sorted(items, key=lambda entry: (entry[identity_key], entry["created_at"], entry[path_key]), reverse=True):
        latest.setdefault(item[identity_key], item[path_key])
    return latest


def build_catalog() -> dict[str, Any]:
    benchmark_manifest = load_benchmark_manifest()
    execution_manifest = load_execution_manifest()
    showcase_manifest = load_showcase_manifest()
    packets = scan_packets(benchmark_manifest)
    runs = scan_runs(benchmark_manifest)
    plans = scan_plans(benchmark_manifest)
    results = scan_results(benchmark_manifest)
    dispatches = scan_dispatches(benchmark_manifest)
    comparisons = scan_comparisons()

    catalog = {
        "benchmark_id": benchmark_manifest["benchmark_id"],
        "models": list(track_ids(benchmark_manifest)),
        "execution_catalog_path": execution_manifest["catalog_path"],
        "showcase_catalog_version": showcase_manifest["version"],
        "packets": packets,
        "plans": plans,
        "results": results,
        "dispatches": dispatches,
        "comparisons": comparisons,
        "runs": runs,
        "latest": {
            "packets_by_model": latest_by_model(packets),
            "plans_by_model": latest_by_model(plans),
            "results_by_model": latest_by_model(results),
            "outputs_by_model": latest_by_model(results, "output_root"),
            "dispatches_by_model": latest_by_model(dispatches),
            "request_bundles_by_model": latest_by_model(dispatches, "request_bundle_root"),
            "comparisons_by_pair": latest_by_identity(comparisons, "pair_key"),
            "comparison_sites_by_pair": latest_by_identity(comparisons, "pair_key", "site_root"),
            "runs_by_model": latest_by_model(runs),
        },
        "duplicates": {
            "exact_packets": group_duplicates(packets, "exact_hash"),
            "semantic_packets": group_duplicates(packets, "semantic_hash"),
            "exact_results": group_duplicates(results, "exact_hash"),
            "semantic_results": group_duplicates(results, "semantic_hash"),
            "exact_dispatches": group_duplicates(dispatches, "exact_hash"),
            "semantic_dispatches": group_duplicates(dispatches, "semantic_hash"),
        },
    }
    return catalog


def cmd_build_catalog(args: argparse.Namespace) -> int:
    catalog = build_catalog()
    content = json.dumps(catalog, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        current = CATALOG_PATH.read_text(encoding="utf-8") if CATALOG_PATH.exists() else None
        if current != content:
            print(f"Generated file is stale: {relative_path(CATALOG_PATH)}", file=sys.stderr)
            return 1
        return 0

    write_text_if_changed(CATALOG_PATH, content)
    print(relative_path(CATALOG_PATH))
    return 0


def cmd_list_latest(args: argparse.Namespace) -> int:
    catalog = build_catalog()
    latest = catalog["latest"]
    key = {
        "packet": "packets_by_model",
        "plan": "plans_by_model",
        "result": "results_by_model",
        "output": "outputs_by_model",
        "dispatch": "dispatches_by_model",
        "request-bundle": "request_bundles_by_model",
        "comparison": "comparisons_by_pair",
        "comparison-site": "comparison_sites_by_pair",
        "run": "runs_by_model",
    }[args.kind]

    identity = args.pair if args.kind in {"comparison", "comparison-site"} else args.model
    if identity:
        path = latest[key].get(identity)
        if not path:
            qualifier = args.pair if args.kind in {"comparison", "comparison-site"} else args.model
            print(f"No {args.kind} found for {qualifier}", file=sys.stderr)
            return 1
        print(path)
        return 0

    for model_id, path in sorted(latest[key].items()):
        print(f"{model_id}\t{path}")
    return 0


def cmd_find_duplicates(args: argparse.Namespace) -> int:
    catalog = build_catalog()
    duplicate_key = {
        ("packet", "exact"): "exact_packets",
        ("packet", "semantic"): "semantic_packets",
        ("result", "exact"): "exact_results",
        ("result", "semantic"): "semantic_results",
        ("dispatch", "exact"): "exact_dispatches",
        ("dispatch", "semantic"): "semantic_dispatches",
    }[(args.kind, args.mode)]
    groups = catalog["duplicates"][duplicate_key]
    if not groups:
        print(f"No duplicate {args.kind}s found.")
        return 0

    for group in groups:
        print(f"keep\t{group['keep']}")
        for member in group["members"]:
            print(f"member\t{member}")
    return 0


def packet_markdown_pair(packet_json_path: str) -> Path:
    return (ROOT / packet_json_path).with_suffix(".md")


def cmd_prune_packets(args: argparse.Namespace) -> int:
    catalog = build_catalog()
    duplicate_key = {
        "exact": "exact_packets",
        "semantic": "semantic_packets",
    }[args.mode]
    groups = catalog["duplicates"][duplicate_key]

    deletions: list[Path] = []
    for group in groups:
        for member in group["members"]:
            if member == group["keep"]:
                continue
            deletions.append(ROOT / member)
            markdown_pair = packet_markdown_pair(member)
            if markdown_pair.exists():
                deletions.append(markdown_pair)

    if not deletions:
        print("No packet deletions needed.")
        return 0

    for path in deletions:
        print(relative_path(path))

    if not args.apply:
        return 0

    for path in deletions:
        if path.exists():
            os.remove(path)
    print(f"Deleted {len(deletions)} file(s).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tesseract benchmark admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build-catalog", help="Build the SSOT benchmark catalog")
    build.add_argument("--check", action="store_true", help="Fail instead of writing if the catalog is stale")
    build.set_defaults(func=cmd_build_catalog)

    latest = subparsers.add_parser("list-latest", help="List latest packet, plan, result, output, dispatch, request-bundle, or run paths")
    latest.add_argument("--kind", choices=["packet", "plan", "result", "output", "dispatch", "request-bundle", "comparison", "comparison-site", "run"], default="packet")
    latest.add_argument("--model", help="Optional model filter")
    latest.add_argument("--pair", help="Optional comparison pair filter for comparison kinds")
    latest.set_defaults(func=cmd_list_latest)

    duplicates = subparsers.add_parser("find-duplicates", help="Find duplicate packets, results, or dispatches")
    duplicates.add_argument("--kind", choices=["packet", "result", "dispatch"], default="packet")
    duplicates.add_argument("--mode", choices=["exact", "semantic"], default="semantic")
    duplicates.set_defaults(func=cmd_find_duplicates)

    prune = subparsers.add_parser("prune-packets", help="Prune duplicate packets, keeping the latest")
    prune.add_argument("--mode", choices=["exact", "semantic"], default="semantic")
    prune.add_argument("--apply", action="store_true", help="Actually delete files instead of printing them")
    prune.set_defaults(func=cmd_prune_packets)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
