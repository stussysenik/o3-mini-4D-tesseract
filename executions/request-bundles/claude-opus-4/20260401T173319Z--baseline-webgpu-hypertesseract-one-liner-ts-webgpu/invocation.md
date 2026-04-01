# Invocation: claude-opus-4--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Transport
- Kind: `http-api`
- Provider Profile: `anthropic-messages`
- Transport: `messages-api`
- Model: `claude-opus-4-0`
- Endpoint: `https://api.anthropic.com/v1/messages`
- Auth: `$ANTHROPIC_API_KEY`

## Tool Profiles
- `claude-code-native`: Native Claude Code configuration against Anthropic endpoints.

## Recommended Execution
- Prompt bundle: `executions/request-bundles/claude-opus-4/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md`
- Request payload: `executions/request-bundles/claude-opus-4/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json`
- Raw response target: `executions/request-bundles/claude-opus-4/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json`
- Suggested command: `bash executions/request-bundles/claude-opus-4/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh`
- After generation, run `python benchmark_execute.py ingest-response --dispatch executions/dispatches/claude-opus-4/20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json`.
