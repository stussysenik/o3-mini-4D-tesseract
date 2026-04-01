# Prompt Bundle: claude-opus-4--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu

## Dispatch Context
- Model: `claude-opus-4`
- Provider Model: `claude-opus-4-0`
- Provider Profile: `anthropic-messages`
- Tool Profiles: `claude-code-native`
- Result: `claude-opus-4--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Plan: `claude-opus-4--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Packet: `claude-opus-4--20260401T173319Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu`
- Target: `ts-webgpu`
- Capabilities: `html, css, dom, webgpu, wgsl`
- Locales: `en`

## System Prompt

```text
# Tesseract Benchmark System Prompt

You are generating artifacts for a longitudinal 3D frontend benchmark.

Follow these rules:
- Respect the declared target language, runtime, and benchmark lane.
- Favor browser-native delivery for primary-lane work.
- Use only the selected capabilities unless a fallback is explicitly justified.
- Keep the implementation self-contained and runnable with minimal setup.
- Do not silently swap to a different language or runtime.
- Be explicit about whether WebGPU is used.
- Be explicit about whether WASM is used and why.
- Avoid fake claims about performance, multilingual support, or visual fidelity.

Always return these sections in order:
1. `Implementation Summary`
2. `Target Declaration`
3. `Capability Declaration`
4. `Files`
5. `Benchmark Report`
6. `Known Limitations`

Inside `Benchmark Report`, include a machine-readable JSON block with:
- `target_id`
- `target_language`
- `runtime`
- `lane`
- `used_capabilities`
- `requested_locales`
- `wasm_used`
- `webgpu_used`
- `fallback_path`
- `known_gaps`

If the prompt is underspecified, make the smallest reasonable assumption and state it in `Known Limitations` instead of asking for clarification.
```

## Scene Prompt

```text
# WebGPU Hypertesseract Benchmark v1

Build a browser-native visual benchmark scene centered on a hypertesseract or tesseract-derived object.

Scene requirements:
- The scene must feel like a modern high-end graphics demo rather than a classroom wireframe.
- Geometry, motion, lighting, and composition should communicate higher-dimensional structure.
- The implementation should visibly justify the use of WebGPU when WebGPU is selected.
- If WASM is selected, its role must be specific and defensible, for example geometry generation, simulation, or data processing.
- The UI should include a compact benchmark/report surface showing target, capabilities, locales, and known limitations.
- The scene should remain self-contained without external asset downloads unless explicitly allowed later.

Benchmark intent:
- Compare how different models synthesize ambitious graphics prompts.
- Preserve reproducibility through explicit capability declarations.
- Make multilingual UX visible rather than hidden in code comments.
```

## User Prompt

```text
Build a self-contained TypeScript + WebGPU Hypertesseract v1 benchmark scene with visual fidelity, shader clarity, and benchmark honesty, a precise luminous sci-fi look, procedural hypertesseract wireframe with volumetric cues, ambient orbit plus subtle pointer interaction, support for en, and a compact scientific benchmark panel that clearly states WebGPU/WASM usage and limitations.
```
