# Mission planning Scroll

Status: draft  
Owner: Konoha Agentic Academy  
Applies to: Hokage, Local Kage, Shikamaru, Jounin, Kagebunshin, Clerks  
Primary policies: Mission Charter Policy, Context Policy, Approval Policy, Safety Policy, Review Policy

## Purpose

This Scroll converts a vague request into a clear Mission Charter before any execution begins.

It is used when the user asks for work that is not yet scoped enough to assign to a Kagebunshin, run commands, modify files, access local context, or declare success criteria.

## Core rule

Planning is not execution.

A mission plan may define what should happen, what context is needed, what risks exist, and what approvals are required. It may not perform the work.

## When to use this Scroll

Use this Scroll when a request includes any of the following:

- unclear objective;
- missing context;
- ambiguous files, folders, systems, or repositories;
- possible code, data, Git, server, model, BI, ETL, documentation, or production impact;
- sensitive or local context;
- external systems;
- multiple possible approaches;
- need for agent delegation;
- need for review or approval;
- unclear definition of done.

## When not to use this Scroll

Do not use this Scroll when:

- the user only wants a short explanation;
- the task is already fully scoped and approved;
- the task is casual conversation;
- emergency safety rules require stopping immediately;
- the user asks for execution but the required authorization is missing.

In those cases, stop and ask for the smallest missing approval or context.

## Authority

This Scroll may guide planning. It does not grant permission.

This Scroll cannot override:

- Konoha Laws;
- Agent Conduct;
- Safety Policy;
- Context Policy;
- Approval Policy;
- Mission Charter Policy;
- Review Policy;
- Teachback Policy;
- local Village rules.

If there is a conflict, the stricter rule wins.

## Allowed by default

During mission planning, the agent may:

- restate the user request;
- identify the likely mission type;
- list missing context;
- ask clarifying questions;
- propose mission boundaries;
- propose allowed and forbidden paths;
- propose allowed and forbidden commands;
- identify risks;
- identify required approvals;
- identify required review level;
- propose assigned roles;
- draft a Mission Charter;
- draft acceptance criteria;
- draft a teachback plan;
- explain trade-offs;
- recommend whether execution should proceed, pause, or be split into smaller missions.

## Forbidden by default

During mission planning, the agent may not:

- modify files;
- create files in the repo;
- run state-changing commands;
- access private local context;
- inspect the user's machine;
- connect to external services;
- read secrets;
- assume missing permissions;
- approve its own Mission Charter;
- assign Kagebunshin to execute work;
- mark a mission complete;
- write doctrine changes directly;
- convert a learning into doctrine;
- continue when the scope is unclear.

## Inputs

A planning mission should collect the following inputs when relevant:

```text
User request:
Expected outcome:
Repository or system:
Known files or paths:
Allowed files or paths:
Forbidden files or paths:
Allowed commands:
Forbidden commands:
Sensitive context:
External systems:
Data classification:
Deadline or priority:
Review expectation:
Definition of done:
```

If any field is unknown, write `Unknown` rather than guessing.

## Planning workflow

### 1. Restate the request

Rewrite the request in plain language.

The restatement must separate:

```text
What the user asked for:
What is known:
What is unknown:
What must not be assumed:
```

### 2. Classify the mission

Assign one primary mission type:

```text
conversation
planning
documentation
repo-review
code-change
data-task
modeling
BI-dashboard
ETL
Git-operation
server-operation
memory-update
doctrine-change
external-integration
```

If more than one applies, list the secondary types.

### 3. Identify risk level

Use the lowest risk level that honestly fits.

```text
low:
  Read-only, no sensitive context, no external system, no state change.

medium:
  File edits, generated docs, local memory updates, test execution, or non-sensitive repo changes.

high:
  Production systems, credentials, private data, model behavior, permissions, CI/CD, server changes, destructive commands, external publishing, or doctrine changes.
```

When unsure, choose the higher risk level.

### 4. Identify missing context

List only context that is needed to proceed.

Avoid asking for broad context when one small answer is enough.

Preferred format:

```text
Missing context:
1. ...
2. ...

Smallest useful question:
...
```

### 5. Define mission boundaries

Boundaries must be explicit.

