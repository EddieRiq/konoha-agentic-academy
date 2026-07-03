# Teachback Scroll

## Status

Draft.

## Purpose

This Scroll defines how an agent helps the user understand a completed mission before the mission is closed.

Teachback is the final learning and ownership step. It confirms that the user can explain what changed, why it changed, how to use it, what risks remain, and what evidence supports the result.

## Core rule

A mission is not complete until the user can explain the outcome.

Agent delivery is not the same as user completion.

## Authority

This Scroll follows and cannot override:

- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/teachback/teachback_policy.md`
- `protocols/mission-charter/mission_charter.md`
- `protocols/context/context_policy.md`
- `protocols/approval/approval_policy.md`
- `protocols/review/review_policy.md`
- `protocols/safety/safety_policy.md`

If this Scroll conflicts with any higher policy, the higher policy wins.

## When to use this Scroll

Use this Scroll when a mission produced something the user may need to operate, review, defend, maintain, explain, or approve.

Examples:

- code changes;
- repository changes;
- documentation changes;
- data pipelines;
- model workflows;
- dashboards;
- architecture decisions;
- Git operations;
- mission reports;
- learning proposals;
- public release preparation.

Teachback may be skipped only when the Mission Charter explicitly sets a lower closure level and the work is low risk.

## What teachback is not

Teachback is not:

- a celebration message;
- a generic summary;
- a replacement for review;
- a replacement for tests;
- a way to pressure the user;
- a request for blind approval;
- a memory update by itself;
- permission to execute more work.

Teachback explains completed work. It does not expand scope.

## Required inputs

Before teachback, the agent should have:

- approved Mission Charter;
- mission output;
- evidence gathered during execution;
- review outcome, if required;
- list of files changed or artifacts created;
- remaining risks or assumptions;
- commands executed, if any;
- validation results, if any.

If required evidence is missing, stop and report the gap.

## Teachback levels

### Level 0: acknowledgement

Use for very small read-only tasks.

The user only needs to know what was found and what remains open.

### Level 1: operational summary

Use for low-risk deliverables.

The user should understand:

- what was done;
- where the output is;
- how to use it;
- what to check next.

### Level 2: defendable explanation

Use for technical work, repo changes, process changes, policy changes, or public content.

The user should be able to explain:

- what changed;
- why it changed;
- what alternatives were considered;
- what evidence supports it;
- what risks remain;
- how to validate it again.

### Level 3: formal handoff

Use for high-risk, sensitive, production, architecture, security, model, data, or doctrine work.

The user should be able to:

- explain the full decision path;
- identify who approved the work;
- describe the evidence;
- describe rollback or recovery options;
- explain operational impact;
- state what is not covered.

Level 3 may require Jounin review or Kage Summit before closure.

## Workflow

### 1. Restate the mission

State the original mission in one or two sentences.

Do not rewrite the mission to make the result look better.

### 2. State what changed

List the actual outputs.

For repository work, include paths.

For commands, include only safe command names and relevant outcomes. Do not reveal secrets or sensitive values.

### 3. Explain why it changed

Explain the reason behind the work.

Tie the explanation to the Mission Charter, user request, policy, or evidence.

### 4. Show evidence

Provide concrete evidence, such as:

- files created;
- files modified;
- checks run;
- tests passed or failed;
- diffs reviewed;
- logs summarized safely;
- validation outputs;
- reviewer verdicts.

Do not claim evidence that was not checked.

### 5. Explain how to use it

Give the user the next usable action.

Examples:

- where to place a file;
- which command to run;
- how to read a report;
- how to validate a result;
- what to inspect in GitHub;
- how to undo or amend if needed.

### 6. State risks and limits

Mention remaining risks plainly.

Examples:

- not tested locally;
- depends on a tool not installed;
- no external review done;
- assumes repo structure is unchanged;
- public safety review still needed;
- no production data was checked.

### 7. Ask for user teachback

Ask the user to explain the result back in their own words when the mission requires it.

Use a practical prompt, not an exam tone.

Example:

```text
Before we close this mission, explain back in your own words:
1. What changed?
2. Why was it needed?
3. What would you check before publishing or using it?
```

### 8. Correct gently

If the user misses something important, correct the gap directly.

Do not shame the user.

Do not declare completion until the important points are understood.

### 9. Close the mission

Close only when:

- required review is complete;
- required evidence is present;
- the user understands the result at the required level;
- remaining risks are documented;
- memory or learning steps are handled if approved.

## Teachback report format

Use this format for medium or high-risk missions:

```markdown
# Teachback report

## Mission

[Original mission]

## Output

- [Output 1]
- [Output 2]

## Why it matters

[Plain explanation]

## Evidence

- [Evidence 1]
- [Evidence 2]

## How to use it

[Concrete next action]

## Risks and limits

- [Risk 1]
- [Risk 2]

## User teachback

Status: pending | passed | needs correction | skipped by charter

Notes:
[Notes]

## Closure

Status: open | closed | blocked
Reason:
[Reason]
```

## Agent behavior

Agents must:

- use plain language;
- separate facts from assumptions;
- avoid inflated claims;
- admit missing evidence;
- keep the user oriented;
- focus on ownership, not performance theater;
- avoid exposing secrets or private context;
- stop when teachback reveals misunderstanding that affects safe use.

Agents must not:

- say the mission is complete just because files were created;
- hide failed checks;
- invent tests;
- claim review happened when it did not;
- pressure the user into approval;
- turn teachback into a long lecture;
- add new tasks without a new Mission Charter.

## Stop conditions

Stop and ask for clarification when:

- the user cannot explain a high-risk outcome;
- evidence is missing;
- review is missing;
- the output may contain sensitive content;
- the user wants to publish before safety review;
- the mission scope changed during teachback;
- the user asks for new execution steps not covered by the current charter.

## Interaction with memory

Teachback may generate useful memory, but memory updates require permission.

Allowed without memory approval:

- explaining the result;
- summarizing current mission outcome;
- pointing out possible lessons.

Not allowed without explicit approval:

- writing memory notes;
- updating local Village memory;
- promoting lessons to doctrine;
- storing sensitive details;
- storing user private context.

## Interaction with learning

If teachback reveals a reusable lesson, the agent may propose a Learning Proposal.

The proposal must remain separate from doctrine until reviewed and approved.

## Completion checklist

Before closing a teachback mission, confirm:

- [ ] The mission was restated accurately.
- [ ] Outputs were listed.
- [ ] Evidence was shown.
- [ ] Usage instructions were provided.
- [ ] Risks and limits were stated.
- [ ] Required review was completed or marked as missing.
- [ ] User understanding was confirmed at the required level.
- [ ] No new scope was silently added.
- [ ] Memory or learning updates were handled only if approved.

## Final rule

Teachback is not about making the agent look successful.

Teachback is about making the user capable.
