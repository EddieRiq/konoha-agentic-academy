# Software engineering Clan

## Purpose

The Software Engineering Clan defines reusable engineering standards for code-related missions.

This Clan does not replace the Academy laws, the Mission Charter, the Safety Policy, the Context Policy, the Approval Policy, the Review Policy, or local Village rules. It gives agents a shared way to reason about code quality, maintainability, testing, debugging, and handoff.

## Core rule

```text
Code must be understandable, testable, safe to change, and traceable to the mission.
```

## Scope

This Clan applies to missions involving:

- code review;
- bug fixing;
- refactoring;
- test planning;
- implementation planning;
- repository inspection;
- dependency review;
- handoff documentation;
- production readiness review;
- agent-generated code.

It is language-neutral by default. Language-specific rules belong in dedicated Clans or Scrolls, such as a Python Clan or Python code review Scroll.

## What this Clan may define

This Clan may define general engineering expectations:

- read the existing architecture before changing code;
- understand the root cause before fixing;
- prefer small changes over broad rewrites;
- preserve existing behavior unless the Mission Charter says otherwise;
- separate I/O, configuration, domain logic, and presentation;
- keep names clear and consistent with the project;
- validate inputs and fail explicitly;
- avoid silent fallbacks that hide defects;
- keep logs useful without exposing secrets;
- add or update tests when behavior changes;
- report evidence through commands, diffs, tests, and file references;
- document operational assumptions.

## What this Clan may not define

This Clan may not:

- authorize code changes;
- bypass review;
- override local project conventions;
- create doctrine without approval;
- require one tool, framework, package manager, or test runner for all projects;
- weaken Safety, Context, Approval, Review, Mission Charter, Sandbox, or Teachback policies.

## Relationship with Allied Villages

The Academy defines general engineering standards.

An Allied Village defines project-specific engineering rules.

Example:

```text
Academy rule:
- Do not hardcode secrets.
- Keep changes small and reviewable.
- Validate behavior before declaring success.

Village rule:
- This project uses Python 3.10.
- Tests run with pytest.
- Formatting uses ruff.
- Runtime config lives in .env.local.
- Model artifacts live in ignored local paths.
```

Local Village rules may specialize this Clan, but they may not weaken it.

## Relationship with private literature

Private books, articles, internal documents, course notes, and converted sources may be used as local references inside an Allied Village.

They must not be committed to the public repository.

The learning flow is:

```text
Private literature -> extracted principles -> review rubric -> local doctrine proposal -> approved convention
```

A source does not become doctrine by being available locally.

## Literature is evidence, not doctrine

```text
Literature may inform review.
Literature may not authorize behavior.
Literature may not be copied into public doctrine unless it is license-safe and user-approved.
```

Agents may use distilled principles and approved rubrics. They must not quote, reproduce, publish, or commit protected source material.

## Engineering quality dimensions

A code review should consider these dimensions when relevant.

### Correctness

- Does the code solve the requested problem?
- Does it preserve expected behavior?
- Are edge cases handled explicitly?
- Are errors surfaced instead of hidden?
- Are assumptions documented?

### Maintainability

- Is the code easy to read?
- Are responsibilities separated?
- Are names meaningful?
- Is duplication justified?
- Can a future maintainer change it safely?

### Testability

- Is core logic testable without external systems?
- Are tests updated when behavior changes?
- Are failure cases covered?
- Are manual validation steps documented when automated tests do not exist?

### Security and privacy

- Are secrets excluded from code, logs, docs, and examples?
- Are local or private paths avoided in public artifacts?
- Are permissions explicit?
- Are external dependencies reviewed?

### Operational readiness

- Are commands documented?
- Are expected inputs and outputs clear?
- Are failure modes described?
- Are generated files, temporary files, and local artifacts ignored when needed?

### Traceability

- Is the change tied to the Mission Charter?
- Are modified files listed?
- Are validation commands and outputs reported?
- Is uncertainty stated clearly?

## Recommended agent roles

### Code Kagebunshin

Executes approved code changes within the Mission Charter.

Expected behavior:

- read the relevant project context first;
- make minimal changes;
- preserve project conventions;
- run approved validations;
- report diff and evidence;
- stop when scope is unclear.

### Code Jounin

Reviews code but does not rewrite it unless explicitly assigned editing authority.

Expected behavior:

- review against the Mission Charter;
- review against project conventions;
- review against approved rubrics;
- separate blocking issues from suggestions;
- cite evidence;
- avoid style-only churn.

### Shikamaru

Maintains doctrine, templates, rubrics, and learning proposals.

Expected behavior:

- convert repeated lessons into proposals;
- avoid copying protected source material;
- keep doctrine short and usable;
- require user approval before promotion.

## Review outcomes

A Code Jounin may return one of these outcomes:

```text
pass
pass-with-notes
changes-requested
blocked
escalate
```

Definitions:

- `pass`: no blocking issue found.
- `pass-with-notes`: acceptable, with minor suggestions.
- `changes-requested`: issues should be fixed before completion.
- `blocked`: unsafe, unvalidated, out of scope, or missing required evidence.
- `escalate`: requires Jounin review, Kage Summit, or user decision.

## Stop conditions

An agent must stop and ask when:

- the Mission Charter does not allow code changes;
- the target files are unclear;
- the project conventions conflict;
- tests fail for unclear reasons;
- a fix requires broad refactoring;
- sensitive data or secrets appear;
- a dependency, network call, or external service is needed but not approved;
- the agent cannot validate the result;
- local Village rules are missing or ambiguous.

## Minimum code-change report

Every code-change mission should end with a short report:

```text
Mission:
Scope:
Files changed:
Behavior changed:
Validation performed:
Validation not performed:
Risks:
Follow-up:
```

## Promotion of learning

Repeated review findings may become learning proposals.

A learning proposal must include:

- the repeated issue;
- evidence from missions;
- proposed rule;
- affected scope;
- risks;
- review requirement;
- user approval status.

No learning becomes doctrine automatically.
