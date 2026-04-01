# Design

## Agent Capture

Workspace-agent and code-agent transports do not expose the same request telemetry as direct HTTP APIs, so the repository should record an explicit provenance block with:

- runner label
- approximate start and finish timestamps
- duration
- transport identity
- prompt bundle path and hash
- response byte count
- explicit notes that token and billing telemetry are unavailable

The capture flow writes the raw text response into the canonical dispatch bundle location and then reuses existing response ingestion logic.

## Latest Showcase Resolution

Showcase generation should not require engineers to hunt for result JSON paths. The resolver scans result bundles for a given model id, target id, and optional reasoning effort, then picks the latest relevant match using captured or created timestamps.

By default scaffolded results are excluded. Engineers can opt into scaffolded fallback when comparing an executed lane against a still-pending lane.
