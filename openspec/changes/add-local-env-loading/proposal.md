# Proposal: Add Local Env Loading

## Why

The benchmark repo currently expects provider credentials to be present in the process environment. In practice, engineers keep benchmark keys in `.env.local`, which means auth checks, readiness reports, and generated dispatch scripts do not automatically see configured credentials.

That creates avoidable friction exactly where the workflow should be lowest-overhead.

## What Changes

- Add repository-native `.env.local` and `.env` loading to the shared auth surface.
- Make generated provider dispatch scripts source local env files automatically.
- Ignore local env files in git.
- Add tests that prove env-file-backed auth readiness works.

## Expected Outcome

An engineer can place credentials in `.env.local` and immediately use `auth-status`, `readiness-report`, and generated `curl.sh` bundles without extra export steps.
