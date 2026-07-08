# Product Runtime Bootstrap Review Scroll

## Review goal

Review whether the Product Runtime Bootstrap keeps Konoha easy to operate without weakening the v1.0 safety model.

## Evidence to inspect

- Product bootstrap CLI output.
- Product doctor report.
- Workspace manifest.
- Mission Charter skeleton.
- Mission manifest.
- Config validation output.
- Delegated dry-run workflow output.

## Required confirmations

Confirm:

- workspace writes stay under the approved workspace root;
- default workspace remains inside sandbox;
- mission IDs reject path traversal;
- generated Mission Charters do not imply approval;
- doctor remains read-only;
- config validation does not execute tools;
- `run dry-run` delegates only to the allowlisted mission workflow;
- Git writes remain blocked;
- real adapters remain blocked;
- private context remains blocked;
- network access remains blocked.

## Blockers

Block release if:

- workspace paths can escape the repo root;
- mission IDs can contain path separators;
- the CLI stages, commits, pushes, cleans, or resets Git state;
- the CLI invokes real adapters;
- the CLI uses network access;
- the CLI reads private Village context;
- the CLI turns generated Charters into implicit approvals;
- UI files are introduced without prior UI draft approval.
