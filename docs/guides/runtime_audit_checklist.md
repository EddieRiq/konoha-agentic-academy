# Runtime Audit Checklist

Status: public documentation-first checklist.

This checklist is used before tagging or publishing a runtime-planning release, and before any future work proposes executable runtime behavior.

It does not authorize execution. It only helps reviewers verify that runtime documentation, templates, boundaries, and public/private safety rules are coherent.

## Purpose

The Runtime Audit Checklist verifies that runtime planning remains:

- documentation-first;
- non-executing;
- explicit about boundaries;
- safe for public release;
- consistent with Konoha laws, Mission Charter requirements, approval policy, adapter contracts, eval boundaries, and local/private context rules.

## Scope

Use this checklist when reviewing:

- runtime planning documentation;
- command runner boundary documentation;
- filesystem mutation boundary documentation;
- Git operation boundary documentation;
- rollback boundary documentation;
- runtime lifecycle documentation;
- runtime templates;
- runtime-related Scrolls;
- release candidates that mention runtime behavior.

## Non-goals

This checklist does not:

- implement runtime;
- approve command execution;
- approve filesystem mutation;
- approve Git operations;
- approve adapter runtime integration;
- approve access to private Villages;
- replace Mission Charter, approval, review, evidence, or teachback requirements.

## Checklist

### 1. Release state

- [ ] The release clearly states whether runtime is planning-only or executable.
- [ ] No document claims that autonomous runtime execution exists if it does not.
- [ ] The release notes include a safety boundary.
- [ ] The release notes state that technical capability is not authorization.
- [ ] The release is marked pre-release when runtime remains documentation-first alpha.

### 2. Runtime files

- [ ] `runtime/README.md` exists.
- [ ] `docs/guides/runtime_planning_baseline.md` exists.
- [ ] `docs/guides/command_runner_boundary.md` exists.
- [ ] `docs/guides/filesystem_mutation_boundary.md` exists.
- [ ] `docs/guides/git_operation_boundary.md` exists.
- [ ] `docs/guides/rollback_boundary.md` exists.
- [ ] `docs/guides/runtime_lifecycle.md` exists.
- [ ] Runtime templates exist under `runtime/templates/`.
- [ ] Runtime review Scrolls exist under `scrolls/`.

### 3. Boundary consistency

- [ ] Command execution requires explicit authorization.
- [ ] Filesystem mutation requires explicit authorization.
- [ ] Git operations require explicit authorization.
- [ ] Rollback expectations are documented before risky behavior.
- [ ] Runtime closure requires evidence and validation.
- [ ] No runtime document bypasses Mission Charter requirements.
- [ ] No runtime document allows adapter capability to become authorization.

### 4. Evidence consistency

- [ ] Runtime plans require scope.
- [ ] Runtime plans require allowed paths or explicit no-path scope.
- [ ] Runtime plans require expected commands or explicit no-command scope.
- [ ] Runtime results require evidence.
- [ ] Runtime closure reports residual risk.
- [ ] Runtime closure reports validation.
- [ ] Runtime closure includes teachback or user-facing explanation.

### 5. Privacy and local boundaries

- [ ] Public runtime docs do not mention real private Village content.
- [ ] Public runtime docs do not include private paths except generic placeholders.
- [ ] Public runtime docs do not include private source names, private book names, converted source content, credentials, tokens, or local memory.
- [ ] Local Villages remain ignored by Git.
- [ ] Runtime docs do not instruct users to commit local virtual environments, local locks, private sources, or private outputs.

### 6. Git safety

- [ ] No runtime doc permits automatic `git add`.
- [ ] No runtime doc permits automatic `git commit`.
- [ ] No runtime doc permits automatic `git push`.
- [ ] No runtime doc permits automatic tag or release creation.
- [ ] Any future Git operation requires explicit scope, evidence, approval, and rollback awareness.

### 7. Stop conditions

- [ ] The checklist identifies stop conditions for ambiguous scope.
- [ ] The checklist identifies stop conditions for private context.
- [ ] The checklist identifies stop conditions for unapproved commands.
- [ ] The checklist identifies stop conditions for unapproved file mutation.
- [ ] The checklist identifies stop conditions for unapproved Git operations.
- [ ] The checklist identifies stop conditions for missing rollback plan when risk exists.

## Suggested audit commands

These commands are examples for local manual review.

```powershell
git status
git log --oneline --decorate -12
```

Check tracked runtime files:

```powershell
git ls-files runtime docs/guides scrolls | Select-String -Pattern "runtime|command_runner|filesystem_mutation|git_operation|rollback"
```

Check for private leakage markers:

```powershell
git grep -n "Effective-Python-Brett-Slatkin\|Brett Slatkin\|Praise for Effective Python\|alliance/kirigakure/private-library/books/effective-python\|kirienv" -- .
```

Check local Village boundary:

```powershell
git ls-files alliance/kirigakure
git check-ignore -v alliance/kirigakure/.venv/pyvenv.cfg
```

## Verdict

Use one of:

- Pass;
- Pass with notes;
- Needs changes;
- Blocked.

## Blocking conditions

Block release or runtime promotion if:

- executable runtime is implied but not implemented;
- runtime is allowed to execute commands without explicit approval;
- filesystem mutation is allowed without explicit scope;
- Git operations are allowed without explicit approval;
- rollback expectations are missing for risky behavior;
- private Village content appears in tracked files;
- credentials, secrets, private source content, or local memory appear in tracked files.
