# Proposal: Add Provider Dispatch Bundles

## Why

The repository can now create packets, plans, results, and runs, but it still lacks a first-class dispatch package that a human or tool can execute against a provider.

That is the last missing control-plane step before real generations.

## What Changes

- add an OpenSpec capability for provider dispatch bundles
- add an execution CLI command to prepare dispatch from an existing result
- store dispatch metadata and instructions inside the result output bundle
- validate dispatch bundle files when present

## Expected Outcome

An engineer can prepare a provider-specific request package without spending usage yet, then run the actual generation using the exact bundle and capture the response back into the existing result lifecycle.
