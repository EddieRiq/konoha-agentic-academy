# Git Operation Boundary

Status: public planning boundary.

Konoha does not currently include an executable Git operation runtime.

This guide defines the boundary for any future component that may stage files, commit, push, create tags, publish releases, modify branches, or interact with remotes.

## Purpose

Git operations are high-impact actions because they can publish content, change history, expose private context, trigger CI, or create public release artifacts.

A future runtime must treat Git operations as explicit, reviewable, reversible workflow steps. They must never happen merely because an adapter, worker, model, or tool is technically able to run Git commands.

## Core rule

Technical capability is not authorization.

A future runtime may only perform a Git operation when all of the following are true:

- a Mission Charter explicitly allows the operation;
- the exact Git operation is listed in scope;
- the working tree state has been captured;
- private-boundary checks have passed;
- expected files are reviewed;
- execution gate approval is recorded;
- rollback or recovery notes exist;
- the user has approved the operation when required.

## Git operation classes

### Read-only Git operations

Examples:

```text
git status
git diff
git log
git branch --show-current
git tag -l
git ls-files
git check-ignore -v <path>
```

Read-only Git operations may be allowed for diagnostics when the Mission Charter permits repository inspection.

They must not be used to infer permission for mutation.

### Staging operations

Examples:

```text
git add <path>
git restore --staged <path>
```

Staging operations require explicit path scope.

A runtime must not stage broad paths such as `.` unless the Mission Charter explicitly authorizes that scope and the evidence pack shows why it is safe.

### Commit operations

Examples:

```text
git commit -m "<message>"
```

Commit operations require:

- reviewed diff;
- commit message;
- files list;
- no private-boundary violations;
- no unexpected generated files;
- approval recorded.

### Push operations

Examples:

```text
git push
git push origin <branch>
```

Push operations require:

- clean review of local commits;
- remote target;
- branch target;
- no accidental tags;
- approval recorded.

A runtime must not push private branches, local experiments, credentials, generated outputs, or local Village content.

### Tag operations

Examples:

```text
git tag -a vX.Y.Z -m "<message>"
git push origin vX.Y.Z
```

Tags require release readiness review.

A tag must not be created until:

- version intent is explicit;
- changelog is updated;
- safety checks pass;
- private-boundary checks pass;
- release notes are drafted;
- user approval is recorded.

### Release operations

Publishing a GitHub/GitLab release requires explicit release authorization.

A runtime must not publish releases automatically.

Release publishing requires:

- tag exists and points to intended commit;
- release notes reviewed;
- pre-release or stable status is explicit;
- no private files are included;
- user approval is recorded.

### History-changing operations

Examples:

```text
git rebase
git reset --hard
git push --force
git filter-repo
git filter-branch
```

These are blocked by default.

They require exceptional approval and a dedicated recovery plan.

## Blocked by default

A future runtime must block these unless explicitly authorized by a high-trust Mission Charter and reviewed evidence:

```text
git push --force
git reset --hard
git clean -f -d
git clean -xdf
git rebase
git tag -d
git push origin :<branch>
git push origin --delete <branch>
git config --global
git credential approve
git credential fill
```

## Private-boundary requirements

Before any Git mutation, the runtime must check that private content is not staged or about to be published.

At minimum:

```text
git status
git diff --stat
git diff --cached --stat
git ls-files alliance/<village>
git check-ignore -v alliance/<village>/test.md
```

For local Villages, expected behavior is:

```text
git ls-files alliance/<village>
```

returns no files.

## Required evidence before mutation

A Git operation request must include:

- repository path;
- current branch;
- remote target;
- operation type;
- exact command or API action;
- files affected;
- diff summary;
- private-boundary check;
- approval status;
- rollback notes.

## Required evidence after mutation

A Git operation result must include:

- command executed;
- exit status;
- output summary;
- new `git status`;
- new commit/tag hash if applicable;
- changed remote state if applicable;
- unexpected changes;
- follow-up actions.

## Stop conditions

Stop before Git mutation if:

- Mission Charter does not authorize Git operations;
- the command is not listed exactly;
- path scope is broad or ambiguous;
- private files may be staged;
- local Village content may be exposed;
- release/tag intent is unclear;
- remote branch is unclear;
- working tree contains unexpected changes;
- rollback plan is missing;
- user approval is required but not recorded.

## Non-goals

This boundary does not implement:

- Git command execution;
- GitHub/GitLab API integration;
- release publishing;
- branch protection management;
- CI/CD triggering;
- credentials management.

## Relationship to other doctrine

Git operation work must comply with:

- Mission Charter requirements;
- adapter permission matrix;
- adapter invocation contract;
- execution gate;
- evidence pack;
- dry-run protocol;
- runtime planning baseline;
- command runner boundary;
- filesystem mutation boundary;
- public/private boundary.

If there is a conflict, the stricter rule wins.

## Runtime readiness requirement

Before implementing Git operation runtime behavior, complete a Git operation readiness review.

A runtime must remain planning-only until readiness is approved.
