# Adapter Contract Review Scroll

Status: public Scroll.

Use this Scroll to review a proposed adapter before it is used in a mission.

This Scroll reviews contracts. It does not grant execution authority.

## Purpose

The Adapter Contract Review Scroll helps a Jounin, Local Kage, or Hokage verify that an adapter is narrow, safe, reviewable, and compatible with Konoha doctrine.

## Inputs

Required inputs:

- adapter manifest;
- adapter capabilities document;
- adapter safety checklist;
- Mission Charter, if the adapter is being reviewed for a specific mission.

Optional inputs:

- README;
- examples;
- test output;
- dry-run output;
- security notes;
- eval cases.

## Outputs

The reviewer must produce:

- review verdict;
- required changes;
- allowed scope, if approved;
- explicit stop conditions;
- validation evidence required before use.

## Non-goals

This Scroll must not:

- execute the adapter;
- approve broad autonomous behavior;
- bypass the Mission Charter;
- approve private context access without explicit authorization;
- promote local adapter behavior to public doctrine automatically.

## Review sequence

### 1. Confirm adapter identity

Check that the adapter has:

- a name;
- owner;
- type;
- location;
- public or local status;
- purpose;
- non-goals.

Stop if identity is ambiguous.

### 2. Check authority boundary

Verify that the manifest states:

- capability is not permission;
- Mission Charter is required for use;
- approval is required for writes, commands, network, publishing, memory, doctrine, commits, pushes, tags, and releases.

Stop if the adapter implies it can act merely because it exists.

### 3. Check execution boundary

Review:

- allowed directories;
- forbidden directories;
- allowed file operations;
- allowed commands or tools;
- network policy;
- dependency installation policy;
- cleanup expectations.

Stop if writes or commands are broad, vague, or unbounded.

### 4. Check input safety

Inputs must be explicit.

Reject or require changes if the adapter can read:

- credentials;
- `.env` files;
- local memory;
- private literature;
- private Village files;
- personal data;
- client data;
- internal infrastructure details;

unless the Mission Charter explicitly authorizes that access.

### 5. Check output safety

Outputs must not include:

- secrets;
- private source content;
- unapproved memory;
- unapproved doctrine changes;
- private paths when unnecessary;
- copyrighted source excerpts beyond safe limits;
- unsupported claims of mission completion.

### 6. Check validation

The adapter must define how results are validated.

Examples:

- dry run;
- test command;
- lint output;
- generated diff;
- file list;
- checksum;
- `git status`;
- `git diff`;
- manual review.

Stop if validation is not reproducible.

### 7. Check review requirements

Identify whether the adapter requires:

- Jounin review;
- security review;
- Local Kage approval;
- Hokage approval;
- Kage Summit escalation;
- user approval.

Escalate if authority is unclear.

### 8. Check failure modes

The adapter should document likely failures.

Examples:

- wrong working directory;
- path traversal;
- stale context;
- prompt injection;
- unbounded file search;
- dependency conflict;
- tool version mismatch;
- network failure;
- partial output;
- generated content that looks authoritative but is not validated.

Stop if high-risk failures are ignored.

## Verdicts

### Pass

Adapter contract is clear and safe for the stated scope.

### Pass with limits

Adapter may be used only within specific limits.

The limits must be written explicitly.

### Needs changes

Adapter contract is incomplete or unclear.

The adapter must not be used until changes are reviewed.

### Blocked

Adapter is unsafe, too broad, or conflicts with doctrine.

## Required review report

Use this format:

```markdown
# Adapter contract review

Adapter: `<adapter-name>`

Verdict: `<pass | pass with limits | needs changes | blocked>`

## Scope reviewed

## Evidence reviewed

## Allowed operations

## Forbidden operations

## Required approvals

## Stop conditions

## Required validation

## Risks

## Required changes

## Final note
```

## Stop conditions

Stop the review if:

- the adapter has no manifest;
- the adapter has no explicit scope;
- the adapter can act without Mission Charter approval;
- private context boundaries are unclear;
- shell, network, or write access is unbounded;
- validation is missing;
- the reviewer cannot explain what the adapter is allowed to do and what it must not do.

## Teachback

Before approving operational use, the user should be able to explain:

- what the adapter connects to;
- what it can do;
- what it is allowed to do;
- what it must never do;
- what evidence confirms it stayed within scope.
