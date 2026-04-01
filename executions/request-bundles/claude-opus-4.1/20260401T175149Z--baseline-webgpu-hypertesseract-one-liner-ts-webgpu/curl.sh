#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../../.." && pwd)"

if [ -f "$repo_root/.env.local" ]; then
  set -a
  . "$repo_root/.env.local"
  set +a
elif [ -f "$repo_root/.env" ]; then
  set -a
  . "$repo_root/.env"
  set +a
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then echo "Missing ANTHROPIC_API_KEY. Set it in the environment or $repo_root/.env.local" >&2; exit 1; fi

request_path="$repo_root/executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json"
response_path="$repo_root/executions/request-bundles/claude-opus-4.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json"

curl -sS 'https://api.anthropic.com/v1/messages' \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  --data "@$request_path" \
  --output "$response_path"

printf 'Wrote raw response to %s\n' "$response_path"
