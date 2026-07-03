# Git Safety Scroll

```yaml
name: git_safety_scroll
version: 0.1.0
status: draft
type: scroll
risk_level: medium
default_mode: guarded
owner: Konoha Agentic Academy
```

## Purpose

This Scroll defines a safe workflow for Git operations inside a repository.

It is used when a mission needs to inspect Git state, stage files, create commits, amend commits, push branches, create branches, handle line endings, review diffs, or prepare changes for publication.

## Core rule

Git changes project history.

No agent may stage, commit, amend, reset, rebase, push, force-push, delete branches, change remotes, or publish repository content unless the action is explicitly allowed by an approved Mission Charter.

## Authority

This Scroll does not grant permission by itself.

It must operate under:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/mission-charter/mission_charter.md`
4. `protocols/context/context_policy.md`
5. `protocols/safety/safety_policy.md`
6. `protocols/approval/approval_policy.md`
7. `protocols/review/review_policy.md`
8. `sandbox/README.md`
9. `AGENTS.md`

If this Scroll conflicts with any higher authority document, the higher authority document wins.

## When to use this Scroll

Use this Scroll when the mission involves:

- checking repository status;
- reviewing diffs;
- staging files;
- committing changes;
- amending commits;
- creating or switching branches;
- pushing changes;
- handling merge conflicts;
- normalizing line endings;
- changing Git author identity;
- preparing a pull request or merge request;
- checking whether private files, credentials, generated outputs, or local assets may be published.

## When not to use this Scroll

Do not use this Scroll as permission to:

- modify files;
- publish private context;
- bypass review;
- hide generated files;
- rewrite public history casually;
- force-push without explicit approval;
- change Git configuration outside the mission scope;
- commit secrets or local Village content.

Those actions require explicit approval in the Mission Charter.

## Required inputs

A Git mission should define:

```yaml
repo_path: ""
mission_goal: ""
current_branch: ""
target_branch: ""
allowed_git_commands: []
forbidden_git_commands: []
allowed_paths: []
forbidden_paths: []
public_repo: true
sensitive_paths: []
commit_allowed: false
push_allowed: false
history_rewrite_allowed: false
expected_commit_message: ""
required_review_level: ""
```

If the branch, allowed commands, or publication rules are unclear, stop and ask.

## Default allowed actions

Unless the Mission Charter says otherwise, the agent may run read-only Git commands:

```bash
git status
git diff
git diff --stat
git diff --name-only
git log --oneline -n 5
git branch --show-current
git remote -v
git config --get user.name
git config --get user.email
```

The agent may summarize the output and identify risks.

## Default forbidden actions

Unless explicitly approved, the agent must not run:

```bash
git add
git commit
git commit --amend
git reset
git restore
git checkout
git switch
git branch -D
git rebase
git merge
git push
git push --force
git push --force-with-lease
git remote add
git remote set-url
git clean
```

Some of these commands are safe in specific contexts, but they are not safe by default.

## Git operation levels

### Level 0: Read-only inspection

Allowed with basic Mission Charter approval:

```bash
git status
git diff
git diff --stat
git log --oneline -n 5
git branch --show-current
git remote -v
```

Purpose:

- understand repository state;
- verify branch;
- review changes;
- detect untracked files;
- detect risky paths;
- prepare a report.

### Level 1: Local non-history setup

Requires explicit approval.

Examples:

```bash
git config user.name "Name"
git config user.email "email@example.com"
git config core.autocrlf false
```

Rules:

- prefer repository-local config unless the user asks for global config;
- do not expose private or workplace email in public repos without user confirmation;
- report the exact config changed.

### Level 2: Staging and committing

Requires explicit approval and a clean review of the diff.

Examples:

```bash
git add <paths>
git commit -m "Commit message"
```

Rules:

- stage specific paths when possible;
- avoid `git add .` unless the full diff was reviewed;
- do not commit secrets, local Village content, generated heavy outputs, logs, caches, or private assets;
- use a clear commit message;
- run `git status` after commit.

### Level 3: Publishing

Requires explicit approval.

Examples:

```bash
git push
git push origin <branch>
```

Rules:

- verify branch and remote before pushing;
- confirm the repo is safe for publication;
- confirm author identity;
- confirm no private content is included;
- prefer normal push over force push.

### Level 4: History rewrite or destructive cleanup

Requires explicit human approval and, when risk is medium or high, Jounin review or Kage Summit review.

Examples:

```bash
git commit --amend
git reset --hard
git rebase
git push --force-with-lease
git clean -fd
```

Rules:

- explain what will be rewritten or deleted;
- verify whether the commit was already pushed;
- prefer `--force-with-lease` over `--force` when a force push is explicitly approved;
- never rewrite shared history without explicit user confirmation.

## Standard workflow

### 1. Inspect state

Run:

```bash
git status
git branch --show-current
git remote -v
git diff --stat
```

Report:

```text
Current branch:
Remote:
Changed files:
Untracked files:
Risky files:
Recommended next action:
```

### 2. Review changes before staging

Run:

```bash
git diff
git diff --name-only
```

Check for:

- secrets;
- `.env`;
- tokens;
- private keys;
- local Village paths;
- personal data;
- generated outputs;
- caches;
- large binaries;
- copyrighted assets;
- accidental deletes;
- unrelated files.

If anything is suspicious, stop and ask.

### 3. Stage only approved files

Prefer:

```bash
git add path/to/file.md
```

Avoid:

```bash
git add .
```

Use `git add .` only when the Mission Charter allows it and the full file list was reviewed.

### 4. Commit

Before commit:

```bash
git status
```

Commit with a concise message:

```bash
git commit -m "Add mission templates"
```

After commit:

```bash
git status
git log --oneline -n 3
```

### 5. Push

Before push:

```bash
git status
git branch --show-current
git remote -v
git log --oneline -n 3
```

Then push only if approved:

```bash
git push
```

If the commit was amended after a previous push, use only with explicit approval:

```bash
git push --force-with-lease
```

## Public repository checks

Before publishing to a public repository, verify:

- no workplace email is unintentionally exposed;
- no company name appears unless intended;
- no credentials or tokens are present;
- no `.env` or config with secrets is tracked;
- no local private Village content is tracked;
- no private notes or working memory files are tracked;
- no internal screenshots, datasets, logs, or customer data are tracked;
- no franchise-specific or copyrighted assets are committed without license clearance;
- license file and README license statement match.

## Author identity

For public repositories, check identity before the first public push:

```bash
git config user.name
git config user.email
```

Use repository-local config when the identity should apply only to one repo:

```bash
git config user.name "Eduardo Riquelme"
git config user.email "example@example.com"
```

Use global config only when the user wants the identity to apply across repos:

```bash
git config --global user.name "Eduardo Riquelme"
git config --global user.email "example@example.com"
```

If the wrong identity was used in the latest local commit and the commit was not pushed, amend safely after approval:

```bash
git commit --amend --reset-author --no-edit
```

If the wrong identity was already pushed, stop and ask before rewriting history.

## Line endings

For Markdown-heavy public repositories, prefer consistent LF line endings.

Recommended `.gitattributes`:

```gitattributes
* text=auto eol=lf

