# Adapter Evidence Review Scroll

Status: public baseline.

This Scroll reviews whether an adapter invocation has enough evidence to proceed, be accepted, or be blocked.

## Purpose

Use this Scroll when reviewing adapter evidence before or after:

- file reads;
- patch proposals;
- command execution;
- local-private work;
- Git operations;
- release preparation;
- adapter result acceptance.

## Inputs

Required inputs:

```text
Mission Charter
adapter manifest
adapter permission matrix
adapter invocation request
adapter execution gate, if execution is requested
adapter evidence pack
adapter invocation result, if available
```

## Review questions

### Request evidence

- Is the requested adapter identified?
- Is the requested mode explicit?
- Are allowed paths and excluded paths listed?
- Are commands or tools listed when relevant?
- Is the expected output defined?
- Is the private context boundary explicit?

### Permission evidence

- Does the permission matrix allow the requested mode?
- Is technical capability separated from authorization?
- Are stop conditions listed?
- Are approval requirements clear?

### Execution evidence

If execution is requested:

- Is there an execution gate?
- Is dry-run evidence present when required?
- Is explicit user approval present?
- Are rollback notes present for risky changes?
- Is the command scope bounded?

### Git evidence

When Git is in scope:

- Was `git status` checked before action?
- Were unrelated changes present?
- Is the diff limited to allowed files?
- Was final `git status` recorded?

### Result evidence

After action:

- Are files read, changed, created, or deleted listed?
- Are commands suggested or executed listed?
- Are errors and warnings recorded?
- Is validation documented?
- Are remaining risks stated?

## Verdicts

### Accept evidence

Evidence is sufficient and consistent with the Mission Charter.

### Accept with notes

Evidence is sufficient, but there are minor documentation gaps.

### Needs more evidence

The invocation or result may be valid, but evidence is incomplete.

### Block

Evidence shows a safety, privacy, authorization, Git, or scope issue.

## Stop conditions

Stop review and block if:

- evidence contains secrets or sensitive data;
- private content is copied into public outputs;
- approval is missing for execution;
- permission matrix does not allow the action;
- execution gate is missing;
- Git has unrelated changes and the request touches Git;
- commands are destructive without explicit authorization;
- result claims changes without showing evidence.

## Output

The review must state:

```text
Verdict:
Reason:
Evidence accepted:
Evidence missing:
Required follow-up:
```

Do not approve an adapter invocation based on trust, reputation, or technical capability alone.
