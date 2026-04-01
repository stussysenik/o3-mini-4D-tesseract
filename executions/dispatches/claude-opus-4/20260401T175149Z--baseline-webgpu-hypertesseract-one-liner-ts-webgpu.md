# Provider Dispatch: claude-opus-4--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `claude-opus-4`
- Result: `claude-opus-4--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `anthropic-messages`
- Tool Profiles: `claude-code-native`
- Execution Channel: `api`
- Transport: `messages-api`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:51:49.637640Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.anthropic.com/v1/messages",
  "api_key_hint": "$ANTHROPIC_API_KEY",
  "suggested_command": "bash executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "b573e292201043cfe7639b743de5aa9026aaadb6ffe5a5a24f16de7ea68361a4",
  "request_payload_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "7a9ebe830e05281c9bd557f8dc8b4748532614f9da81cb99ead6a82f0aeed4c2",
  "response_placeholder_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/claude-opus-4/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
