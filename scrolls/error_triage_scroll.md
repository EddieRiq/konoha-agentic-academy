# Error triage scroll

Status: draft  
Scope: troubleshooting, diagnostics, root-cause analysis, and safe recovery planning  
Default mode: read-only diagnostics

## Core rule

Root cause before fix.

An agent may inspect evidence, summarize failures, propose diagnostics, and draft recovery plans. It may not edit files, delete outputs, change configuration, restart services, rerun costly jobs, rotate credentials, install dependencies, or apply fixes unless those actions are explicitly allowed by an approved Mission Charter.

## Purpose

This Scroll defines how Konoha agents triage errors without guessing, hiding uncertainty, or making the system worse.

Use it when a mission involves:

- failing commands;
- failing tests;
- broken scripts;
- dependency errors;
- Git errors;
- CI failures;
- runtime exceptions;
- model scoring failures;
- data pipeline failures;
- missing files or paths;
- environment issues;
- configuration problems;
- unexpected outputs;
- failed adapters, tools, or Scrolls.

## Non-purpose

This Scroll does not authorize:

- applying fixes automatically;
- modifying production systems;
- deleting files;
- overwriting outputs;
- changing secrets;
- changing remotes or branch history;
- editing doctrine;
- bypassing review;
- treating a workaround as a root-cause fix;
- declaring the issue resolved without evidence.

## Required inputs

Before triage, collect the smallest useful context:

```text
- What command, workflow, tool, or process failed?
- What was the expected outcome?
- What actually happened?
- What changed recently?
- What environment was used?
- What files, paths, configs, or dependencies are involved?
- Is this local, CI, production, sandbox, or an Allied Village?
```

If the mission lacks enough context to distinguish likely causes, stop and ask for the smallest missing piece.

## Safety boundaries

Error triage must follow:

```text
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
protocols/safety/safety_policy.md
protocols/context/context_policy.md
protocols/approval/approval_policy.md
protocols/review/review_policy.md
protocols/mission-charter/mission_charter.md
sandbox/README.md
```

Safety overrides speed.

Do not request or reproduce secrets. If a log contains credentials, tokens, personal data, internal URLs, or private paths, summarize the risk without repeating the value.

## Default allowed actions

Unless the Mission Charter says otherwise, the agent may:

```text
- read the provided error message;
- inspect provided logs;
- inspect relevant read-only files;
- ask clarifying questions;
- classify the failure;
- identify likely causes with evidence;
- separate confirmed facts from hypotheses;
- propose diagnostic commands;
- propose safe fixes;
- propose rollback or recovery steps;
- draft a report.
```

## Actions requiring explicit approval

The following require explicit approval in the Mission Charter:

```text
- editing files;
- running state-changing commands;
- installing, upgrading, or removing dependencies;
- deleting files or outputs;
- overwriting generated data;
- restarting services;
- changing environment variables;
- changing credentials or connection strings;
- running long or costly jobs;
- pushing commits;
- amending commits;
- force-pushing;
- changing CI/CD configuration;
- accessing private local context;
- inspecting local machines beyond approved paths;
- using external services or network calls;
- changing doctrine.
```

## Triage workflow

### 1. Restate the failure

Begin by restating the issue in plain terms.

Use this format:

```text
Failure:
Expected:
Actual:
Environment:
Most relevant evidence:
```

Do not jump to a fix before identifying the failure mode.

### 2. Classify the error

Classify the error into one or more categories:

```text
- syntax or parsing;
- missing file or path;
- permissions;
- dependency or version mismatch;
- environment configuration;
- credentials or authentication;
- network or external service;
- data schema;
- data quality;
- key or join logic;
- memory or performance;
- test expectation mismatch;
- Git state;
- CI/CD pipeline;
- model artifact compatibility;
- runtime logic bug;
- documentation mismatch;
- user command mismatch;
- unknown.
```

Use `unknown` when evidence is insufficient.

### 3. Separate evidence from hypotheses

The report must distinguish:

```text
Confirmed:
Supported by the log, command output, file contents, or reproducible behavior.

Likely:
Supported by evidence, but not fully proven.

Possible:
Plausible, but needs diagnostics.

Not supported:
Speculation without evidence.
```

Do not present a hypothesis as fact.

### 4. Identify the smallest safe diagnostic

Prefer diagnostics that are:

```text
- read-only;
- cheap;
- reversible;
- local;
- narrow;
- easy to explain;
- safe for public or sanitized logs.
```

Examples:

```bash
git status
git diff --stat
python --version
python -m pip show package_name
ls -la path/to/expected/file
grep -R "expected_name" path/
pytest path/to/test.py -q
```

Do not propose broad commands when a narrow command is enough.

### 5. Diagnose before fixing

A valid diagnosis should answer:

```text
- What failed?
- Where did it fail?
- Why did it fail?
- What evidence supports that explanation?
- What is the smallest safe fix?
- What could break if the fix is wrong?
- How will we validate the fix?
```

If the root cause is not confirmed, propose a diagnostic plan instead of a fix.

### 6. Propose fixes by risk level

Group possible fixes by risk:

```text
Low risk:
Documentation-only, local path correction, command correction, read-only config verification.

Medium risk:
Code change, dependency pin, test update, generated file regeneration, local environment change.

High risk:
Data overwrite, production behavior change, credential rotation, schema migration, CI/CD change, branch history rewrite.

Blocked:
Requires secrets, private data, production access, legal/security decision, or doctrine change.
```

High-risk fixes require review and explicit human approval.

### 7. Validate the fix

Every proposed fix must include validation.

Use this format:

```text
Validation command:
Expected output:
Failure signal:
Rollback or next step:
```