*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
*.txt text eol=lf
*.sh text eol=lf
```

After adding `.gitattributes`, normalize only with approval:

```bash
git add .gitattributes
git add --renormalize .
git status
git diff --stat
git commit -m "Normalize line endings"
```

If there is nothing to commit, report it and do not invent a fix.

## Branch safety

Before changing branches:

```bash
git status
```

Rules:

- do not switch branches with uncommitted changes unless the user approves;
- do not delete branches without explicit approval;
- do not create long-lived branches without a clear purpose;
- name branches clearly.

Recommended branch names:

```text
docs/add-agent-entrypoint
docs/add-mission-templates
scrolls/add-git-safety-scroll
fix/readme-license
```

## Remote safety

Before pushing or changing remotes:

```bash
git remote -v
```

Rules:

- never change `origin` without explicit approval;
- never push to an unknown remote;
- never paste credentials into a remote URL;
- prefer HTTPS or SSH according to the user's setup;
- stop if the remote points to the wrong organization or account.

## Merge and rebase

Merges and rebases require explicit approval.

Before merge or rebase:

```bash
git status
git log --oneline --graph --decorate -n 10
```

Rules:

- do not rebase shared branches without approval;
- do not auto-resolve conflicts without showing what changed;
- do not use `ours` or `theirs` as a shortcut unless the user explicitly approves;
- after conflict resolution, show `git diff` and `git status`.

## Large files and generated outputs

Before committing, check for large or generated files:

```bash
git status
git diff --stat
```

Do not commit by default:

```text
.env
*.pem
*.key
*.p12
*.sqlite
*.db
*.parquet
*.csv
*.xlsx
*.zip
*.tar
*.log
__pycache__/
.ipynb_checkpoints/
node_modules/
dist/
build/
.venv/
```

Exceptions require explicit approval and a reason.

## Sensitive path handling

If a path may contain private local context, secrets, user data, company information, local Village memory, or generated outputs, stop and ask before staging or publishing it.

Examples:

```text
alliance/kirigakure/
memory/yamanaka/local/
.local/
.env
secrets/
private/
tmp/
archive/
```

## Commit message guidelines

Use short, concrete commit messages.

Good:

```text
Add agent entrypoint instructions
Add mission templates
Add Git safety scroll
Normalize line endings
Fix README license
```

Avoid:

```text
Update stuff
Various changes
Final version
Huge improvement
WIP
```

Use past tense only when the commit is explicitly a log or closure note.

## Evidence report

For every Git operation mission, report:

```text
Repository:
Branch:
Remote:
Commands run:
Files staged:
Commit created:
Commit hash:
Push status:
Review performed:
Risks checked:
Remaining questions:
```

Do not claim success without evidence from Git output.

## Stop-and-ask triggers

Stop and ask when:

- the branch is unclear;
- the remote is unclear;
- the repo may be public and sensitive content may be present;
- a workplace email may be exposed unintentionally;
- a command would rewrite history;
- a command would delete files;
- a command would publish changes;
- `git status` shows unexpected files;
- the diff includes unrelated changes;
- a file looks like a secret, dataset, log, or private note;
- line ending normalization changes many files unexpectedly;
- merge conflicts appear;
- the user asks for a risky command without enough context.

## Violations

A violation occurs if an agent:

- stages files without permission;
- commits without permission;
- pushes without permission;
- rewrites history without permission;
- hides a risky diff;
- commits secrets or private context;
- changes remotes silently;
- deletes branches or files without approval;
- claims a push succeeded without evidence.

When a violation occurs, stop, report what happened, preserve evidence, and ask for the next approved step.

## Completion checklist

A Git mission is complete only when:

- the requested Git action is done or explicitly deferred;
- `git status` was checked;
- relevant diffs were reviewed;
- sensitive content checks were performed;
- author identity was checked when publishing publicly;
- branch and remote were confirmed before push;
- commit hash is reported when a commit was created;
- push result is reported when a push was approved;
- no unresolved risky state remains;
- the user understands what happened and what to do next.
