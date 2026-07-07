# Git Staging Gate Review Scroll

Status: pre-release review Scroll.

## Purpose

Review whether a Git staging operation is safe, explicit, allowlisted, and human-approved.

This Scroll does not authorize commits, pushes, shell execution, adapter execution, private context access, or runtime actions.

## Required evidence

A reviewer must inspect:

- requested repo root;
- requested staging paths;
- normalized paths;
- allowlist match;
- blocked/private path checks;
- ignored-path checks;
- preview output;
- human approval evidence for confirmed staging;
- resulting staging report;
- absence of commit or push behavior.

## Review checklist

### 1. Scope

- [ ] The operation is staging only.
- [ ] No commit is requested.
- [ ] No push is requested.
- [ ] No clean/reset/rewrite operation is requested.
- [ ] The path list is explicit.

### 2. Path safety

- [ ] No absolute paths are present.
- [ ] No path traversal is present.
- [ ] No private or local-only paths are present.
- [ ] No ignored paths are staged.
- [ ] All paths are in the allowlist.

### 3. Approval

- [ ] Preview was available before staging.
- [ ] Confirmed staging used `--confirm-stage`.
- [ ] Confirmed staging used exact token `STAGE_ALLOWLISTED_FILES`.
- [ ] Approval evidence is recorded in the report.

### 4. Git boundary

- [ ] Only allowlisted read-only Git commands and explicit `git add -- <paths>` are used.
- [ ] No broad `git add .`, `git add -A`, or `git add --all` is used.
- [ ] No commit command exists.
- [ ] No push command exists.

### 5. Outcome

Allowed outcomes:

- `approved_for_staging`;
- `revision_required`;
- `blocked`.

## Stop conditions

Block if:

- any path is ambiguous;
- any path is private, ignored, local-only, or outside the allowlist;
- staging would be broad rather than explicit;
- approval is missing;
- the operation includes commit, push, reset, clean, or history rewrite;
- the reviewer cannot explain what will be staged.

## Closure

A staging gate review is complete only when the user can explain:

- which files were staged;
- why each file is allowlisted;
- which Git operations remained blocked;
- why staging does not authorize commit or push.
