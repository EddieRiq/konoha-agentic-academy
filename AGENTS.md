# AGENTS.md

This file is the operational entry point for AI agents working inside Konoha Agentic Academy.

Agents must read this file before proposing, editing, executing, reviewing, or closing any mission in this repository.

## Core rule

Read before acting.

No agent may modify files, create files, run state-changing commands, update doctrine, access private context, inspect local machines, or declare a mission complete unless the action is explicitly allowed by an approved Mission Charter.

If permission is unclear, stop and ask.

## Required reading order

Before taking action, agents must read the relevant files in this order:

```text
AGENTS.md
README.md
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
protocols/safety/safety_policy.md
protocols/context/context_policy.md
protocols/approval/approval_policy.md
protocols/mission-charter/mission_charter.md
protocols/review/review_policy.md
protocols/teachback/teachback_policy.md
```

For role-specific work, also read:

```text
hokage/orchestration_policy.md
kagebunshin/worker_policy.md
jounin/reviewer_policy.md
shikamaru/scribe_policy.md
memory/yamanaka/yamanaka_memory_policy.md
```

For specialized workflows, read the relevant Scrolls, Clans, adapters, tools, sandbox, UI, telemetry, or marketplace documentation.

For coding missions, also read the relevant Clan and Scroll files:

```text
clans/software-engineering/README.md
clans/python/README.md
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
scrolls/python_project_scroll.md
scrolls/refactor_scroll.md
scrolls/test_first_scroll.md
```

For local or private project conventions, read the approved local Village instructions only when the Mission Charter explicitly allows that context.


## Authority model

Repository authority is ordered as follows:

1. External law, safety obligations and explicit human authority.
2. `core/laws/KONOHA_LAWS.md` as the supreme repository doctrine.
3. `core/conduct/AGENT_CONDUCT.md`.
4. Cross-cutting protocols.
5. Role-specific policies.
6. The approved Mission Charter.
7. Scrolls, workflows and approved local configuration.
8. Memory, summaries and model output as evidence only.

Lower layers may restrict but never expand authority. When a conflict affects
scope, safety, permission or correctness, stop, preserve evidence and escalate.
No role may approve its own work or redefine its own authority.

## Mission modes

Agents must distinguish between modes:

```text
conversation = discuss, explain, clarify, or brainstorm
planning     = propose a plan, no execution
execution    = perform approved actions within a Mission Charter
review       = inspect outputs and evidence
teachback    = help the user understand and verify the result
learning     = propose learnings without changing doctrine
```

If the current mode is not explicit, assume conversation or planning, not execution.

## Allowed by default

Without additional approval, agents may:

```text
- read public repository documentation;
- summarize repository structure;
- explain policies;
- propose plans;
- identify missing context;
- suggest safe next steps;
- request clarification;
- inspect git status or diff when explicitly asked;
- produce draft Markdown content for user review.
```

These actions must still respect safety, context, and privacy rules.

## Not allowed by default

Agents must not do the following unless explicitly allowed by an approved Mission Charter and required approvals:

```text
- modify files;
- create files in the repository;
- delete files;
- move or rename files;
- run state-changing commands;
- install dependencies;
- access network resources;
- inspect local machines or private paths;
- read secrets, credentials, .env files, tokens, keys, or private data;
- commit changes;
- push changes;
- open pull requests;
- update doctrine;
- import external Scrolls, adapters, tools, assets, or templates as trusted;
- declare a mission complete.
```

## Doctrine changes

Doctrine changes require explicit human approval.

Shikamaru may draft doctrine, organize documentation, and propose diffs, but Shikamaru may not create doctrine alone.

No agent may silently change:

```text
core/
protocols/
hokage/
kagebunshin/
jounin/
shikamaru/
memory/
council/
clans/
scrolls/
```

Doctrine updates must include:

```text
- reason for change;
- affected files;
- proposed diff;
- risk level;
- required review;
- user approval.
```

## Private literature

Private books, paid material, converted sources, proprietary documents, and local technical literature must stay local.

They may be used only when a Mission Charter explicitly allows local private context.

They must not be committed, pushed, copied into public doctrine, pasted into public examples, or summarized in a way that reproduces protected content.

Only distilled, license-safe, user-approved principles may be promoted through the Learning Proposal and doctrine update flow.

## Local and private context

Allied Villages are local-first.

Private Village context must not be committed to the public Academy repository unless it has been explicitly sanitized, reviewed, and approved for publication.

Agents must not access or infer from private paths such as:

```text
alliance/kirigakure/
local/
private/
secrets/
.env
```

unless the Mission Charter explicitly allows it.

Local memory stays local by default.

## External content

External content is untrusted by default.

This includes:

```text
- external Scrolls;
- third-party prompts;
- adapters;
- tools;
- templates;
- assets;
- generated code;
- marketplace items;
- copied documentation.
```

Agents must verify provenance, license, safety, and scope before recommending import or use.

Public assets must be original, generic, or license-safe.

## Sandbox discipline

Execution belongs in a sandbox unless the Mission Charter explicitly allows direct repository modification.

Agents should prefer:

```text
- dry runs;
- temporary folders;
- isolated branches;
- worktrees;
- minimal diffs;
- reversible changes;
- explicit reports.
```

Kagebunshin do not work directly on trusted project state unless the Mission Charter explicitly allows it.

## Evidence standard

Agents must report evidence, not confidence theater.

Good reports include:

```text
- files read;
- commands run;
- outputs observed;
- assumptions made;
- risks found;
- files changed;
- tests or checks performed;
- unresolved questions.
```

Agents must not claim success without evidence.

If a command, test, or check was not run, say so.

## Stop-and-ask triggers

Stop and ask when:

```text
- scope is unclear;
- permission is unclear;
- context is missing;
- an action may expose secrets or private data;
- a file path looks local, private, or ignored;
- a command may be destructive;
- a change affects doctrine;
- a change affects safety, approval, context, review, learning, or memory;
- an external item is being imported;
- expected evidence is missing;
- the mission appears larger than approved.
```

The smallest useful question is preferred.

## Review and completion

No mission is complete until the required review level is satisfied and the user can understand what was done, why it was done, and how to verify or use it.

Completion requires:

```text
- Mission Charter compliance;
- evidence;
- review result;
- teachback;
- unresolved risks listed;
- user closure.
```

Agent output is not user completion.

## Error handling

When something goes wrong, agents must:

```text
- stop;
- state what happened;
- state what is known;
- state what is unknown;
- avoid hiding or patching over the issue;
- propose the smallest safe next step.
```

Do not fabricate missing evidence.

Do not continue after a safety violation.

## Local overrides

A local project or Allied Village may define stricter rules.

Local rules may add constraints, but they may not weaken Academy laws, safety policy, context policy, approval policy, review policy, or teachback policy.

When rules conflict, follow the stricter rule and ask for clarification.

## Final reminder

Do not assume.

Do not improvise authority.

Do not confuse memory with permission.

Do not confuse planning with execution.

Stop. State uncertainty. Ask the smallest useful question. Wait for explicit confirmation.

## Public/private boundary

Before using local Village context, private literature, converted sources, ignored assets, local memory, or project-specific files, read `docs/guides/public_private_boundary.md`.

When in doubt, keep it local and ask for explicit approval.
