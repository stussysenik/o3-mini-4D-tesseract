# Provider Dispatch: gpt-5.4--20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex

## Metadata
- Model: `gpt-5.4`
- Result: `gpt-5.4--20260401T204500Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium`
- Provider Profile: `codex-workspace`
- Tool Profiles: `codex-workspace`
- Execution Channel: `workspace-agent`
- Transport: `workspace-agent`
- Status: `captured`
- Request Bundle: `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex`
- Created At: `2026-04-01T20:46:00Z`

## Invocation
```json
{
  "kind": "manual-handoff",
  "endpoint": null,
  "api_key_hint": "",
  "suggested_command": "open executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/invocation.md"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/prompt_bundle.md",
  "prompt_bundle_hash": "5e262819cc9ded65316a9520ecca50ca530633cb7e08b1752bf77318973cb2d3",
  "request_payload_path": null,
  "request_payload_hash": null,
  "response_placeholder_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.placeholder.json"
}
```


## Request Settings
```json
{
  "reasoning_effort": "medium"
}
```



## Request Execution
```json
{
  "runner": "codex-workspace gpt-5.4 medium",
  "started_at": "2026-04-01T20:46:00Z",
  "finished_at": "2026-04-01T20:50:30Z",
  "duration_ms": 270000,
  "endpoint": "workspace-agent",
  "request_payload_path": null,
  "request_payload_hash": null,
  "prompt_bundle_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/prompt_bundle.md",
  "prompt_bundle_hash": "5e262819cc9ded65316a9520ecca50ca530633cb7e08b1752bf77318973cb2d3",
  "request_bytes": 3873,
  "response_bytes": 18176,
  "response_content_type": "text/markdown",
  "agent_transport": "workspace-agent",
  "workspace_reasoning_effort": "medium",
  "token_usage_available": false,
  "cost_available": false,
  "notes": [
    "Agent-captured execution does not expose provider token usage or billing telemetry in this environment."
  ]
}
```


## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.text.md",
  "generated_manifest_path": "executions/output/gpt-5.4/20260401T204500Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex.json"
}
```


## Response Capture
```json
{
  "captured_at": "2026-04-01T20:50:30Z",
  "source_format": "text",
  "source_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.raw.txt",
  "canonical_response_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.normalized.json",
  "assistant_text_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.text.md",
  "generated_manifest_path": "executions/output/gpt-5.4/20260401T204500Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium/generated/generation_manifest.json",
  "extracted_file_count": 3,
  "request_settings": {
    "reasoning_effort": "medium"
  },
  "request_execution": {
    "runner": "codex-workspace gpt-5.4 medium",
    "started_at": "2026-04-01T20:46:00Z",
    "finished_at": "2026-04-01T20:50:30Z",
    "duration_ms": 270000,
    "endpoint": "workspace-agent",
    "request_payload_path": null,
    "request_payload_hash": null,
    "prompt_bundle_path": "executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/prompt_bundle.md",
    "prompt_bundle_hash": "5e262819cc9ded65316a9520ecca50ca530633cb7e08b1752bf77318973cb2d3",
    "request_bytes": 3873,
    "response_bytes": 18176,
    "response_content_type": "text/markdown",
    "agent_transport": "workspace-agent",
    "workspace_reasoning_effort": "medium",
    "token_usage_available": false,
    "cost_available": false,
    "notes": [
      "Agent-captured execution does not expose provider token usage or billing telemetry in this environment."
    ]
  },
  "provider_response": {
    "response_id": null,
    "provider_model": null,
    "status": null,
    "usage": null,
    "finish_reasons": []
  },
  "normalized_usage": null,
  "cost_estimate": null,
  "warnings": [
    "Ignored benchmark report field `target_id` from model output; result metadata is authoritative.",
    "Ignored benchmark report field `target_language` from model output; result metadata is authoritative.",
    "Ignored benchmark report field `runtime` from model output; result metadata is authoritative."
  ]
}
```


## Request Artifacts
- `executions/dispatches/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex.json` (dispatch-record)
- `executions/dispatches/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex.md` (dispatch-record-doc)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/invocation.md` (invocation-doc)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.normalized.json` (response-normalized)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.placeholder.json` (response-placeholder)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.raw.txt` (response-raw-text)
- `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/response.text.md` (response-text)
