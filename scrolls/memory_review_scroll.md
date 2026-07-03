# Memory Review Scroll

## Status

Draft.

## Purpose

This Scroll defines how to review memory notes, context packs, learning records, summaries, and local memory structures before they are used by an agent or promoted into broader Academy doctrine.

Memory review is about trust, scope, sensitivity, and traceability.

It is not approval to act.

## Core rule

Memory supports action.

Memory does not authorize action.

## Applies to

Use this Scroll when reviewing:

- Yamanaka Memory Network notes;
- Obsidian-compatible memory notes;
- context packs;
- learning proposals;
- mission summaries;
- archived mission records;
- local Village memory;
- private project memory;
- communication summaries;
- reusable decisions;
- approved tactics;
- failure records.

## Does not apply to

This Scroll does not replace:

- Mission Charter approval;
- Safety Policy;
- Context Policy;
- Approval Policy;
- Learning Policy;
- Teachback Policy;
- Kage Summit review;
- human approval for sensitive content.

A memory item may be accurate and still not be authorized for use in a mission.

## Required reading

Before applying this Scroll, read:

```text
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
memory/yamanaka/yamanaka_memory_policy.md
protocols/context/context_policy.md
protocols/safety/safety_policy.md
protocols/learning/learning_policy.md
protocols/approval/approval_policy.md
protocols/review/review_policy.md
```

If the memory belongs to a local Village, also read the relevant local Village rules, if access was explicitly allowed.

## Review modes

### Mode 1: read-only memory review

Default mode.

Allowed:

- inspect memory structure;
- check frontmatter;
- check source references;
- classify sensitivity;
- identify stale or unsupported claims;
- recommend edits;
- recommend archival;
- recommend escalation.

Not allowed:

- edit memory;
- create memory;
- delete memory;
- promote memory to doctrine;
- use memory as permission;
- access private files outside approved scope.

### Mode 2: memory correction proposal

Allowed only when explicitly requested.

Allowed:

- draft corrected text;
- propose frontmatter changes;
- propose tags;
- propose source links;
- propose deprecation notes.

Not allowed:

- apply changes unless file edits are explicitly approved;
- remove uncertainty to make the note look cleaner;
- convert a summary into a source of truth.

### Mode 3: memory promotion review

Used when a local learning or mission note may become Academy-level memory or doctrine.

Requires:

- Jounin review;
- Shikamaru draft if doctrine is affected;
- human approval;
- Kage Summit when the promotion changes behavior, safety, review, permissions, memory handling, or agent authority.

## Memory trust levels

### Raw source

Original source material.

Examples:

- mission transcript;
- user-provided document;
- approved command output;
- reviewed diff;
- test output;
- issue or MR discussion;
- explicit human decision.

Highest evidentiary value, but may contain sensitive content.

### Extracted fact

A specific fact copied or derived from a raw source.

Needs citation or source pointer.

Example:

```text
The mission used review level 2 according to the approved Mission Charter.
```

### Summary

A condensed description of source material.

Useful for context, not truth.

A summary must not hide uncertainty, conflict, missing evidence, or sensitive-source limits.

### Interpretation

A conclusion drawn from facts.

Must be labeled as interpretation.

Example:

```text
Interpretation: the failure likely came from unclear scope, not from tool misuse.
```

### Proposal

A suggested change, tactic, or doctrine update.

A proposal is never active policy until approved.

## Review checklist

### 1. Scope

Confirm:

- the memory item belongs to the mission, project, Village, or Academy area being reviewed;
- the Mission Charter allows memory review;
- the paths are explicitly allowed;
- the item is not from a private Village unless access was approved.

Stop if scope is unclear.

### 2. Source

Check whether the memory item identifies its source.

Acceptable source references include:

- Mission ID;
- approved Mission Charter;
- Mission Report;
- explicit user decision;
- reviewed diff;
- command output;
- file path and commit hash;
- Kage Summit verdict;
- linked local source, if local access is allowed.

If there is no source, mark the item as unsupported.

Do not delete it automatically.

### 3. Evidence quality

Classify evidence as:

```text
strong
partial
weak
missing
conflicting
```

Strong evidence usually includes source, timestamp, mission ID, and exact decision or output.

Weak evidence usually includes vague summaries like:

```text
We learned that this is better.
```

without proof, scope, or conditions.

### 4. Sensitivity

Check whether the memory contains:

- names of private people;
- customer identifiers;
- internal company names;
- emails;
- phones;
- addresses;
- operation numbers;
- credentials;
- tokens;
- file paths exposing private systems;
- private project names;
- screenshots;
- copyrighted assets;
- proprietary prompts;
- private model metadata;
- business rules not meant for public release.

If sensitive content exists, classify it and recommend one of:

```text
keep local
redact
summarize safely
archive outside active memory
block promotion
delete only with explicit approval
```

Never reproduce secrets in the review report.

### 5. Local vs Academy memory

Classify the item as:

```text
Academy memory
Local Village memory
project memory
mission memory
temporary context
archive-only
blocked
```

Local memory stays local by default.

A local note can be promoted only when it is generalized, sanitized, reviewed, and approved.

### 6. Accuracy

Check whether the note:

- distinguishes facts from interpretation;
- preserves uncertainty;
- avoids invented certainty;
- does not turn assumptions into decisions;
- does not omit relevant constraints;
- does not claim success without evidence;
- does not conflict with current doctrine.

If there is a conflict, doctrine wins unless a new doctrine change is explicitly approved.

### 7. Freshness

Check whether the memory is stale.

Signals of staleness:

- old Mission Charter;
- deprecated Scroll;
- changed repo structure;
- replaced policy;
- obsolete adapter behavior;
- old local environment;
- archived project decision.

