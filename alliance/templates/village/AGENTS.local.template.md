# AGENTS.local.md

This file defines local agent instructions for the `{{VILLAGE_NAME}}` Allied Village.

It applies only inside this local Village.

It may specialize Academy doctrine, but it may not weaken it.

## Authority order

When working inside this Village, agents must follow this order:

```text
1. Explicit user instruction.
2. Konoha Laws.
3. Safety Policy.
4. Root AGENTS.md.
5. Mission Charter.
6. Local AGENTS.local.md.
7. Local Village doctrine.
8. Relevant Clans and Scrolls.
9. Local memory and context packs.
```

If instructions conflict, safety, privacy, explicit permission, and the Mission Charter win.

## Local rule

Local context stays local by default.

No agent may copy, summarize, publish, commit, transmit, or promote local Village context unless the action is explicitly allowed by the user and the Mission Charter.

## Default mode

Default mode is read-only planning.

Agents may read local instructions and propose a plan.

Agents may not modify files, run state-changing commands, inspect private folders, write memory, update doctrine, or publish content without explicit approval.

## Allowed by default

Unless the Mission Charter says otherwise, agents may:

```text
- read this file;
- read the approved Mission Charter;
- read local context explicitly attached to the mission;
- summarize known context;
- identify missing context;
- propose safe next steps;
- ask clarifying questions;
- prepare a draft plan.
```

## Not allowed by default

Agents may not:

```text
- access secrets;
- read .env files;
- inspect private-library sources unless explicitly approved;
- copy copyrighted source material;
- commit local Village files;
- publish local context to the public Academy repo;
- update local doctrine silently;
- execute commands that modify project state;
- run network or dependency commands without approval;
- infer permission from file presence.
```

## Required stop conditions

Stop and ask when:

```text
- scope is unclear;
- a file may contain secrets or personal data;
- a path is not explicitly allowed;
- a command changes state;
- a task could publish local context;
- a rule conflicts with Konoha doctrine;
- the agent is unsure whether content is public-safe;
- a mission needs a higher review level;
- private literature would need to be quoted or copied.
```

## Coding missions

For coding missions, agents must read the relevant files before proposing changes:

```text
clans/software-engineering/README.md
clans/python/README.md
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
scrolls/git_safety_scroll.md
```

Local coding conventions live in:

```text
doctrine/coding_conventions.md
doctrine/review_rubrics.md
```

If local conventions do not exist yet, agents must propose them before relying on them.

## Private literature

Private literature may support review and learning, but it does not directly authorize doctrine.

Agents must follow:

```text
docs/guides/private_literature_library.md
scrolls/private_literature_extraction_scroll.md
```

Rules:

```text
- do not copy protected source text into public docs;
- do not quote long passages;
- extract short, safe principles;
- preserve source metadata locally;
- promote only distilled, approved rules.
```

## Memory

Local memory must be scoped, sourced, and sensitivity-checked.

Memory supports action, but does not authorize action.

A memory note may not expand mission scope.

## Review

Local work must be reviewed according to risk.

Use:

```text
protocols/review/review_policy.md
jounin/reviewer_policy.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
```

No mission is complete until review and teachback requirements are satisfied.

## Reporting

Reports must include:

```text
- what was read;
- what was changed;
- what was not changed;
- commands run;
- evidence;
- risks;
- open questions;
- required review;
- teachback summary.
```

Do not report success without evidence.

## Local overrides

Add local overrides below.

Local overrides must be explicit and cannot weaken Academy rules.

### Local stack

```text
TODO: Python version, tools, frameworks, package manager, test command, lint command.
```

### Local paths

```text
TODO: approved project paths.
```

### Local forbidden paths

```text
TODO: forbidden paths, secrets, private outputs, datasets, credentials.
```

### Local commands

```text
TODO: approved read-only commands and state-changing commands requiring approval.
```

### Local reviewers

```text
TODO: required human reviewers or local Jounin roles.
```
