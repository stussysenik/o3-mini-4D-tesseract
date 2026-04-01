from __future__ import annotations

import unittest

from benchmark_execute import (
    agent_capture_request_execution_payload,
    build_request_payload,
    estimate_cost_from_usage,
    extract_assistant_text_from_payload,
    merge_ingested_benchmark_report,
    normalize_usage_payload,
    parse_generation_response_text,
)


SAMPLE_ASSISTANT_MARKDOWN = """## Implementation Summary

Builds a browser-native WebGPU hypertesseract benchmark scene with a compact report panel.

## Target Declaration

- target_id: ts-webgpu
- target_language: ts
- runtime: browser

## Capability Declaration

- webgpu: true
- wasm: false

## Files

### FILE: index.html
```html
<!doctype html>
<html></html>
```

### FILE: src/main.ts
```ts
console.log("hypertesseract");
```

## Benchmark Report

```json
{
  "target_id": "ts-webgpu",
  "target_language": "ts",
  "runtime": "browser",
  "lane": "primary",
  "used_capabilities": ["html", "css", "dom", "webgpu", "wgsl"],
  "requested_locales": ["en"],
  "wasm_used": false,
  "webgpu_used": true,
  "fallback_path": "none",
  "known_gaps": ["No screenshot capture yet."]
}
```

## Known Limitations

- No screenshot capture yet.
- No performance instrumentation yet.
"""


class ResponseExtractionTests(unittest.TestCase):
    def test_extracts_openai_responses_output_text(self) -> None:
        payload = {
            "id": "resp_123",
            "output_text": SAMPLE_ASSISTANT_MARKDOWN,
        }

        assistant_text, warnings = extract_assistant_text_from_payload(payload, "responses-api")

        self.assertIn("Implementation Summary", assistant_text or "")
        self.assertEqual([], warnings)

    def test_extracts_openai_compatible_chat_content(self) -> None:
        payload = {
            "id": "chatcmpl_123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": SAMPLE_ASSISTANT_MARKDOWN,
                    }
                }
            ],
        }

        assistant_text, warnings = extract_assistant_text_from_payload(payload, "openai-compatible")

        self.assertIn("Benchmark Report", assistant_text or "")
        self.assertEqual([], warnings)

    def test_extracts_anthropic_message_text_blocks(self) -> None:
        payload = {
            "id": "msg_123",
            "content": [
                {
                    "type": "text",
                    "text": SAMPLE_ASSISTANT_MARKDOWN,
                }
            ],
        }

        assistant_text, warnings = extract_assistant_text_from_payload(payload, "messages-api")

        self.assertIn("Known Limitations", assistant_text or "")
        self.assertEqual([], warnings)


