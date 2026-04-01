from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import subprocess
from functools import lru_cache
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
BENCHMARK_MANIFEST_PATH = ROOT / "benchmark_manifest.json"
GENERATION_MANIFEST_PATH = ROOT / "generation" / "manifest.json"
MODEL_REGISTRY_PATH = ROOT / "models" / "registry.json"
PROVIDER_REGISTRY_PATH = ROOT / "providers" / "registry.json"
PRICING_MANIFEST_PATH = ROOT / "providers" / "pricing.json"
EXECUTION_MANIFEST_PATH = ROOT / "executions" / "manifest.json"
SHOWCASE_MANIFEST_PATH = ROOT / "showcase" / "manifest.json"
LOCAL_ENV_PATHS = (ROOT / ".env.local", ROOT / ".env")

ENV_CAPTURE_KEYS = (
    "TB_BROWSER_NAME",
    "TB_BROWSER_VERSION",
    "TB_BROWSER_CHANNEL",
    "TB_GPU_VENDOR",
    "TB_GPU_ADAPTER",
    "TB_GPU_DRIVER",
    "TB_WEBGPU_BACKEND",
    "TB_WASM_RUNTIME",
    "TB_WASM_FEATURES",
    "TB_LOCALE",
    "TB_CANVAS_SIZE",
    "TB_DEVICE_PIXEL_RATIO",
    "TB_HEADLESS",
    "TB_OS_NOTES",
)


