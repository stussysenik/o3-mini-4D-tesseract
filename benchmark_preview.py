from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from benchmark_core import ROOT, relative_path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_reference_path(reference: str) -> Path:
    path = Path(reference)
    resolved = path if path.is_absolute() else (ROOT / path).resolve()
    if not resolved.exists():
        raise ValueError(f"Reference does not exist: {reference}")
    return resolved


def resolve_result_generated_root(reference: str) -> Path:
    path = resolve_reference_path(reference)
    result = load_json(path)
    if "result_id" not in result:
        raise ValueError(f"Not an execution result: {reference}")
    output_root = ROOT / result["output_root"]
    generated_root = output_root / "generated"
    if not generated_root.exists():
        raise ValueError(f"Generated output root is missing: {relative_path(generated_root)}")
    index_path = generated_root / "index.html"
    if not index_path.exists():
        raise ValueError(f"Generated output is missing index.html: {relative_path(index_path)}")
    return generated_root


def resolve_showcase_root(reference: str) -> Path:
    path = resolve_reference_path(reference)
    if path.is_dir():
        index_path = path / "index.html"
        if not index_path.exists():
            raise ValueError(f"Showcase directory is missing index.html: {relative_path(index_path)}")
        return path

    comparison = load_json(path)
    if "comparison_id" not in comparison:
        raise ValueError(f"Not a showcase comparison record: {reference}")
    site_root = ROOT / comparison["site_root"]
    index_path = site_root / "index.html"
    if not index_path.exists():
        raise ValueError(f"Showcase site is missing index.html: {relative_path(index_path)}")
    return site_root


def resolve_vite_bin() -> list[str]:
    local_vite = ROOT / "node_modules" / ".bin" / "vite"
    if local_vite.exists():
        return [str(local_vite)]

    npm = shutil.which("npm")
    if npm:
        return [npm, "exec", "vite", "--"]

    raise ValueError("Could not find a local Vite install or npm. Run `npm install` first.")


def preview_url(host: str, port: int) -> str:
    display_host = "127.0.0.1" if host == "0.0.0.0" else host
    return f"http://{display_host}:{port}/"


def vite_command(root: Path, *, host: str, port: int, open_browser: bool) -> list[str]:
    command = [
        *resolve_vite_bin(),
        str(root),
        "--host",
        host,
        "--port",
        str(port),
        "--strictPort",
    ]
    if open_browser:
        command.append("--open")
    return command


def run_vite(root: Path, *, host: str, port: int, open_browser: bool) -> int:
    command = vite_command(root, host=host, port=port, open_browser=open_browser)
    print(f"Serving {relative_path(root)}")
    print(preview_url(host, port))
    return subprocess.call(command, cwd=ROOT)


def cmd_serve_result(args: argparse.Namespace) -> int:
    try:
        root = resolve_result_generated_root(args.result)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return run_vite(root, host=args.host, port=args.port, open_browser=args.open)


def cmd_serve_showcase(args: argparse.Namespace) -> int:
    try:
        root = resolve_showcase_root(args.comparison)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return run_vite(root, host=args.host, port=args.port, open_browser=args.open)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local preview server for generated benchmark outputs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_result = subparsers.add_parser("serve-result", help="Serve a captured execution result's generated output via Vite")
    serve_result.add_argument("--result", required=True, help="Execution result JSON path")
    serve_result.add_argument("--host", default="127.0.0.1", help="Preview host")
    serve_result.add_argument("--port", type=int, default=4173, help="Preview port")
    serve_result.add_argument("--open", action="store_true", help="Open the browser automatically")
    serve_result.set_defaults(func=cmd_serve_result)

    serve_showcase = subparsers.add_parser("serve-showcase", help="Serve a showcase comparison site via Vite")
    serve_showcase.add_argument("--comparison", required=True, help="Comparison JSON path or site root")
    serve_showcase.add_argument("--host", default="127.0.0.1", help="Preview host")
    serve_showcase.add_argument("--port", type=int, default=4174, help="Preview port")
    serve_showcase.add_argument("--open", action="store_true", help="Open the browser automatically")
    serve_showcase.set_defaults(func=cmd_serve_showcase)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
