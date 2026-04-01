# Invocation: gpt-5.1-codex-mini--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Transport
- Kind: `http-api`
- Provider Profile: `openai-responses`
- Transport: `responses-api`
- Model: `gpt-5.1-codex-mini`
- Endpoint: `https://api.openai.com/v1/responses`
- Auth: `$OPENAI_API_KEY`

## Tool Profiles
- `codex-workspace`: Uses the current coding workspace agent channel rather than direct provider API credentials.

## Recommended Execution
- Prompt bundle: `executions/request-bundles/gpt-5.1-codex-mini/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md`
- Request payload: `executions/request-bundles/gpt-5.1-codex-mini/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json`
- Raw response target: `executions/request-bundles/gpt-5.1-codex-mini/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json`
- Suggested command: `bash executions/request-bundles/gpt-5.1-codex-mini/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh`
- After generation, run `python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.1-codex-mini/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json`.
