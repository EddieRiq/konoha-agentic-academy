# Documentation Review Scroll

## Status

Draft.

## Purpose

This Scroll defines a safe workflow for reviewing documentation in a repository without modifying files by default.

It is used when the mission is to inspect README files, handovers, architecture notes, policy documents, templates, contributor guides, or project documentation and return findings, risks, inconsistencies, and proposed changes.

## Core rule

Documentation review is read-only by default.

A reviewer may identify issues, propose edits, and prepare a change plan, but may not modify files unless the approved Mission Charter explicitly allows editing.

## Authority

This Scroll does not grant permission by itself.

It must operate under:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/mission-charter/mission_charter.md`
4. `protocols/safety/safety_policy.md`
5. `protocols/context/context_policy.md`
6. `protocols/approval/approval_policy.md`
7. `protocols/review/review_policy.md`
8. `protocols/teachback/teachback_policy.md`
9. Local Village rules, when reviewing a local repository

If this Scroll conflicts with higher authority, the higher authority wins.

## When to use this Scroll

Use this Scroll for missions such as:

- reviewing a project README;
- checking consistency between documentation files;
- reviewing technical handover documents;
- reviewing policy or doctrine files;
- reviewing templates;
- checking whether documentation matches the repository structure;
- identifying outdated, duplicated, unclear, or risky documentation;
- preparing a proposed documentation update plan.

## When not to use this Scroll

Do not use this Scroll to:

- change code;
- run migrations;
- update dependencies;
- modify doctrine;
- approve a Mission Charter;
- close a mission without review and teachback;
- inspect private or local content not included in the Mission Charter;
- rewrite documents in place without explicit approval.

## Required inputs

Before starting, the Hokage or Local Kage must provide:

```text
Mission ID:
Repository path:
Review objective:
Allowed files or directories:
Forbidden files or directories:
Sensitive content rules:
Output format:
Review depth:
Allowed commands:
Editing allowed: yes/no
Required review level:
```

If any required input is missing, stop and ask.

## Default mode

The default mode is:

```text
read-only documentation inspection
```

Allowed by default, if the Mission Charter permits the repository path:

```text
pwd
ls
find
tree
git status
git diff --stat
git log --oneline -n 5
read files explicitly in scope
search text in files explicitly in scope
summarize findings
propose changes
```

Not allowed by default:

```text
write files
delete files
move files
rename files
format files
commit changes
push changes
edit doctrine
read local private context
read secrets
inspect user machine outside the repository
```

## Review dimensions

### 1. Purpose and audience

Check whether the documentation clearly states:

- what the project is;
- who it is for;
- what problem it solves;
- what is in scope;
- what is out of scope;
- what the reader should do next.

### 2. Repository alignment

Check whether the documentation matches the actual repository structure.

Look for:

- paths that do not exist;
- files that exist but are not documented;
- outdated folder names;
- conflicting naming conventions;
- references to old structures;
- missing setup or navigation instructions.

### 3. Operational clarity

Check whether a user can execute or maintain the process from the documentation.

Look for:

- commands that can be copied safely;
- required prerequisites;
- setup steps;
- expected outputs;
- validation steps;
- failure handling;
- rollback or recovery notes when relevant.

### 4. Safety and privacy

Check for:

- credentials;
- tokens;
- private URLs;
- internal hostnames;
- customer data;
- personal identifiers;
- local filesystem paths that should not be public;
- copyrighted or franchise-specific assets;
- overbroad instructions that could cause destructive actions.

Any sensitive content found must be reported without repeating the sensitive value.

### 5. Consistency

Check consistency across:

- README;
- architecture docs;
- contribution docs;
- policies;
- templates;
- Scrolls;
- examples;
- command snippets;
- naming conventions.

Common issues:

- same concept with multiple names;
- same folder described differently across files;
- outdated examples;
- contradictory permissions;
- duplicate sections with drift;
- unclear hierarchy between policy files.

### 6. Maintainability

Check whether future contributors can maintain the documentation.

Look for:

- documents that are too long without navigation;
- missing table of contents when useful;
- repeated text that should be linked instead;
- unclear ownership;
- missing lifecycle status;
- missing update rules;
- unclear versioning;
- stale roadmap language.

### 7. Writing quality

Check whether the writing is clear and usable.

Prefer:

- direct sentences;
- concrete paths;
- explicit commands;
- precise terms;
- plain explanation;
- no inflated claims;
- no vague promises;
- no marketing tone.

Do not rewrite voice unless the Mission Charter asks for rewriting.

## Review levels

### Level 0: quick pass

Use for small files or simple checks.

Output:

```text
Summary
Blocking issues
Non-blocking issues
Suggested next action
```

### Level 1: standard review

Use for README files, handovers, and normal docs.

Output:

```text
Summary
Scope reviewed
Findings by severity
Evidence
Recommended changes
Open questions
```

### Level 2: doctrine or architecture review

Use when reviewing policy, architecture, permission, safety, memory, review, approval, or agent behavior documents.

Requires Jounin review.

Output must include:

```text
Authority impact
Potential contradictions
Risk classification
Files affected
Required approval level
Whether Kage Summit is needed
```

### Level 3: sensitive or public-release review

Use before publishing public documentation, importing external content, or changing security, privacy, permission, or doctrine language.

Requires Kage Summit or explicit human approval when defined by the Mission Charter.

## Severity levels

Use these labels in the report:

```text
BLOCKER
HIGH
MEDIUM
LOW
NOTE
```

Definitions:

- `BLOCKER`: must be fixed before publishing or closing the mission.
- `HIGH`: likely to cause misuse, confusion, broken workflow, privacy risk, or policy conflict.
- `MEDIUM`: should be fixed soon, but does not block basic use.
- `LOW`: clarity, formatting, or small consistency issue.
- `NOTE`: observation, optional improvement, or follow-up idea.

## Evidence standard

Every finding must include evidence.

Acceptable evidence:

```text
File:
Section:
Line or heading if available:
Observed issue:
Why it matters:
Suggested action:
```

Do not report a finding based only on vibes.

If line numbers are unavailable, cite the heading, filename, and nearby text.

## Stop-and-ask triggers

Stop and ask when:

- the Mission Charter does not define review scope;
- the file may contain private context;
- the user asks for "fix everything" without editing approval;
- the review requires reading ignored or local files;
- sensitive content is found;
- the documentation contradicts safety, approval, context, review, or memory policy;
- a proposed fix would change doctrine;
- the repository structure differs from the assumptions in the mission;
- the reviewer is not sure whether a file is public or private.

## Editing mode

Editing is disabled unless explicitly allowed.

If editing is allowed, the Mission Charter must define:

```text
Files allowed to edit:
Files forbidden to edit:
Max change size:
Whether doctrine changes are allowed:
Whether formatting-only changes are allowed:
Whether commits are allowed:
Required review level:
```

Even in editing mode, doctrine changes require the approval path defined by the Approval Policy and Scribe Policy.

## Proposed change format

When proposing changes, use this format:

```text
File:
Current issue:
Recommended change:
Reason:
Risk:
Requires approval: yes/no
```

For small edits, include a patch-style suggestion.

For large edits, propose a plan first.

## Output template

```md
# Documentation review report

