# Git Commit Gate

Status: pre-release / Git commit gate alpha.

The Git Commit Gate is the first controlled commit boundary for Konoha Agentic Academy.

It may create a Git commit only from files that are already staged, already allowlisted, and explicitly approved by a human approval token.

It is not Git automation. It is not a mission executor.

## Purpose

The gate separates three actions that must remain distinct:

1. proposing changes;
2. staging allowlisted files;
3. committing already staged allowlisted files.

This release only covers the third action.

The gate does not stage files. Staging remains delegated to the Git Staging Gate.

## Command

Preview mode:

```powershell
python .\tools\git_commit\create_git_commit.py `
  --repo-root "." `
  --message "Add safe docs update"
```

Confirmed commit:

```powershell
python .\tools\git_commit\create_git_commit.py `
  --repo-root "." `
  --message "Add safe docs update" `
  --confirm-commit `
  --approval-token "COMMIT_STAGED_ALLOWLISTED_FILES"
```

## Required approval

Confirmed commit requires:

```text
COMMIT_STAGED_ALLOWLISTED_FILES
```

Without this exact token, the gate must fail.

## Allowed behavior

The gate may:

- inspect the Git repository root;
- inspect Git status;
- inspect already staged files;
- reject private or unsafe staged paths;
- preview a commit request;
- run `git commit -m <message>` only after explicit approval;
- print a text or JSON report.

## Blocked behavior

The gate may not:

- stage files;
- run `git add`;
- run `git push`;
- run `git clean`;
- run `git reset`;
- rewrite history;
- amend commits;
- execute mission actions;
- invoke adapters;
- access private Village context;
- authorize runtime actions.

## Commit message policy

The commit message must be:

- single-line;
- non-empty;
- no more than 120 characters;
- free from unsupported shell/control characters.

This gate is intentionally conservative.

## Path policy

Every staged path must be allowlisted.

Private or local-only paths are blocked, including:

- `alliance/kirigakure/`;
- private libraries;
- local memory;
- vaults;
- credentials;
- `.env`;
- virtual environments;
- caches.

## Dirty working tree policy

By default, unstaged or untracked changes block the commit. This prevents committing in a confusing state.

`--allow-dirty` may be used only after review. It does not relax staged path validation.

## Relationship to earlier gates

The expected sequence is:

```text
proposed artifact workflow
→ human-approved apply plan
→ Git read-only gate
→ Git staging gate
→ Git commit gate
```

The commit gate does not replace any previous gate.

## Review evidence

A reviewer should verify:

- staged paths are explicit and allowlisted;
- no private paths are staged;
- commit message is appropriate;
- approval token was intentionally provided;
- no push occurred;
- no mission execution occurred.
