# Adapter Dry-Run Review Scroll

Status: public baseline.

This Scroll reviews adapter dry-run requests and results before any action moves toward execution.

## Purpose

Use this Scroll when a mission asks an adapter to simulate file changes, command execution, release actions, local-private work, or other side-effecting behavior.

The Scroll ensures that dry-run remains planning only.

## Inputs

Required inputs:

- Mission Charter;
- adapter manifest;
- adapter permission matrix;
- adapter invocation request;
- dry-run request;
- relevant safety checklist;
- repository status, if applicable.

Optional inputs:

- evidence pack;
- execution gate draft;
- previous dry-run result;
- review notes;
- Kage Summit verdict.

## Review steps

### 1. Confirm mission authority

Check that the Mission Charter allows the requested planning activity.

If the Mission Charter does not mention the adapter, scope, or permission level, stop.

### 2. Confirm dry-run mode

Classify the request as one of:

- read-only dry-run;
- patch-planning dry-run;
- command-planning dry-run;
- release-planning dry-run;
- local-private dry-run.

If the mode is unclear, stop.

### 3. Check adapter permissions

Compare the request against the adapter permission matrix.

A technical capability is not authorization.

If requested behavior exceeds permission level, block or escalate.

### 4. Check scope

Validate:

- allowed paths;
- blocked paths;
- files to read;
- files to propose changing;
- local/private paths;
- Git operations;
- dependency operations;
- release operations.

Ambiguous scope is a stop condition.

### 5. Check private-context boundary

If private or ignored content is involved, confirm explicit authorization.

The adapter must not copy private content into public outputs.

### 6. Check proposed commands

Dry-run may describe commands but must not execute them.

Command proposals must include:

- command text;
- expected purpose;
- expected side effects;
- files or services affected;
- rollback or recovery notes.

### 7. Check evidence

A valid dry-run result should state what evidence it used.

Unsupported assumptions must be marked as assumptions or removed.

### 8. Check output contract

The dry-run result must include:

- proposed reads;
- proposed changes;
- proposed commands;
- risk review;
- privacy review;
- Git impact;
- dependency impact;
- rollback notes;
- explicit approval requirement;
- final recommendation.

### 9. Decide

Allowed verdicts:

- block;
- revise request;
- approve planning only;
- recommend execution gate review;
- escalate to Kage Summit.

The Scroll must not approve execution directly.

## Stop conditions

Stop if:

- execution already happened during dry-run;
- files were modified during dry-run;
- commands were run without authorization;
- scope is unclear;
- private context was accessed without explicit approval;
- output includes private or copyrighted source material;
- Git status is dirty and unexplained;
- adapter permissions are missing;
- the dry-run result claims execution approval.

## Output

The reviewer should produce:

- verdict;
- required revisions;
- risks;
- evidence gaps;
- whether execution gate review is allowed;
- teachback note for the user.

## Completion criteria

Dry-run review is complete only when the user can explain:

- what the adapter would do;
- what it would not do;
- what evidence supports the plan;
- what approval is still required;
- why dry-run is not execution.