A mission is not resolved because the agent thinks the fix is correct. It is resolved when validation evidence supports it and required review is complete.

## Error-specific guidance

### Git errors

For Git failures, prefer:

```bash
git status
git log --oneline -5
git branch -vv
git remote -v
git diff --stat
```

Do not recommend `reset --hard`, `rebase`, `amend`, `push --force`, or branch deletion unless the Mission Charter explicitly allows it and the user understands the consequence.

Use `--force-with-lease` over `--force` when history rewrite is explicitly approved.

### Dependency errors

For dependency failures, inspect versions before installing or upgrading.

Prefer:

```bash
python --version
python -m pip --version
python -m pip show <package>
python -m pip freeze | grep <package>
```

Do not install packages globally by default.

Do not change lock files unless explicitly approved.

### Path errors

For path failures, check whether the command is being run from the expected root.

Prefer:

```bash
pwd
ls
ls path/to/parent
```

In WSL/Windows mixed environments, distinguish:

```text
PowerShell path:
C:\Users\username\Downloads\file.md

WSL path:
/mnt/c/Users/username/Downloads/file.md
```

Do not silently convert paths without confirming the shell context.

### Data errors

For data issues, do not patch symptoms with `drop_duplicates`, broad type coercion, or null filling before diagnosing.

Check:

```text
- row counts;
- key uniqueness;
- nulls in keys;
- duplicate keys;
- schema drift;
- date range;
- join cardinality;
- source coverage;
- sample of affected records using anonymized values.
```

Do not reproduce personal data or operation-level identifiers in reports.

### Model errors

For model scoring or training failures, check:

```text
- model artifact path;
- model version;
- feature list;
- feature order;
- missing columns;
- type mismatch;
- category handling;
- preprocessing pipeline;
- train/score compatibility;
- environment versions.
```

Do not retrain or replace model artifacts without explicit approval.

### CI/CD errors

For CI/CD failures, distinguish:

```text
- local-only issue;
- pipeline configuration issue;
- dependency issue;
- secret/permission issue;
- flaky test;
- environment mismatch;
- actual code regression.
```

Do not modify CI/CD config or secrets without approval.

### Adapter or tool errors

For Konoha adapter or tool failures, determine whether the issue is:

```text
- missing capability;
- misconfigured adapter;
- external service unavailable;
- permission denied;
- invalid input;
- output schema mismatch;
- unsafe requested action;
- tool bug.
```

Adapters and tools may fail closed. Do not bypass a failed safety check.

## Stop conditions

Stop and ask when:

```text
- the error log is incomplete;
- the command that failed is unknown;
- the shell or environment is ambiguous;
- the likely fix changes files or state;
- the issue may involve credentials;
- the issue may involve private data;
- the issue may involve production;
- the issue may require destructive commands;
- the issue may require dependency changes;
- the issue may require network access;
- the issue may require doctrine changes;
- the agent cannot distinguish between two risky causes.
```

Ask the smallest useful question.

## Reporting format

Use this report structure:

```text
# Error triage report

## Summary

One or two sentences describing the failure.

## Evidence reviewed

- Command:
- Error message:
- Relevant files:
- Environment:
- Recent changes:

## Classification

Primary category:
Secondary category:

## Confirmed facts

- ...

## Likely cause

- ...

## Hypotheses still open

- ...

## Recommended next diagnostic

Command:
Why:
Expected result:

## Proposed fix

Only include this if root cause is sufficiently supported.

## Risk level

Low / Medium / High / Blocked

## Validation

Command:
Expected output:
Failure signal:

## Stop conditions

Any remaining blocker or required approval.
```

## Evidence standard

Reports must cite concrete evidence:

```text
- exact command;
- exact file path;
- exact error class or message, sanitized if needed;
- relevant line number when available;
- test name;
- Git commit or branch when relevant;
- environment or version when relevant.
```

Do not cite confidence as evidence.

## Interaction with Mission Charter

If triage reveals that the mission requires actions outside the approved Charter, the agent must stop and request a Charter update.

Examples:

```text
- read-only triage discovers a needed code edit;
- local diagnostics require accessing private files;
- a proposed fix requires dependency installation;
- validation requires running a state-changing process;
- recovery requires Git history rewrite.
```

## Interaction with review

Review is required when:

```text
- the proposed fix changes code;
- the proposed fix changes data;
- the proposed fix changes configuration;
- the proposed fix changes dependencies;
- the proposed fix changes Git history;
- the error affects safety, security, memory, adapters, tools, or doctrine;
- the diagnosis is uncertain but action is still proposed.
```

## Interaction with learning

After resolution, the agent may propose a learning note when:

```text
- the same error is likely to recur;
- the root cause reveals a missing check;
- the workflow needs a safer diagnostic;
- documentation was unclear;
- a template or Scroll needs improvement.
```

The learning note does not become doctrine unless reviewed and approved.

## Violations

The following are violations:

```text
- applying a fix before diagnosis;
- hiding uncertainty;
- inventing a root cause;
- deleting or overwriting data without approval;
- exposing secrets in a report;
- reproducing personal data;
- using broad destructive commands;
- modifying files during read-only triage;
- changing dependencies without approval;
- bypassing failed safety checks;
- declaring resolution without validation evidence.
```

## Completion checklist

Before closing error triage:

```text
- failure was restated accurately;
- evidence was reviewed;
- error category was identified;
- facts and hypotheses were separated;
- diagnostics were minimal and safe;
- proposed fix matches the evidence;
- risk level was stated;
- validation path was defined;
- required approvals were identified;
- no sensitive values were reproduced;
- user can explain what failed, why, and what happens next.
```
