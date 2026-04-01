# Provider Dispatch: claude-opus-4.1--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `claude-opus-4.1`
- Result: `claude-opus-4.1--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `anthropic-messages`
- Tool Profiles: `claude-code-native`
- Execution Channel: `api`
- Transport: `messages-api`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:51:49.625403Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.anthropic.com/v1/messages",
  "api_key_hint": "$ANTHROPIC_API_KEY",
  "suggested_command": "bash executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "2498171232d5b6d4bc332443fadbc29c4e70813b0449eb5dc919c40a5b391839",
  "request_payload_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "da9b71b4b3def4f66e2ce59c2df880fb48453863a30daf61f55a09993e41a03c",
  "response_placeholder_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
