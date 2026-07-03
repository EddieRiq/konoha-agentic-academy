# Learning capture scroll

## Status

Draft.

## Purpose

This Scroll defines a safe workflow for capturing lessons from a mission after the work has been reviewed.

The goal is to preserve useful experience without silently changing doctrine, expanding permissions, or treating one mission outcome as a general rule.

## Core rule

Experience is not doctrine.

A mission can produce observations, lessons, tactics, warnings, and proposals. None of them become Academy doctrine until they are reviewed, drafted by Shikamaru when needed, and approved by the user or the required authority.

## When to use this Scroll

Use this Scroll when a mission produced any of the following:

- a repeated mistake;
- a useful workflow;
- a failed approach;
- a debugging lesson;
- a new safety concern;
- a context handling lesson;
- a Git, repo, adapter, Scroll, or template improvement;
- a user preference that should be remembered;
- a local Village lesson that may stay local;
- a possible doctrine change;
- a possible new Scroll, Clan, tool, adapter, or template.

Do not use this Scroll as a substitute for Mission Report, Teachback, Review, or Kage Summit.

## Inputs required

Before capturing learning, collect:

- Mission ID;
- approved Mission Charter;
- final Mission Report;
- reviewer result, if any;
- teachback result, if any;
- relevant diffs or file references;
- commands run, if applicable;
- failures or incidents, if applicable;
- user feedback;
- sensitivity classification;
- target memory location;
- whether the lesson is Academy-wide or local to a Village.

If the mission was not reviewed or closed properly, stop and mark the learning as provisional.

## Default permissions

Unless the Mission Charter explicitly allows more, this Scroll is read-only and draft-only.

Allowed by default:

- read the Mission Charter;
- read the Mission Report;
- read approved review notes;
- read approved teachback notes;
- inspect approved diffs or outputs;
- summarize lessons;
- classify observations;
- draft a memory note;
- draft a learning proposal;
- recommend follow-up actions.

Not allowed by default:

- modify doctrine;
- create or edit files in the repository;
- write to Academy memory;
- write to Local Village memory;
- copy private context into public memory;
- promote a local lesson to public doctrine;
- update Scrolls, Clans, policies, templates, or AGENTS.md;
- declare a new rule active;
- hide uncertainty;
- summarize secrets or personal data.

## Learning categories

Classify each captured item as one of:

```text
fact
decision
preference
tactic
failure
risk
open-question
local-pattern
doctrine-proposal
scroll-proposal
tool-proposal
adapter-proposal
template-proposal
```

Use the weakest accurate category.

A single successful mission usually supports a tactic or proposal, not a doctrine change.

## Evidence standard

Every captured lesson must include evidence.

Acceptable evidence includes:

- user approval;
- Mission Charter text;
- Mission Report findings;
- reviewer notes;
- command output;
- test results;
- diff summary;
- file path and section reference;
- incident report;
- repeated occurrence across missions.

Do not capture lessons based only on confidence, vibes, inferred intent, or model memory.

## Sensitivity check

Before writing or proposing any memory entry, check whether the content includes:

- secrets;
- credentials;
- tokens;
- private keys;
- connection strings;
- personal data;
- customer data;
- internal company names or paths;
- local machine paths;
- private Village context;
- copyrighted or franchise-specific assets;
- unpublished business decisions.

If sensitive content is present, do not copy it into public memory.

Use placeholders or a local-only memory target when appropriate.

## Academy memory vs Local Village memory

Use Academy memory for lessons that are generic, public-safe, and useful across projects.

Use Local Village memory for lessons tied to:

- private repositories;
- internal systems;
- client or company context;
- local folders;
- private workflows;
- user-specific operational preferences;
- sensitive project constraints.

Local memory stays local by default.

A local lesson may be proposed for Academy promotion only after it is sanitized and reviewed.

## What to capture

Good learning capture is specific enough to help future missions.

Capture:

- what happened;
- what was expected;
- what failed or worked;
- why it matters;
- what evidence supports it;
- where it applies;
- where it does not apply;
- what should be done next;
- who must approve promotion.

Avoid:

- vague summaries;
- generic productivity advice;
- inflated conclusions;
- unverified root causes;
- raw logs with secrets;
- personal data;
- full private paths when a placeholder is enough;
- declaring a general law from one case.

