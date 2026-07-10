# Sandbox Evidence Hygiene

## Purpose

Konoha writes local mission sessions, audit reports, Git Gate evidence and smoke outputs under `sandbox/`.
Those artifacts are useful local evidence, but they are not public source files and must not be staged by accident.

## Public allowlist

Only these files are intentionally tracked:

```text
sandbox/README.md
sandbox/tmp/.gitkeep
sandbox/worktrees/.gitkeep
```

Everything else under `sandbox/` is local runtime evidence.

## Safety

- Existing reports are not deleted.
- Sandbox evidence is not permission.
- Public examples must be deliberately sanitized.
- Private memory remains local.
- Git stage, commit, push, tag and release remain separately approved.

## Verification

```bash
git check-ignore -v sandbox/hokage-shell
git check-ignore -v sandbox/v3-1-1-hokage-shell-review-panels.json
git ls-files sandbox
git status --short
```
