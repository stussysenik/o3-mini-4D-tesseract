# Proposal: Add Generation Readiness Bootstrap

## Why

The repository can now represent the full packet-to-dispatch lifecycle, but only one model lane has actually been prepared.

Before any real generations are run, we need a repeatable way to:
- prepare every model lane
- reuse existing artifacts when possible
- report which models are genuinely runnable right now

## What Changes

- add a generation-readiness spec
- add execution CLI support to bootstrap packets, plans, results, and dispatches for model sets
- add a readiness report that combines artifact availability with current auth status
- seed artifacts across the existing benchmark matrix

## Expected Outcome

The repository becomes operationally ready for real generation runs across the configured model set, not just for a single manually prepared lane.