## Workflow

### Step 1: verify closure status

Check whether the mission has:

- approved Charter;
- completed work;
- required review;
- teachback result;
- final report;
- unresolved blockers.

If closure is incomplete, classify the learning as provisional and do not promote it.

### Step 2: extract observations

List concrete observations from the mission.

Use this format:

```text
Observation:
Evidence:
Scope:
Sensitivity:
Confidence:
```

Confidence must be based on evidence, not tone.

### Step 3: classify each observation

Assign one learning category to each observation.

If an item could change agent behavior, mark it as a proposal, not a rule.

### Step 4: decide memory target

Choose one:

```text
no-memory
academy-memory-draft
local-village-memory-draft
learning-proposal
kage-summit-brief
incident-report
```

Use `no-memory` when the lesson is too minor, too sensitive, or not reusable.

### Step 5: draft memory note or proposal

Use the approved templates when available:

```text
memory/yamanaka/templates/memory_note_template.md
memory/yamanaka/templates/learning_proposal_template.md
council/templates/kage_summit_brief_template.md
```

Draft only. Do not write the file unless explicitly allowed.

### Step 6: request approval

Before saving or promoting learning, ask for explicit approval.

The approval request must include:

- target location;
- sensitivity classification;
- summary of captured lesson;
- evidence;
- expected future use;
- what will not be stored;
- review requirement.

### Step 7: store or escalate

If approved, store the item in the approved location.

If the lesson changes permissions, doctrine, safety behavior, memory policy, review requirements, or agent authority, escalate to Kage Summit.

## Promotion path

Learning can move through these states:

```text
observed
captured
drafted
reviewed
approved-local
approved-academy
promoted-to-doctrine
rejected
archived
```

Promotion to doctrine requires:

- evidence;
- Shikamaru draft;
- required review;
- explicit user approval;
- traceable reference to the source mission.

## Role responsibilities

### Hokage

The Hokage decides whether learning capture is needed and routes it to Shikamaru, a Clerk, a Jounin, or Kage Summit.

The Hokage may not promote learning to doctrine alone.

### Shikamaru

Shikamaru structures memory notes, learning proposals, and doctrine drafts.

Shikamaru may write drafts, but may not create doctrine alone.

### Jounin

Jounin reviews whether the lesson is supported by evidence, scoped correctly, and safe to store or promote.

### Clerk

A Clerk may summarize, tag, cluster, deduplicate, or format learning notes.

A Clerk may not approve technical correctness, safety, doctrine, or promotion.

### Kagebunshin

A Kagebunshin may report lessons from execution.

A Kagebunshin may not store memory, rewrite doctrine, or decide promotion unless explicitly authorized.

## Stop conditions

Stop and ask when:

- evidence is missing;
- the lesson is based on inferred user intent;
- the mission was not reviewed;
- the lesson includes sensitive content;
- the lesson may change doctrine;
- the lesson may affect permissions;
- local context might leak into public memory;
- the correct memory target is unclear;
- the user has not approved storage;
- the lesson contradicts existing policy.

## Output format

A learning capture report should include:

```text
Mission ID:
Closure status:
Learning capture status:
Sensitivity:
Memory target:
Items captured:
Items rejected:
Doctrine impact:
Review needed:
Approval needed:
Recommended next action:
Evidence:
```

## Minimal learning capture report

For small missions, use:

```text
Mission ID:
Lesson:
Evidence:
Scope:
Sensitivity:
Target:
Approval required:
```

## Violations

The following are violations of this Scroll:

- writing memory without approval;
- converting a lesson into doctrine without review;
- storing sensitive content in public memory;
- promoting local Village context to Academy memory without sanitization;
- recording speculation as fact;
- hiding uncertainty;
- summarizing secrets instead of removing them;
- using a lesson to expand future permissions;
- skipping required Kage Summit escalation.

## Completion checklist

Before closing a learning capture mission, verify:

```text
[ ] Mission source identified.
[ ] Evidence reviewed.
[ ] Lesson classified.
[ ] Sensitivity checked.
[ ] Memory target selected.
[ ] No secrets or personal data copied.
[ ] Doctrine impact assessed.
[ ] Required review identified.
[ ] User approval requested when storage or promotion is needed.
[ ] Output clearly marks draft vs approved content.
```