A stale item may still be useful as history, but it should not be used as active context without review.

### 8. Authorization risk

Check for language that implies permission.

Unsafe examples:

```text
This project allows agents to edit files.
The user usually approves this.
This command is safe.
The agent can publish this later.
```

Safer form:

```text
This was allowed in Mission KAA-0007 under its approved Mission Charter.
Future missions still require explicit approval.
```

Memory may describe past permission.

It may not grant future permission.

### 9. Frontmatter

Recommended frontmatter:

```yaml
---
type: memory_note
status: draft
scope: academy
mission_id:
source:
created:
updated:
sensitivity: public
review_level: pending
trust_level: summary
tags: []
---
```

For local notes:

```yaml
scope: local-village
village:
public_safe: false
```

For learning proposals:

```yaml
type: learning_proposal
status: proposed
requires_review: true
doctrine_change: false
```

### 10. Links and backlinks

For Obsidian-compatible memory, check:

- links point to approved or accessible notes;
- backlinks do not expose private paths;
- tags are useful and not excessive;
- filenames are descriptive;
- aliases do not leak private names;
- broken links are noted.

### 11. Duplication

Check whether the note duplicates:

- another memory note;
- an approved tactic;
- a policy file;
- a project-specific decision;
- a learning proposal.

Possible outcomes:

```text
keep both
merge proposal
mark as duplicate
archive older note
convert one note into source reference
```

Do not merge automatically without approval.

### 12. Promotion readiness

A memory item is ready for promotion only if it is:

- source-backed;
- generalized;
- sanitized;
- not local-sensitive;
- consistent with doctrine;
- reviewed at the required level;
- approved by the user when required.

If it changes behavior, permissions, safety, memory rules, review, or execution flow, it needs doctrine process.

## Stop conditions

Stop and ask when:

- memory contains secrets;
- memory contains personal data;
- memory belongs to a private Village outside scope;
- source is missing for an important claim;
- the note conflicts with doctrine;
- the note implies future permission;
- the review would require editing files without approval;
- promotion would change policy or agent behavior;
- the memory item references unavailable private files;
- the agent cannot tell whether content is public-safe.

## Allowed outputs

A memory review may produce:

- review report;
- sensitivity classification;
- trust classification;
- stale-memory warning;
- proposed edits;
- proposed tags;
- proposed archive action;
- proposed learning proposal;
- proposed Kage Summit escalation.

## Forbidden outputs

A memory review may not produce:

- silent memory edits;
- silent doctrine updates;
- rewritten history;
- fabricated citations;
- generalized rules from one example;
- public summaries of private memory;
- approval to execute a mission;
- clearance to publish sensitive content.

## Report format

Use this format:

```markdown
# Memory review report

## Reviewed item

- Path:
- Type:
- Scope:
- Status:

## Verdict

- Result: pass | pass-with-notes | needs-changes | blocked
- Reason:

## Sensitivity

- Classification:
- Public safe: yes | no | unclear
- Notes:

## Source and evidence

- Source present: yes | no | partial
- Evidence quality:
- Missing evidence:

## Accuracy

- Facts vs interpretation:
- Unsupported claims:
- Conflicts:

## Authorization risk

- Permission implied: yes | no | unclear
- Notes:

## Freshness

- Fresh: yes | no | unclear
- Staleness notes:

## Recommended action

- Keep:
- Edit:
- Archive:
- Promote:
- Escalate:

## Required approvals

- Human approval:
- Jounin review:
- Shikamaru draft:
- Kage Summit:

## Safe summary

Short summary that does not reproduce sensitive content.
```

## Pass criteria

A memory item passes review when:

- scope is clear;
- source exists or lack of source is acceptable for the use case;
- sensitivity is classified;
- facts and interpretations are separated;
- no future permission is implied;
- stale content is marked;
- conflicts are identified;
- public-safe status is clear;
- required review level is satisfied.

## Block criteria

Block use or promotion when:

- secrets are present;
- personal data is present without explicit approval and safeguards;
- local private content would be exposed publicly;
- source is missing for a decision or rule;
- the item conflicts with safety policy;
- the item changes doctrine without approval;
- the item grants authority through memory;
- reviewer cannot determine sensitivity.

## Relationship with learning

Learning proposals may come from memory review, but they stay proposals.

Do not convert memory into doctrine directly.

Correct flow:

```text
Memory item
→ Memory review
→ Learning proposal
→ Jounin review
→ Shikamaru draft if doctrine is affected
→ Human approval
→ Kage Summit if required
→ Doctrine or approved tactic
```

## Relationship with Mission Charter

A Mission Charter can allow memory review.

It can also allow memory edits.

It must say so explicitly.

If the Charter allows only read-only review, do not modify memory files.

## Relationship with local Villages

Local Village memory may include private context.

Default handling:

```text
read only if explicitly allowed
summarize safely
do not copy into Academy memory
do not publish
do not promote without sanitization and approval
```

## Violations

These are violations:

- using memory as permission;
- publishing local memory;
- summarizing secrets;
- silently editing memory;
- promoting a learning as doctrine;
- hiding uncertainty;
- deleting inconvenient history;
- treating summaries as truth;
- copying private project context into public Academy files.

## Closure checklist

Before closing a memory review mission, confirm:

```text
[ ] Scope was explicit.
[ ] Reviewed paths were allowed.
[ ] Sensitivity was classified.
[ ] Source quality was assessed.
[ ] Unsupported claims were identified.
[ ] Authorization risk was checked.
[ ] Stale content was marked.
[ ] Recommended action was stated.
[ ] Required approvals were listed.
[ ] No sensitive values were reproduced in the report.
[ ] Mission completion was not declared until required review and teachback were done.
```
