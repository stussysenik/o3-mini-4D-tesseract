# Execution Result: gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Metadata
- Model: `gpt-5.1-codex-max`
- Plan: `gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Packet: `gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Execution Mode: `plan-only`
- Status: `scaffolded`
- Output Root: `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Created At: `2026-04-01T17:51:49.591754Z`

## Summary
Scaffolded output bundle for execution plan gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.

## Benchmark Report
```json
{
  "report_version": 1,
  "result_id": "gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu",
  "benchmark_id": "webgpu-hypertesseract-v1",
  "generation_kind": "one-liner",
  "target_id": "ts-webgpu",
  "target_language": "ts",
  "runtime": "browser",
  "lane": "primary",
  "used_capabilities": [
    "html",
    "css",
    "dom",
    "webgpu",
    "wgsl"
  ],
  "requested_locales": [
    "en"
  ],
  "wasm_used": false,
  "webgpu_used": true,
  "fallback_path": "undeclared",
  "known_gaps": [
    "Generated implementation files have not been attached yet.",
    "Benchmark scoring has not been completed yet."
  ],
  "hypothesis": "This prompt packet should produce a browser-native hypertesseract scene that is valid for later benchmark scoring.",
  "method": "Use the execution plan as the authoritative dispatch contract, store the raw output bundle here, and score only after review.",
  "result_summary": "Scaffolded result bundle created. Awaiting generated files and review.",
  "limitations": [
    "This is a scaffolded artifact, not a scored benchmark run.",
    "Provider execution has not been captured in this record yet."
  ],
  "next_steps": [
    "Run the linked dispatch bundle and ingest the provider response via benchmark_execute.py ingest-response.",
    "Capture screenshots or recordings under executions/output/.../captures/.",
    "Update this report after review, then create a scored benchmark run if warranted."
  ],
  "score_ready": false,
  "scoring_status": "pending-review",
  "recommended_run_conditions": {
    "generation_kind": "one-liner",
    "target_id": "ts-webgpu",
    "prompt_packet_id": "gpt-5.1-codex-max--20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu",
    "prompt_revision": "v0",
    "scene_seed": "seed-001",
    "toolchain": "manual",
    "shader_strategy": "webgpu-native",
    "geometry_strategy": "procedural",
    "wasm_enabled": false,
    "multilingual_scope": "en"
  }
}
```

## Review State
```json
{
  "score_ready": false,
  "linked_run_id": null,
  "linked_run_path": null
}
```

## Artifacts
- `executions/results/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (execution-result)
- `executions/results/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (execution-result-doc)
- `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/README.md` (output-bundle-doc)
- `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/benchmark_report.json` (benchmark-report)
- `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/bundle_manifest.json` (output-bundle-manifest)
- `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/captures/README.md` (capture-output-slot)
- `executions/output/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/generated/README.md` (generated-output-slot)
- `executions/dispatches/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.json` (dispatch-record)
- `executions/dispatches/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu.md` (dispatch-record-doc)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/curl.sh` (curl-script)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/dispatch_manifest.json` (dispatch-manifest)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/invocation.md` (invocation-doc)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/prompt_bundle.md` (prompt-bundle)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json` (request-payload)
- `executions/request-bundles/gpt-5.1-codex-max/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.placeholder.json` (response-placeholder)

## OpenSpec References
- `openspec/specs/model-registry/spec.md`
- `openspec/specs/prompt-packet-lifecycle/spec.md`
- `openspec/specs/execution-orchestration/spec.md`
- `openspec/specs/provider-auth/spec.md`
- `openspec/changes/add-dspy-openspec-execution`
- `openspec/specs/execution-results/spec.md`
- `openspec/changes/add-execution-results-layer`

## Notes
- Execution results are the durable layer between plans and scored benchmark runs.
- This artifact is scaffold-first so provider-backed generations can be attached later without losing provenance.
- Dispatch bundle created for profile openai-responses.
