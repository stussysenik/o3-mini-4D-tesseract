# Invocation: glm-5.1--20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Transport
- Kind: `http-api`
- Provider Profile: `zai-openai-compatible`
- Transport: `openai-compatible`
- Model: `glm-5.1`
- Endpoint: `https://api.z.ai/api/paas/v4/chat/completions`
- Auth: `$ZAI_API_KEY`

## Tool Profiles
- `zai-claude-code-bridge`: Official Z.AI quick start for Claude Code uses ANTHROPIC_AUTH_TOKEN plus ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic.

## Recommended Execution
- Prompt bundle: `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md`
- Request payload: `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json`
- Raw response target: `executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json`
- Suggested command: `bash executions/request-bundles/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh`
- After generation, run `python benchmark_execute.py ingest-response --dispatch executions/dispatches/glm-5.1/20260401T172343Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json`.
