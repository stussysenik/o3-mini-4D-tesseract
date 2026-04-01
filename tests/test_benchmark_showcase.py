from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from benchmark_core import ROOT, load_benchmark_manifest, load_showcase_manifest, relative_path
from benchmark_showcase import (
    build_comparison,
    comparison_path_for,
    load_side,
    resolve_latest_result_reference,
    scan_generated_files,
    site_paths_for,
    site_root_for,
    validate_comparison,
    write_comparison_files,
    write_showcase_index,
)


class ShowcaseComparisonTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _write_result_fixture(
        self,
        root: Path,
        *,
        model_id: str,
        serial: str,
        summary: str,
        files: dict[str, str],
        captures: list[str],
        reasoning_effort: str | None = None,
        status: str = "captured",
    ) -> tuple[Path, Path, dict[str, str]]:
        output_root = root / "executions" / "output" / model_id / serial
        generated_root = output_root / "generated"
        captures_root = output_root / "captures"
        generated_root.mkdir(parents=True, exist_ok=True)
        captures_root.mkdir(parents=True, exist_ok=True)

        for relative_file_path, content in files.items():
            file_path = generated_root / relative_file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

        for capture_name in captures:
            capture_path = captures_root / capture_name
            capture_path.parent.mkdir(parents=True, exist_ok=True)
            capture_path.write_bytes(b"PNG")

        result_id = f"{model_id}--{serial}"
        result_path = root / "executions" / "results" / model_id / f"{serial}.json"
        result_payload = {
            "result_id": result_id,
            "model_id": model_id,
            "status": status,
            "summary": summary,
            "output_root": relative_path(output_root),
            "benchmark_report": {
                "target_id": "ts-webgpu",
                "generation_kind": "one-liner",
                "target_language": "ts",
                "runtime": "browser",
                "lane": "primary",
                "requested_locales": ["en"],
                "webgpu_used": True,
                "wasm_used": False,
            },
        }
        if reasoning_effort:
            result_payload["benchmark_report"]["provider_execution"] = {
                "request_settings": {
                    "reasoning_effort": reasoning_effort,
                }
            }
        self._write_json(result_path, result_payload)
        return result_path, output_root, files

    def _cleanup_result_fixture(self, result_path: Path, output_root: Path) -> None:
        if result_path.exists():
            result_path.unlink()
        if output_root.exists():
            shutil.rmtree(output_root)

    def test_build_comparison_writes_responsive_site_and_code_summary(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            left_result, _, _ = self._write_result_fixture(
                temp_root,
                model_id="alpha-model",
                serial="20260401T210000Z--left-scene",
                summary="Left implementation result.",
                files={
                    "index.html": "<!doctype html>\n<html><body><main>scene</main></body></html>\n",
                    "src/main.ts": "export const side = 'left';\n",
                    "src/left-only.ts": "export const leftOnly = true;\n",
                },
                captures=["scene-mobile.png", "scene-ipad.png", "scene-desktop.png"],
            )
            right_result, _, _ = self._write_result_fixture(
                temp_root,
                model_id="beta-model",
                serial="20260401T210500Z--right-scene",
                summary="Right implementation result.",
                files={
                    "index.html": "<!doctype html>\n<html><body><main>scene</main></body></html>\n",
                    "src/main.ts": "export const side = 'right';\n",
                    "src/right-only.ts": "export const rightOnly = true;\n",
                },
                captures=["scene-mobile.png", "scene-ipad.png", "scene-desktop.png"],
            )

            args = argparse.Namespace(
                left=relative_path(left_result),
                right=relative_path(right_result),
                title=None,
                summary=None,
                slug="alpha-vs-beta-ts-webgpu",
                status=None,
                recorded_at="2026-04-01T22:00:00Z",
                note=[],
                dry_run=False,
            )

            comparison = build_comparison(args)
            self.addCleanup(self._cleanup_comparison_artifacts, comparison["comparison_id"])

            self.assertEqual(comparison["target_id"], "ts-webgpu")
            self.assertEqual(comparison["pair_key"], "alpha-model__vs__beta-model__ts-webgpu")
            self.assertEqual(comparison["code_summary"]["shared_changed"], ["src/main.ts"])
            self.assertEqual(comparison["code_summary"]["left_only"], ["src/left-only.ts"])
            self.assertEqual(comparison["code_summary"]["right_only"], ["src/right-only.ts"])

            write_comparison_files(comparison)

            comparison_json = comparison_path_for(comparison["comparison_id"], "json")
            site_paths = site_paths_for(comparison["comparison_id"])
            site_payload = json.loads(site_paths["data"].read_text(encoding="utf-8"))

            self.assertTrue(comparison_json.exists())
            self.assertTrue(site_paths["html"].exists())
            self.assertTrue(site_paths["css"].exists())
            self.assertTrue(site_paths["js"].exists())
            self.assertTrue((site_paths["root"].parent / "index.html").exists())
            self.assertTrue((site_paths["root"].parent / "index.css").exists())
            self.assertTrue((site_paths["root"].parent / "index.json").exists())
            self.assertIn("Mobile", site_paths["html"].read_text(encoding="utf-8"))
            self.assertIn("Tablet", site_paths["html"].read_text(encoding="utf-8"))
            self.assertIn("Desktop", site_paths["html"].read_text(encoding="utf-8"))
            self.assertEqual(site_payload["comparison_id"], comparison["comparison_id"])
            self.assertEqual(
                [entry["path"] for entry in site_payload["code_summary"]["diff_entries"]],
                ["src/main.ts"],
            )

            errors = validate_comparison(
                comparison_json,
                load_showcase_manifest(),
                load_benchmark_manifest(),
            )
            self.assertEqual(errors, [])

    def test_load_side_prefers_execution_result_id_for_run_references(self) -> None:
        serial = "20260401T220000Z--resolved-scene"
        result_path, output_root, files = self._write_result_fixture(
            ROOT,
            model_id="alpha-model",
            serial=serial,
            summary="Resolved result payload.",
            files={"src/main.ts": "console.log('resolved');\n"},
            captures=["scene-mobile.png"],
        )
        self.addCleanup(self._cleanup_result_fixture, result_path, output_root)

        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            run_path = temp_root / "alpha-model" / "runs" / "20260401T220100Z--resolved-run.json"
            self._write_json(
                run_path,
                {
                    "run_id": "alpha-model--20260401T220100Z--resolved-run",
                    "track": "alpha-model",
                    "status": "completed",
                    "title": "Resolved run",
                    "summary": "Run backed by a result bundle.",
                    "conditions": {
                        "execution_result_id": f"alpha-model--{serial}",
                        "target_id": "ts-webgpu",
                    },
                    "metrics": {},
                    "artifacts": [],
                },
            )

            side, file_contents = load_side(relative_path(run_path), load_showcase_manifest())

        self.assertEqual(side["kind"], "run")
        self.assertEqual(side["linked_result_path"], relative_path(result_path))
        self.assertEqual(side["output_root"], relative_path(output_root))
        self.assertEqual(side["captures_by_device"]["mobile"]["filename"], "scene-mobile.png")
        self.assertEqual(file_contents["src/main.ts"], files["src/main.ts"])

    def test_scan_generated_files_skips_binary_content_for_code_diffs(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            output_root = temp_root / "executions" / "output" / "gamma-model" / "20260401T221000Z--binary-scene"
            generated_root = output_root / "generated"
            generated_root.mkdir(parents=True, exist_ok=True)
            (generated_root / "src").mkdir(parents=True, exist_ok=True)
            (generated_root / "src" / "main.ts").write_text("console.log('text');\n", encoding="utf-8")
            (generated_root / "build.wasm").write_bytes(b"\x00asm\x01\x00\x00\x00")

            inventory, contents = scan_generated_files(output_root)

            self.assertEqual(contents, {"src/main.ts": "console.log('text');\n"})
            binary_entry = next(item for item in inventory if item["path"] == "build.wasm")
            self.assertTrue(binary_entry["binary"])
            self.assertIsNone(binary_entry["line_count"])

    def test_load_side_exposes_reasoning_effort_variant_label(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            temp_root = Path(temp_dir)
            result_path, _, _ = self._write_result_fixture(
                temp_root,
                model_id="gpt-5.4",
                serial="20260401T222000Z--xhigh-scene",
                summary="Variant result payload.",
                files={"src/main.ts": "console.log('variant');\n"},
                captures=[],
                reasoning_effort="xhigh",
            )

            side, _ = load_side(relative_path(result_path), load_showcase_manifest())

            self.assertEqual(side["label"], "gpt-5.4 (xhigh)")
            self.assertEqual(side["comparison_key"], "gpt-5.4[xhigh]")
            self.assertEqual(side["reasoning_effort"], "xhigh")

    def test_resolve_latest_result_reference_filters_by_variant_and_status(self) -> None:
        first_path, first_output_root, _ = self._write_result_fixture(
            ROOT,
            model_id="selector-model",
            serial="20260401T223000Z--medium-scaffolded",
            summary="Older scaffolded result.",
            files={"src/main.ts": "console.log('older');\n"},
            captures=[],
            reasoning_effort="medium",
            status="scaffolded",
        )
        second_path, second_output_root, _ = self._write_result_fixture(
            ROOT,
            model_id="selector-model",
            serial="20260401T223500Z--medium-captured",
            summary="Latest captured result.",
            files={"src/main.ts": "console.log('latest');\n"},
            captures=[],
            reasoning_effort="medium",
            status="captured",
        )
        self.addCleanup(self._cleanup_result_fixture, first_path, first_output_root)
        self.addCleanup(self._cleanup_result_fixture, second_path, second_output_root)

        latest = resolve_latest_result_reference(
            model_id="selector-model",
            target_id="ts-webgpu",
            reasoning_effort="medium",
        )
        including_scaffolded = resolve_latest_result_reference(
            model_id="selector-model",
            target_id="ts-webgpu",
            reasoning_effort="medium",
            allow_scaffolded=True,
        )

        self.assertEqual(latest, relative_path(second_path))
        self.assertEqual(including_scaffolded, relative_path(second_path))

    def _cleanup_comparison_artifacts(self, comparison_id: str) -> None:
        json_path = comparison_path_for(comparison_id, "json")
        md_path = comparison_path_for(comparison_id, "md")
        site_root = site_root_for(comparison_id)
        if json_path.exists():
            json_path.unlink()
        if md_path.exists():
            md_path.unlink()
        if site_root.exists():
            shutil.rmtree(site_root)
        write_showcase_index()


if __name__ == "__main__":
    unittest.main()
