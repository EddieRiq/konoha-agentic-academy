# Runtime Package Manifest Template

## Status

Template.

Use this file to declare the contents, scope, and status of a dry-run runtime package.

## Package identity

- Package ID:
- Mission ID:
- Mission title:
- Created by:
- Created at:
- Last updated:
- Current status: `draft | ready_for_validation | revision_required | blocked | ready_for_review | reviewed_no_execution | deprecated`
- Supersedes package ID:
- Superseded by package ID:

## Authority statement

This package is dry-run only.

It does not authorize:

- shell command execution;
- filesystem mutation;
- Git operations;
- adapter execution;
- private context access;
- release publication;
- doctrine changes;
- autonomous mission expansion.

## Mission binding

- Mission Charter reference:
- Approved scope summary:
- Explicit non-goals:
- Required approvals:
- Human owner:
- Review owner:
- Execution allowed: `no`
- Execution gate required for future action: `yes | no | not_applicable`

## Package artifacts

| Artifact type | Path or reference | Required | Present | Status | Notes |
|---|---|---:|---:|---|---|
| Mission Charter |  | yes |  |  |  |
| Mission intake |  | yes |  |  |  |
| Dry-run execution plan |  | yes |  |  |  |
| Adapter invocation stub |  | conditional |  |  |  |
| Evidence collection stub |  | conditional |  |  |  |
| Runtime state |  | yes |  |  |  |
| Runtime validation checklist |  | yes |  |  |  |
| Runtime validation report |  | yes |  |  |  |
| Runtime trace log |  | yes |  |  |  |
| Runtime trace events |  | conditional |  |  |  |
| Model routing decision |  | conditional |  |  |  |
| Context budget |  | conditional |  |  |  |
| Token usage report |  | conditional |  |  |  |
| Token budget enforcement |  | conditional |  |  |  |
| Capability review |  | conditional |  |  |  |
| Capsule manifest |  | conditional |  |  |  |
| Capsule refresh report |  | conditional |  |  |  |
| Review Scroll output |  | yes |  |  |  |
| Closure report |  | yes |  |  |  |

## Context and source boundaries

- Public-only context:
- Local/private context requested:
- Local/private context approved:
- Capsule-first use:
- Full-source fallback required:
- Sensitive paths present:
- Sensitive paths intentionally excluded:
- Redaction required:

## Model and token governance

- Proposed model tier:
- Reviewer model tier:
- Lowest sufficient tier rationale:
- Escalation triggers:
- Demotion candidates:
- Context budget reference:
- Token budget reference:
- Overage allowed: `no | conditional`
- Overage justification reference:

## Validation summary

- Validation outcome: `valid_for_review | conditional_revision_required | blocked`
- Validation report reference:
- Required revisions:
- Blocking issues:
- Reviewer notes:

## Trace summary

- Trace log reference:
- Number of trace events:
- Supersession records:
- Open blockers:
- Evidence gaps:

## Closure readiness

- Package ready for human review: `yes | no`
- Package ready for future execution gate: `no | conditional`
- Teachback prepared: `yes | no`
- User-facing explanation prepared: `yes | no`
- Remaining risks:

## Final note

Completing this manifest does not authorize execution.

It only declares whether the dry-run runtime package is complete enough for review.
