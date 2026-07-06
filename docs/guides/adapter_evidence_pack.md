# Adapter Evidence Pack

Status: public baseline.

The Adapter Evidence Pack defines the minimum evidence required before, during, and after an adapter invocation.

It does not implement adapter runtime. It defines documentation, review, and audit expectations.

## Purpose

Adapters may be able to read files, propose patches, run commands, or interact with local tools.

Capability is not authorization.

An adapter invocation must leave enough evidence for a reviewer to answer:

- what was requested;
- what was allowed;
- what was blocked;
- what evidence was checked before action;
- what changed;
- what did not change;
- what risks remain.

## Relationship to other adapter documents

Use this guide with:

```text
docs/guides/adapter_contracts.md
docs/guides/adapter_permission_matrix.md
docs/guides/adapter_invocation_contract.md
docs/guides/adapter_execution_gate.md
```

The evidence pack is the audit trail around those controls.

## Required evidence layers

### 1. Request evidence

Before invocation, the request must show:

- adapter profile;
- requested mode;
- requested files, folders, commands, or tools;
- Mission Charter reference;
- permission level;
- expected output;
- known exclusions;
- private context boundary.

### 2. Pre-execution evidence

Before execution, the reviewer must record:

- current Git status when Git is in scope;
- selected permission matrix;
- execution gate decision;
- dry-run or propose-only result when required;
- explicit approval status;
- stop conditions checked.

### 3. Action evidence

During execution or proposal generation, the adapter must record:

- commands suggested or executed;
- files read;
- files proposed for change;
- files changed;
- generated outputs;
- errors and warnings;
- deviations from the request.

### 4. Post-execution evidence

After the invocation, the result must show:

- final status;
- Git status when Git is in scope;
- diff summary when files changed;
- tests or validation performed;
- rollback notes when applicable;
- unresolved risks;
- whether user teachback is required.

## Evidence quality rules

Evidence must be specific enough to review.

Avoid vague statements such as:

```text
Checked everything.
Looks good.
No issues found.
```

Prefer concrete statements such as:

```text
Ran git status. Working tree had no staged changes before execution.
Read only docs/guides/adapter_invocation_contract.md and adapters/README.md.
No command execution was requested or performed.
```

## Sensitive information rules

Evidence must not include:

- secrets;
- tokens;
- credentials;
- private keys;
- personal data;
- customer data;
- private project details not approved for the report;
- long copyrighted excerpts;
- local private literature content.

If sensitive data appears during execution, stop and report the exposure without reproducing the sensitive value.

## Git evidence

When Git is in scope, record:

```text
git status
git diff --stat
git diff -- <allowed paths>
git log --oneline -5
```

Do not run destructive Git commands unless the Mission Charter explicitly allows them.

## Command evidence

For commands, record:

- command text;
- purpose;
- allowed scope;
- expected outcome;
- actual outcome;
- exit status when available;
- relevant summarized output.

Do not record secrets or full logs containing sensitive data.

## File evidence

For files, record:

- paths read;
- paths changed;
- paths created;
- paths deleted;
- paths explicitly excluded.

If private paths are involved, report only approved path-level evidence.

## Stop conditions

Stop if:

- requested evidence would expose private or sensitive content;
- Mission Charter does not define the adapter mode;
- permission matrix does not allow the requested action;
- execution gate is missing;
- dry-run evidence is required but absent;
- Git status contains unrelated changes;
- command scope is unclear;
- rollback path is unclear for risky changes.

## Completion criteria

An adapter invocation is complete only when:

- request evidence exists;
- pre-execution evidence exists when execution is requested;
- action evidence or no-action evidence exists;
- post-execution evidence exists;
- any gaps are explicitly listed;
- the user can understand what happened and why.
