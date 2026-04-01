# Provider Dispatch: gpt-5.4--20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `gpt-5.4`
- Result: `gpt-5.4--20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `openai-responses`
- Tool Profiles: `codex-workspace`
- Execution Channel: `workspace-agent`
- Transport: `responses-api`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:30:00Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.openai.com/v1/responses",
  "api_key_hint": "$OPENAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "d5adb33fa0fe58f723bdced71eb0f6f776fd4e7393618c54c7c0bb5d33c79a77",
  "request_payload_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "a56d696248b6aa18b74d26b3f2d3fe0eadc2aa4876cb3c6b5cf51b02da033c45",
  "response_placeholder_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/gpt-5.4/20260401T173000Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
