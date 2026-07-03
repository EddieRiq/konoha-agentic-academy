# Sandbox

The Sandbox defines how Konoha Agentic Academy isolates execution, protects repositories, and controls commands during Missions.

Sandbox rules apply to every Mission that may inspect, modify, execute, test, generate, or review files.

## Core rule

Kagebunshin do not work directly on trusted project state unless the Mission Charter explicitly allows it.

Execution must be isolated, reversible, and traceable.

## Purpose

The Sandbox exists to:

- prevent accidental modification of the main repository;
- isolate experimental work;
- avoid uncontrolled command execution;
- protect secrets, local memory, and private Village context;
- make diffs easier to review;
- support safe retries;
- keep failed attempts from polluting the working tree.

## Sandbox authority

Sandbox behavior is governed by:

1. `core/laws/KONOHA_LAWS.md`
2. `protocols/safety/safety_policy.md`
3. `protocols/approval/approval_policy.md`
4. `protocols/mission-charter/mission_charter.md`
5. this Sandbox policy

If there is a conflict, the stricter rule wins.

## Default execution model

By default, Missions that modify files should run in one of these isolated environments:

- a Git worktree;
- a temporary branch;
- a temporary directory;
- a container;
- a dry-run mode;
- a local sandbox directory controlled by Konoha.

The Mission Charter must state which isolation method is used.

## Main repository protection

The main repository should be treated as protected.

A Kagebunshin may not directly modify the main repository unless all of the following are true:

- the Mission Charter explicitly allows direct edits;
- the allowed paths are listed;
- the user approved the action when required;
- the action is reversible or backed by version control;
- safety checks passed.

## Git worktrees

For code changes, Git worktrees are preferred when available.

A worktree should be used when the Mission involves:

- code implementation;
- multi-file edits;
- tests;
- dependency changes;
- refactors;
- generated files;
- experiments;
- risky debugging.

A worktree should have a clear Mission-related name.

Example naming pattern:

```text
.worktrees/mission-<mission-id>-<short-title>/
```

## Temporary directories

Temporary directories may be used for:

- generated drafts;
- scratch files;
- proof-of-concept code;
- non-production outputs;
- file conversions;
- local experiments.

Temporary directories must not contain secrets or private data unless explicitly allowed by the Mission Charter.

## Containers

Containers may be used when a Mission requires dependency isolation or reproducible execution.

Container use requires human approval when it involves:

- pulling images from the internet;
- building images from unreviewed Dockerfiles;
- mounting sensitive directories;
- running privileged containers;
- exposing ports;
- accessing network resources;
- modifying volumes.

## Dry-run first

When supported, destructive or state-changing operations should run in dry-run mode first.

Examples:

- migrations;
- deletes;
- cleanup commands;
- generated file replacement;
- bulk renames;
- dependency updates;
- archive operations.

If dry-run is unavailable, the Kagebunshin must state that clearly before execution.

## Allowed command classes

Allowed command classes may include:

- read-only inspection;
- Git status and diff;
- test execution;
- format checks;
- lint checks;
- local scripts approved by the Mission Charter;
- safe file listing;
- schema validation;
- dry-run commands.

The Mission Charter must list specific allowed commands when execution risk is medium or high.

## Commands requiring human approval

The following command classes require explicit human approval:

- installing dependencies;
- deleting files;
- moving large directory trees;
- changing permissions;
- running migrations;
- starting services;
- running Docker containers;
- pushing to remote Git repositories;
- modifying Git history;
- accessing network resources;
- reading private files;
- writing to external storage;
- archiving sensitive context.

## Forbidden by default

The following are forbidden by default unless explicitly allowed under a reviewed Mission Charter:

```bash
rm -rf
sudo
curl | bash
wget | bash
chmod -R
chown -R
git push --force
git clean -fdx
docker system prune
docker volume prune
docker image prune -a
docker run --privileged
```

The list is not exhaustive. Any command that may cause irreversible, external, or security-sensitive effects must stop and ask.

## Secrets and sensitive paths

The Sandbox must not access sensitive paths unless explicitly allowed.

Forbidden by default:

```text
.env
*.pem
*.key
*.p12
*.pfx
secrets/
credentials/
private/
data/
alliance/*/memory/
alliance/*/assets/
alliance/*/.konoha.local/
```

If a Kagebunshin accidentally encounters a secret, it must stop, avoid repeating the secret, and report a sanitized incident.

## Network access

Network access is disabled by default for sandboxed work unless the Mission Charter allows it.

Network access requires approval when used for:

- package installation;
- external documentation lookup;
- API calls;
- uploads;
- downloads;
- telemetry submission;
- model calls outside the local machine;
- email or messaging integrations.

## Local models and Clerks

Local Clerks may operate inside the Sandbox for low-risk tasks, such as:

- summarization;
- classification;
- metadata extraction;
- formatting;
- context pack preparation;
- checklist validation.

Clerks may not bypass Sandbox rules.

A local model being offline or local does not make the task automatically safe.

## Generated outputs

Generated outputs must be written to safe locations first.

Preferred pattern:

```text
tmp/
sandbox/
.worktrees/
mission-output/
```

Outputs may only be moved into final paths after review and approval when required.

## Baseline checks

Before modifying code, the Kagebunshin should capture baseline state when relevant:

- `git status`;
- current branch;
- existing failing tests, if known;
- relevant file list;
- dependency status;
- existing output files.

If baseline checks fail or are unclear, the Kagebunshin must report the issue before proceeding.

## Diff discipline

A Mission must produce a reviewable diff.

The Kagebunshin must report:

- files created;
- files modified;
- files deleted;
- commands run;
- tests run;
- outputs generated;
- risks or unexpected changes.

Large, mixed, or unrelated diffs must be blocked or split.

## Sandbox escape

A Sandbox escape happens when an agent attempts to act outside the approved isolated environment.

Examples:

- editing files outside allowed paths;
- writing to the main repository from a sandboxed Mission;
- reading private files not listed in the Mission Charter;
- running commands outside the approved directory;
- installing dependencies globally;
- modifying system settings.

Sandbox escape is a violation and must be reported.

## Interaction with Local Villages

Allied Villages may define stricter sandbox rules.

Local Village rules may restrict:

- allowed paths;
- allowed commands;
- local model usage;
- memory paths;
- asset paths;
- external storage;
- network access;
- notification behavior.

Local Village rules may not weaken Konoha Safety Policy.

## Completion requirements

A sandboxed Mission may be completed only after:

- all outputs are inside approved locations;
- no forbidden paths were accessed;
- no unauthorized commands were run;
- the diff is reviewable;
- generated files are documented;
- temporary files are cleaned or reported;
- review level requirements are satisfied;
- user Teachback is completed when required.

## Violations

Violations include:

- executing commands not allowed by the Mission Charter;
- editing outside allowed paths;
- reading sensitive files without approval;
- modifying doctrine without Shikamaru;
- using network access without approval;
- hiding command output;
- claiming a test passed without evidence;
- leaving unreported generated files;
- bypassing required review.

Violations must be reported to the Hokage and may trigger Jounin review or Kage Summit escalation.

## Final rule

The Sandbox is not a convenience layer.

It is the boundary between useful autonomy and uncontrolled execution.
