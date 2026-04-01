# Provider Dispatch: gpt-5.3-codex-spark--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `gpt-5.3-codex-spark`
- Result: `gpt-5.3-codex-spark--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `openai-responses`
- Tool Profiles: `codex-workspace`
- Execution Channel: `workspace-agent`
- Transport: `responses-api`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:51:49.574530Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.openai.com/v1/responses",
  "api_key_hint": "$OPENAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "8e4b04b29dc78c839125861920c69f7223ef8824f103e84e874926ce9d93ca35",
  "request_payload_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "a96334024a3d57ca4275faa9426870af2b5b499c022c7bb13335d353d51c556d",
  "response_placeholder_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/gpt-5.3-codex-spark/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
