# Provider Dispatch: glm-5.1--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `glm-5.1`
- Result: `glm-5.1--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `zai-openai-compatible`
- Tool Profiles: `zai-claude-code-bridge`
- Execution Channel: `manual-or-api`
- Transport: `openai-compatible`
- Status: `sent`
- Request Bundle: `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:51:49.534256Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.z.ai/api/paas/v4/chat/completions",
  "api_key_hint": "$ZAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "4fb5ef538368169b5d4571dd87a02f5e9a93011822f22e40331ceb898aeb4ad8",
  "request_payload_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "ce88ba876dd275f41db1d455aefa35d0cf917dde5befd0419eb3bc659ebc51e7",
  "response_placeholder_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```



## Request Execution
```json
{
  "runner": "benchmark_execute.py run-dispatch",
  "started_at": "2026-04-01T21:35:11.566567Z",
  "finished_at": "2026-04-01T21:35:14.181377Z",
  "duration_ms": 2614,
  "http_status": 429,
  "endpoint": "https://api.z.ai/api/paas/v4/chat/completions",
  "request_payload_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "ce88ba876dd275f41db1d455aefa35d0cf917dde5befd0419eb3bc659ebc51e7",
  "prompt_bundle_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "4fb5ef538368169b5d4571dd87a02f5e9a93011822f22e40331ceb898aeb4ad8",
  "request_bytes": 3660,
  "response_bytes": 99,
  "response_content_type": "application/json; charset=UTF-8",
  "error": "{\"error\":{\"code\":\"1113\",\"message\":\"Insufficient balance or no resource package. Please recharge.\"}}"
}
```


## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
- `executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json` (response-raw-json)