## Mission

- Mission ID:
- Repository:
- Review objective:
- Review mode:
- Editing allowed:
- Files reviewed:
- Files not reviewed:

## Summary

Short summary of the current documentation state.

## Blocking issues

| Severity | File | Issue | Evidence | Recommended action |
| --- | --- | --- | --- | --- |

## Non-blocking issues

| Severity | File | Issue | Evidence | Recommended action |
| --- | --- | --- | --- | --- |

## Consistency check

Notes about naming, paths, structure, duplicated concepts, and contradictions.

## Safety and privacy check

Sensitive content found: yes/no

If yes, describe the type of issue without repeating the sensitive value.

## Suggested changes

Ordered list of recommended changes.

## Open questions

Questions that need user, Hokage, Local Kage, Shikamaru, Jounin, or Kage Summit input.

## Review decision

Choose one:

- pass
- pass with notes
- changes requested
- blocked
- escalate to Jounin
- escalate to Kage Summit

## Teachback

Explain what the user should understand before closing the mission.
```

## Completion requirements

A documentation review mission is complete only when:

1. The files reviewed are listed.
2. Findings are backed by evidence.
3. Sensitive content was checked.
4. Scope limits are stated.
5. Required escalations are identified.
6. Proposed changes are separated from approved changes.
7. Review decision is clear.
8. Teachback is provided.

## Violations

The following are violations:

- modifying files without explicit editing approval;
- reading files outside scope;
- exposing sensitive values in the report;
- inventing evidence;
- declaring documentation consistent without checking the relevant files;
- changing doctrine through a normal documentation edit;
- hiding uncertainty;
- marking a mission complete without review decision and teachback.

## Closing principle

Good documentation review protects the user from confusion, drift, and unsafe assumptions.

The reviewer should make the next action clear without taking unauthorized action.
