# Provider Dispatch: glm-5.1--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `glm-5.1`
- Result: `glm-5.1--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Provider Profile: `zai-openai-compatible`
- Tool Profiles: `zai-claude-code-bridge`
- Execution Channel: `manual-or-api`
- Transport: `openai-compatible`
- Status: `prepared`
- Request Bundle: `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:33:19.581155Z`

## Invocation
```json
{
  "kind": "http-api",
  "endpoint": "https://api.z.ai/api/paas/v4/chat/completions",
  "api_key_hint": "$ZAI_API_KEY",
  "suggested_command": "bash executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh"
}
```

## Request Contract
```json
{
  "prompt_bundle_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md",
  "prompt_bundle_hash": "ae2e7f071c7fa616da61825ae4a530c8e9d6b84a0cd1197937a535224cdb655b",
  "request_payload_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json",
  "request_payload_hash": "13a828a88edf827807f651a3451c5d6da8356c92cd3c432989c14719e4ec2fc6",
  "response_placeholder_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json"
}
```

## Response Contract
```json
{
  "raw_response_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json",
  "fallback_text_response_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.txt",
  "normalized_response_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.normalized.json",
  "extracted_text_path": "executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.text.md",
  "generated_manifest_path": "executions/output/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/generation_manifest.json",
  "ingest_command": "python benchmark_execute.py ingest-response --dispatch executions/dispatches/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json"
}
```


## Request Artifacts
- `executions/dispatches/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/glm-5.1/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)
