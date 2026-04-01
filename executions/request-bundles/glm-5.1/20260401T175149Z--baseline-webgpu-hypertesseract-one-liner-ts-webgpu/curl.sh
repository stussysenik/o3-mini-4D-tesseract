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

if [ -z "${ZAI_API_KEY:-}" ]; then echo "Missing ZAI_API_KEY. Set it in the environment or $repo_root/.env.local" >&2; exit 1; fi

request_path="$repo_root/executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/request.json"
response_path="$repo_root/executions/request-bundles/glm-5.1/20260401T175149Z--baseline-webgpu-hypertesseract-one-liner-ts-webgpu/response.raw.json"

curl -sS 'https://api.z.ai/api/paas/v4/chat/completions' \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "content-type: application/json" \
  --data "@$request_path" \
  --output "$response_path"

printf 'Wrote raw response to %s\n' "$response_path"
