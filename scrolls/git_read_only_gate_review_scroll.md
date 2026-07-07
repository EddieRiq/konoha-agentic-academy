# Git Read-only Gate Review Scroll

Status: review Scroll / read-only gate alpha.

## Purpose

Review whether the Git Read-only Gate inspects repository state safely and without mutation.

## Required inputs

- Git Read-only Gate CLI.
- Git readiness report schema.
- Test results.
- Example report.
- Release audit output.

## Review checklist

### Read-only boundary

Confirm that the gate only uses read-only Git commands:

- `rev-parse --show-toplevel`;
- `status --porcelain=v1`;
- `diff --name-only`;
- `ls-files`;
- `check-ignore -v`.

Any command outside this list blocks the release.

### No mutation

Confirm that the gate does not:

- modify files;
- delete files;
- stage files;
- create commits;
- publish changes;
- invoke adapters;
- execute shell beyond the fixed Git read-only command wrapper;
- access private Village context.

### Dirty state handling

Confirm that:

- dirty repositories are blocked by default;
- `--allow-dirty` is documented as development-only;
- release audit does not use `--allow-dirty`.

### Private boundary

Confirm that tracked private or local-only paths are blockers.

The gate may check whether selected paths are ignored, but it must not read ignored private content.

### Report quality

Confirm that reports include:

- status;
- repo root;
- working tree entries;
- changed paths;
- tracked file count;
- private tracked paths;
- blockers;
- warnings;
- safety boundary fields.

## Approval outcome

Use one of:

- `approved_for_pre_release`;
- `revision_required`;
- `blocked`.

Passing this Scroll does not authorize Git write operations, mission execution, adapter execution, or private context access.