```text
In scope:
- ...

Out of scope:
- ...

Allowed paths:
- ...

Forbidden paths:
- ...

Allowed commands:
- ...

Forbidden commands:
- ...
```

If paths or commands are not known, they remain forbidden until approved.

### 6. Define evidence requirements

The plan must state what evidence will prove the work was done.

Examples:

```text
- git status output;
- git diff summary;
- test output;
- rendered README check;
- validation count;
- schema comparison;
- screenshot;
- generated file path;
- review report;
- user teachback confirmation.
```

Do not accept confidence as evidence.

### 7. Define review level

Select the required review level:

```text
Level 0: no review required
Level 1: Clerk review
Level 2: Jounin review
Level 3: Kage Summit review
```

Use Jounin review for code, architecture, security, model behavior, data pipelines, doctrine, external integrations, or anything medium to high risk.

Use Kage Summit review when authority, safety, doctrine, cross-Village impact, or uncertainty exceeds the Mission Charter.

### 8. Draft the Mission Charter

The output of this Scroll should normally be a draft Mission Charter, not execution.

The draft must clearly mark its status:

```text
Status: draft, awaiting user approval
```

No agent may execute from a draft.

### 9. Ask for approval

Ask the user to approve, reject, or modify the Mission Charter.

Use a direct approval prompt:

```text
Approve this Mission Charter for execution?
```

Do not treat silence, enthusiasm, or vague agreement as approval for high-risk actions.

## Output format

Use this format unless the user asks for a different one.

```text
Mission planning result

Mission type:
Risk level:
Current mode:

Restated request:
Known context:
Missing context:
Smallest useful question:

Proposed scope:
Out of scope:
Allowed paths:
Forbidden paths:
Allowed commands:
Forbidden commands:

Required approvals:
Required review:
Evidence required:
Teachback requirement:

Draft Mission Charter:
...
```

## Stop-and-ask triggers

Stop and ask before continuing if:

- the requested action would change files;
- the requested action would run commands;
- the requested action touches secrets, credentials, private data, or local context;
- the user asks for "just do it" without approving scope;
- the target repo, branch, path, or file is unclear;
- the work might affect production;
- the work might publish content externally;
- a command could be destructive;
- the agent would need to inspect the user's machine;
- multiple interpretations are plausible;
- the task requires doctrine changes;
- the agent is about to infer permission from context.

## Handling vague user approval

The following are not sufficient approval for execution:

```text
ok
dale
sounds good
go ahead
continue
looks fine
do it
```

They may confirm planning continuation, but execution still requires an approved Mission Charter when the task involves state-changing work.

For low-risk documentation planning, a short approval may be enough only if the allowed action is already explicit.

## Sensitive context

If the mission may involve private context, credentials, customer data, personal data, local files, or company systems:

1. Stop.
2. Ask for the minimum safe context.
3. Require anonymization where applicable.
4. Mark sensitive paths as forbidden unless explicitly approved.
5. Keep local context local by default.

## Local Village missions

For Allied Village work:

- Local Kage owns local context boundaries;
- Konoha Hokage may coordinate but may not override local safety;
- local memory stays local unless explicitly promoted;
- public Academy files must not receive private Village context;
- local paths must be explicit.

## Doctrine-related missions

If the request may change doctrine:

1. Treat it as high risk.
2. Require explicit user approval.
3. Ask Shikamaru to draft, not decide.
4. Require Jounin or Kage Summit review depending on impact.
5. Do not execute doctrine changes from a planning draft.

## Example

```text
User request:
"Review this backend and add the scoring endpoint."

Planning result:
- Mission type: repo-review, code-change
- Risk level: high
- Current mode: planning
- Missing context: repo path, branch, model artifact path, endpoint pattern, tests
- Smallest useful question: What repo path and branch should be inspected first?
- Recommendation: start with a read-only repo review mission before any code edits.
```

## Completion criteria for this Scroll

This Scroll is complete when one of the following is true:

- the user receives a draft Mission Charter ready for approval;
- the user receives the smallest useful question needed to continue;
- the mission is rejected or paused due to missing context, safety, or authority;
- the mission is split into smaller missions.

This Scroll does not complete the underlying mission. It only prepares it.