class ResponseParsingTests(unittest.TestCase):
    def test_parses_declared_files_and_report(self) -> None:
        parsed = parse_generation_response_text(SAMPLE_ASSISTANT_MARKDOWN)

        self.assertEqual(
            ["index.html", "src/main.ts"],
            [entry["path"] for entry in parsed["file_entries"]],
        )
        self.assertEqual("ts-webgpu", parsed["benchmark_report"]["target_id"])
        self.assertIn("Implementation Summary", parsed["present_sections"])
        self.assertEqual([], parsed["missing_sections"])

    def test_merge_preserves_authoritative_identity_fields(self) -> None:
        base_report = {
            "report_version": 1,
            "result_id": "result-123",
            "benchmark_id": "webgpu-hypertesseract-v1",
            "generation_kind": "one-liner",
            "target_id": "ts-webgpu",
            "target_language": "ts",
            "runtime": "browser",
            "lane": "primary",
            "used_capabilities": ["html", "webgpu"],
            "requested_locales": ["en"],
            "wasm_used": False,
            "webgpu_used": True,
            "fallback_path": "undeclared",
            "known_gaps": ["Generated implementation files have not been attached yet."],
            "hypothesis": "x",
            "method": "y",
            "result_summary": "z",
            "limitations": ["Provider execution has not been captured in this record yet."],
            "next_steps": ["n"],
            "score_ready": False,
            "scoring_status": "pending-review",
            "recommended_run_conditions": {},
        }
        parsed = parse_generation_response_text(SAMPLE_ASSISTANT_MARKDOWN)
        parsed["benchmark_report"]["target_id"] = "wrong-target"

        merged, warnings = merge_ingested_benchmark_report(base_report, parsed)

        self.assertEqual("ts-webgpu", merged["target_id"])
        self.assertEqual(["index.html", "src/main.ts"], merged["generated_files"])
        self.assertNotIn(
            "Generated implementation files have not been attached yet.",
            merged["known_gaps"],
        )
        self.assertTrue(any("target_id" in warning for warning in warnings))

    def test_build_request_payload_includes_reasoning_effort_for_responses_api(self) -> None:
        model = {"id": "gpt-5.4", "provider_model": "gpt-5.4"}
        provider_profile = {"transport": "responses-api"}
        packet = {
            "benchmark_id": "webgpu-hypertesseract-v1",
            "packet_id": "gpt-5.4--packet",
            "generation_kind": "one-liner",
            "target": {"id": "ts-webgpu"},
            "messages": {
                "system_prompt": "system",
                "scene_prompt": "scene",
                "user_prompt": "user",
            },
        }

        payload = build_request_payload(
            model,
            provider_profile,
            packet,
            {"reasoning_effort": "xhigh", "max_output_tokens": 4096},
        )

        self.assertEqual(payload["reasoning"], {"effort": "xhigh"})
        self.assertEqual(payload["max_output_tokens"], 4096)
        self.assertEqual(payload["metadata"]["request_settings"]["reasoning_effort"], "xhigh")

    def test_normalize_usage_and_estimate_cost(self) -> None:
        usage = {
            "input_tokens": 1000,
            "input_tokens_details": {"cached_tokens": 200},
            "output_tokens": 500,
            "output_tokens_details": {"reasoning_tokens": 150},
            "total_tokens": 1500,
        }
        normalized = normalize_usage_payload(usage)
        estimate = estimate_cost_from_usage(
            normalized,
            {
                "model_id": "gpt-5.4",
                "provider_model": "gpt-5.4",
                "effective_date": "2026-04-01",
                "input_per_million_usd": 2.5,
                "cached_input_per_million_usd": 0.25,
                "output_per_million_usd": 15.0,
            },
            {
                "id": "openai-gpt-5-4-pricing-2026-04-01",
                "url": "https://openai.com/index/introducing-gpt-5-4/",
                "retrieved_at": "2026-04-01",
            },
        )

        self.assertEqual(
            normalized,
            {
                "input_tokens": 1000,
                "cached_input_tokens": 200,
                "billable_input_tokens": 800,
                "output_tokens": 500,
                "reasoning_tokens": 150,
                "total_tokens": 1500,
            },
        )
        self.assertAlmostEqual(estimate["estimated_total_usd"], 0.00955, places=8)
        self.assertEqual(estimate["pricing"]["provider_model"], "gpt-5.4")

    def test_agent_capture_request_execution_payload_records_workspace_metadata(self) -> None:
        dispatch = {
            "transport": "workspace-agent",
            "request_settings": {"reasoning_effort": "medium"},
            "request_contract": {
                "prompt_bundle_path": None,
                "prompt_bundle_hash": "prompt-hash",
                "request_payload_path": None,
                "request_payload_hash": None,
            },
        }

        execution = agent_capture_request_execution_payload(
            dispatch,
            started_at="2026-04-01T20:46:00Z",
            finished_at="2026-04-01T20:47:30Z",
            response_text=SAMPLE_ASSISTANT_MARKDOWN,
            runner="codex-workspace",
        )

        self.assertEqual(execution["runner"], "codex-workspace")
        self.assertEqual(execution["endpoint"], "workspace-agent")
        self.assertEqual(execution["duration_ms"], 90000)
        self.assertEqual(execution["workspace_reasoning_effort"], "medium")
        self.assertFalse(execution["token_usage_available"])


if __name__ == "__main__":
    unittest.main()
