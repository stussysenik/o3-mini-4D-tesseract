# Provider Profiles

This directory is the single source of truth for credential and transport profiles.

- `registry.json` defines API and tooling profiles.
- Profiles describe required environment variables, optional variables, derived config, and documentation links.
- Model entries in `models/registry.json` reference these profiles instead of duplicating auth rules.

Current supported families:
- OpenAI Responses API and Codex workspace flows
- Anthropic Messages API and Claude Code
- Z.AI / GLM openai-compatible API and Claude Code bridge
- NVIDIA NIM endpoint and container access

Credential lookup order is:
- process environment
- `.env.local`
- `.env`

Generated API dispatch scripts source `.env.local` or `.env` from the repo root automatically before making provider requests.
