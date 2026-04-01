# Design: Generation Readiness Bootstrap

## Summary

The execution CLI gains two operational commands:
- `bootstrap-readiness`
- `readiness-report`

They do not introduce a new lifecycle. They orchestrate the existing one.

## Bootstrap

For each model, bootstrap should:
1. create or reuse the latest packet
2. create or reuse the latest plan
3. create or reuse the latest result
4. create or reuse the latest dispatch

This should be idempotent for unchanged inputs.

## Reporting

The readiness report should show:
- model id
- execution channel
- latest packet path
- latest plan path
- latest result path and status
- latest dispatch path and status
- primary auth readiness
- tool auth readiness
- whether the lane is ready for actual generation now

## Why This Matters

The benchmark should not require hand-preparing each lane one by one before the first real comparison run.
