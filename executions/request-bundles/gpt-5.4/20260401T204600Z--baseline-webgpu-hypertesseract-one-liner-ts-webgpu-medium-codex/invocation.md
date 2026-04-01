# Invocation: gpt-5.4--20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex

## Transport
- Kind: `manual-handoff`
- Provider Profile: `codex-workspace`
- Transport: `workspace-agent`
- Model: `gpt-5.4`
- Endpoint: not portable across clients; use the configured tool or workspace bridge.
- Auth: `provider-specific auth`

## Tool Profiles
- `codex-workspace`: Uses the current coding workspace agent channel rather than direct provider API credentials.

## Recommended Execution
- Prompt bundle: `executions/request-bundles/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex/prompt_bundle.md`
- Request payload: not emitted for this transport; use the prompt bundle plus invocation notes.
- Raw response target: place the provider output in a text or JSON file, then pass it to `ingest-response --source`.
- Suggested command: Use the prompt bundle plus provider/tool config in your preferred client.
- After generation, run `python benchmark_execute.py ingest-response --dispatch executions/dispatches/gpt-5.4/20260401T204600Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu-medium-codex.json`.