def load_json(path: Path) -> dict[str, Any] | list[Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text_if_changed(path: Path, content: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else None
    if current != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_json_if_changed(path: Path, data: Any) -> None:
    write_text_if_changed(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def load_benchmark_manifest() -> dict[str, Any]:
    return load_json(BENCHMARK_MANIFEST_PATH)


def load_generation_manifest() -> dict[str, Any]:
    return load_json(GENERATION_MANIFEST_PATH)


def load_model_registry() -> dict[str, Any]:
    return load_json(MODEL_REGISTRY_PATH)


def load_provider_registry() -> dict[str, Any]:
    return load_json(PROVIDER_REGISTRY_PATH)


def load_pricing_manifest() -> dict[str, Any]:
    return load_json(PRICING_MANIFEST_PATH)


def load_execution_manifest() -> dict[str, Any]:
    return load_json(EXECUTION_MANIFEST_PATH)


def load_showcase_manifest() -> dict[str, Any]:
    return load_json(SHOWCASE_MANIFEST_PATH)


def index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def track_ids(manifest: dict[str, Any]) -> tuple[str, ...]:
    return tuple(track["id"] for track in manifest["tracks"])


def track_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(manifest["tracks"])


def model_ids(model_registry: dict[str, Any]) -> tuple[str, ...]:
    return tuple(model["id"] for model in model_registry["models"])


def model_map(model_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(model_registry["models"])


def provider_ids(provider_registry: dict[str, Any]) -> tuple[str, ...]:
    return tuple(profile["id"] for profile in provider_registry["profiles"])


def provider_map(provider_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return index_by_id(provider_registry["profiles"])


def storage_root_for_track(manifest: dict[str, Any], track_id: str) -> Path:
    track = track_map(manifest)[track_id]
    return ROOT / track["storage_root"]


def run_dir_for_track(manifest: dict[str, Any], track_id: str) -> Path:
    return storage_root_for_track(manifest, track_id) / "runs"


def packet_dir_for_model(model_id: str) -> Path:
    return ROOT / "generation" / "packets" / model_id


def execution_plan_dir_for_model(model_id: str) -> Path:
    return ROOT / "executions" / "plans" / model_id


def execution_result_dir_for_model(model_id: str) -> Path:
    return ROOT / "executions" / "results" / model_id


def execution_output_dir_for_model(model_id: str) -> Path:
    return ROOT / "executions" / "output" / model_id


def execution_dispatch_dir_for_model(model_id: str) -> Path:
    return ROOT / "executions" / "dispatches" / model_id


def execution_request_bundle_dir_for_model(model_id: str) -> Path:
    return ROOT / "executions" / "request-bundles" / model_id


def showcase_root() -> Path:
    return ROOT / "showcase"


def showcase_comparison_dir() -> Path:
    return showcase_root() / "comparisons"


def showcase_site_dir() -> Path:
    return showcase_root() / "site"


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "run"


def parse_timestamp(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def now_utc() -> datetime:
    return datetime.now(UTC)


def coerce_scalar(raw: str) -> Any:
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        if raw.startswith("0") and raw != "0" and not raw.startswith("0."):
            raise ValueError
        return int(raw)
    except ValueError:
        pass

    try:
        return float(raw)
    except ValueError:
        return raw


def parse_pairs(items: list[str] | None) -> dict[str, Any]:
    pairs: dict[str, Any] = {}
    for item in items or []:
        if "=" not in item:
            raise ValueError(f"Expected KEY=VALUE, got: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Missing key in pair: {item}")
        if key in pairs:
            raise ValueError(f"Duplicate key: {key}")
        pairs[key] = coerce_scalar(value.strip())
    return pairs


def git_output(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def collect_environment() -> dict[str, Any]:
    captured = {}
    for key in ENV_CAPTURE_KEYS:
        value = os.getenv(key)
        if value:
            captured[key.removeprefix("TB_").lower()] = coerce_scalar(value)

    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "git_branch": git_output("rev-parse", "--abbrev-ref", "HEAD"),
        "git_commit": git_output("rev-parse", "HEAD"),
        "captured": captured,
    }


def build_time_ledger(dt: datetime) -> dict[str, Any]:
    iso_year, iso_week, iso_weekday = dt.isocalendar()
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    delta = dt - epoch
    epoch_seconds = (delta.days * 24 * 60 * 60) + delta.seconds
    epoch_ms = (epoch_seconds * 1_000) + (delta.microseconds // 1_000)
    epoch_ns = (epoch_seconds * 1_000_000_000) + (delta.microseconds * 1_000)
    return {
        "recorded_at_utc": dt.isoformat().replace("+00:00", "Z"),
        "epoch_ms": epoch_ms,
        "epoch_ns": epoch_ns,
        "year": dt.year,
        "quarter": f"Q{((dt.month - 1) // 3) + 1}",
        "month": dt.month,
        "day": dt.day,
        "day_of_year": dt.timetuple().tm_yday,
        "iso_week": f"{iso_year}-W{iso_week:02d}",
        "iso_weekday": iso_weekday,
    }


def normalized_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def content_hash(data: Any) -> str:
    digest = hashlib.sha256()
    digest.update(normalized_json(data).encode("utf-8"))
    return digest.hexdigest()


def parse_env_assignment(raw_line: str) -> tuple[str, str] | None:
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        return None

    name, raw_value = line.split("=", 1)
    name = name.strip()
    raw_value = raw_value.strip()
    if not name:
        return None

    if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in {'"', "'"}:
        quote = raw_value[0]
        value = raw_value[1:-1]
        if quote == '"':
            value = bytes(value, "utf-8").decode("unicode_escape")
        return name, value

    return name, raw_value


@lru_cache(maxsize=1)
def local_env_values() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in reversed(LOCAL_ENV_PATHS):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed = parse_env_assignment(line)
            if parsed is None:
                continue
            name, value = parsed
            values[name] = value
    return values


def read_env(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    local_value = local_env_values().get(name)
    return local_value if local_value else None


def env_presence(name: str) -> dict[str, Any]:
    value = read_env(name)
    return {
        "name": name,
        "present": value is not None,
        "length": len(value) if value is not None else 0,
    }


def evaluate_env_requirements(profile: dict[str, Any]) -> dict[str, Any]:
    required = profile.get("required_env", [])
    required_any = profile.get("required_any_env", [])
    optional = profile.get("optional_env", [])

    required_status = [env_presence(name) for name in required]
    any_groups = []
    for names in required_any:
        statuses = [env_presence(name) for name in names]
        any_groups.append(
            {
                "names": names,
                "satisfied": any(status["present"] for status in statuses),
                "statuses": statuses,
            }
        )

    optional_status = [env_presence(name) for name in optional]
    satisfied = all(item["present"] for item in required_status) and all(
        group["satisfied"] for group in any_groups
    )

    return {
        "required": required_status,
        "required_any": any_groups,
        "optional": optional_status,
        "satisfied": satisfied,
    }
