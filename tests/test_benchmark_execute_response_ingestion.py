from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from benchmark_execute import (
    ROOT,
    extract_assistant_text_from_payload,
    extract_response_metadata,
    merge_ingested_benchmark_report,
    parse_generation_response_text,
    write_ingested_generation_artifacts,
)


class ResponseIngestionTests(unittest.TestCase):
    def test_extract_assistant_text_from_openai_compatible_payload(self) -> None:
        payload = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "model": "glm-5.1",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": "Implementation Summary\n\nFiles\n\n### FILE: index.html\n```html index.html\n<html></html>\n```"
                    },
                }
            ],
            "usage": {"prompt_tokens": 12, "completion_tokens": 34, "total_tokens": 46},
        }

        text, warnings = extract_assistant_text_from_payload(payload, "openai-compatible")
        metadata = extract_response_metadata(payload, "openai-compatible")

        self.assertEqual(warnings, [])
        self.assertIn("### FILE: index.html", text or "")
        self.assertEqual(metadata["response_id"], "chatcmpl-test")
        self.assertEqual(metadata["provider_model"], "glm-5.1")
        self.assertEqual(metadata["finish_reasons"], ["stop"])
        self.assertEqual(metadata["usage"]["total_tokens"], 46)

    def test_parse_generation_response_text_extracts_files_and_report(self) -> None:
        assistant_text = """# Implementation Summary

High fidelity hypertesseract demo.

## Target Declaration

TypeScript + WebGPU.

## Capability Declaration

- webgpu
- wgsl

## Files

### FILE: index.html
```html index.html
<!doctype html>
<html></html>
```

### FILE: src/main.ts
```ts src/main.ts
console.log("hello");
```

## Benchmark Report

```json
{
  "target_id": "ts-webgpu",
  "target_language": "ts",
  "runtime": "browser",
  "lane": "primary",
  "used_capabilities": ["webgpu", "wgsl"],
  "requested_locales": ["en"],
  "wasm_used": false,
  "webgpu_used": true,
  "fallback_path": "undeclared",
  "known_gaps": ["No screenshots yet."]
}
```

## Known Limitations

- No capture artifacts yet.
"""

        parsed = parse_generation_response_text(assistant_text)

        self.assertEqual(parsed["missing_sections"], [])
        self.assertEqual([entry["path"] for entry in parsed["file_entries"]], ["index.html", "src/main.ts"])
        self.assertEqual(parsed["benchmark_report"]["target_id"], "ts-webgpu")
        self.assertEqual(parsed["limitations"], ["No capture artifacts yet."])

    def test_merge_ingested_benchmark_report_removes_scaffold_gap_when_files_exist(self) -> None:
        base_report = {
            "known_gaps": [
                "Generated implementation files have not been attached yet.",
                "Benchmark scoring has not been completed yet.",
            ],
            "limitations": [
                "This is a scaffolded artifact, not a scored benchmark run.",
                "Provider execution has not been captured in this record yet.",
            ],
            "result_summary": "Scaffolded result bundle created.",
        }
        parsed = {
            "benchmark_report": {
                "used_capabilities": ["webgpu", "wgsl"],
                "known_gaps": ["No screenshots yet."],
            },
            "summary": "Model returned two files.",
            "limitations": ["No screenshots yet."],
            "file_entries": [{"path": "index.html", "language": "html", "content": "<html></html>\n"}],
            "present_sections": ["Files", "Benchmark Report"],
        }

        merged, warnings = merge_ingested_benchmark_report(base_report, parsed)

        self.assertEqual(warnings, [])
        self.assertEqual(merged["result_summary"], "Model returned two files.")
        self.assertIn("index.html", merged["generated_files"])
        self.assertNotIn("Generated implementation files have not been attached yet.", merged["known_gaps"])
        self.assertIn("Benchmark scoring and visual evaluation are still pending.", merged["limitations"])

    def test_write_ingested_generation_artifacts_materializes_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temp_dir:
            base = Path(temp_dir).resolve().relative_to(ROOT)
            dispatch_root = (base / "request-bundles" / "test").as_posix()
            output_root = (base / "output" / "test").as_posix()
            canonical_path = ROOT / dispatch_root / "response.raw.json"
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            canonical_path.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")

            dispatch = {
                "dispatch_id": "test-model--20260401T000000Z--sample",
                "request_bundle_root": dispatch_root,
                "transport": "openai-compatible",
            }
            result = {
                "result_id": "test-model--20260401T000000Z--sample",
                "output_root": output_root,
            }
            captured_response = {
                "source_format": "json",
                "canonical_path": canonical_path,
                "assistant_text": "## Files\n\n### FILE: index.html\n```html index.html\n<html></html>\n```\n",
                "warnings": [],
                "metadata": {
                    "response_id": "chatcmpl-test",
                    "provider_model": "glm-5.1",
                    "status": "chat.completion",
                    "usage": {"total_tokens": 10},
                    "finish_reasons": ["stop"],
                },
            }
            parsed_response = {
                "present_sections": ["Files"],
                "missing_sections": [],
                "warnings": [],
                "file_entries": [
                    {"path": "index.html", "language": "html", "content": "<html></html>\n"}
                ],
            }

            manifest = write_ingested_generation_artifacts(
                dispatch,
                result,
                captured_response,
                parsed_response,
                "2026-04-01T20:00:00Z",
            )

            response_markdown = ROOT / manifest["assistant_response_path"]
            generated_file = ROOT / result["output_root"] / "generated" / "index.html"
            normalized_path = ROOT / dispatch_root / "response.normalized.json"

            self.assertTrue(response_markdown.exists())
            self.assertTrue(generated_file.exists())
            self.assertTrue(normalized_path.exists())
            self.assertEqual(manifest["generated_file_count"], 1)


if __name__ == "__main__":
    unittest.main()
