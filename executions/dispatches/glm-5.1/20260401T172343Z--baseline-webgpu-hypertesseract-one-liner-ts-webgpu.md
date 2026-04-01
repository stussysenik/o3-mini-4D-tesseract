# Provider Dispatch: glm-5.1--20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `glm-5.1`
- Result: `glm-5.1--20260401T165941Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `zai-openai-compatible`
- Tool Profiles: `zai-claude-code-bridge`
- Execution Channel: `manual-or-api`
- Transport: `openai-compatible`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:23:43.726348Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.z.ai/api/paas/v4/chat/completions",
  "api_key_hint": "$ZAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "e2f18731647679dd8e9ede60959cacd92f69301530ee23f6f96118f6174b09ba",
  "request_payload_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "cfd7e072530bb8c2a9329605a728bc1a4a3c4b6d9aee2f88b4cacbf48f2cba09",
  "response_placeholder_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/glm-5.1/20260401T165941Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
