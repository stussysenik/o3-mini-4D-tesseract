# Provider Dispatch: gpt-5.3-codex--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `gpt-5.3-codex`
- Result: `gpt-5.3-codex--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `openai-responses`
- Tool Profiles: `codex-workspace`
- Execution Channel: `workspace-agent`
- Transport: `responses-api`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:33:19.595852Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.openai.com/v1/responses",
  "api_key_hint": "$OPENAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "6e4248b31a2ad8eafa9ad255b628683d40f4b1a0cff3ad8ebe2ece38359cd829",
  "request_payload_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "796223a9538eee5001767afb1bb4f8a4ec793ae2e248059bca7d6c2ebdf25101",
  "response_placeholder_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/gpt-5.3-codex/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
