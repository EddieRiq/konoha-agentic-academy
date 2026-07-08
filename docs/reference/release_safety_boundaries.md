# Release Safety Boundaries

This document states the stable safety boundaries for Konoha Agentic Academy v1.0.0.

## Always blocked by default

- Real adapter execution.
- Network calls.
- Private Village context access.
- Autonomous shell execution.
- Autonomous mission execution.
- Git push.
- Git clean.
- Git reset.
- Git history rewrite.
- Background autonomous missions.

## Human approval required

- Applying proposed artifacts to allowlisted repository paths.
- Staging allowlisted files.
- Creating a commit from already staged allowlisted files.
- Mock adapter invocation through the adapter gate.

## Sandbox-only by default

- Dry-run runtime outputs.
- Mission workflow reports.
- Proposed artifact outputs.
- Mock adapter outputs.
- Integrated test reports.
- Dogfood reports.
- Release readiness reports.

## Stable release rule

A stable release is not closed by a tool. A tool may provide evidence. A human closes the release.


## Machine-readable boundary phrases

These phrases are intentionally stable because the v1.0 release-readiness checker verifies them exactly.

```text
Execution: blocked
Git operations
Private context access
Network access


