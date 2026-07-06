# Adapter contracts

Status: public guide.

Adapter contracts define how Konoha may connect doctrine to external execution environments without granting uncontrolled authority.

This guide is a baseline for future adapters. It does not implement an executable runtime.

## Purpose

Konoha separates doctrine from execution.

An adapter is the boundary layer between Konoha instructions and an external executor, such as a coding assistant, local model, shell runner, CI job, notebook, or tool wrapper.

The adapter contract answers:

- what the adapter can do;
- what it is allowed to do;
- what evidence is required before using it;
- when it must stop;
- who must review it;
- how public/private boundaries are preserved.

## Core rule

Capability is not permission.

An adapter may be technically capable of reading files, writing files, running commands, accessing the network, or generating artifacts. That does not mean it is authorized to do so.

Permission comes from:

- the Mission Charter;
- Konoha laws;
- approval policy;
- safety policy;
- review policy;
- local Village rules;
- explicit user approval.

## Adapter lifecycle

### 1. Draft

Create an adapter manifest and capabilities document.

Use:

```text
adapters/templates/adapter_manifest.template.md
adapters/templates/adapter_capabilities.template.md
adapters/templates/adapter_safety_checklist.template.md
```

### 2. Review

A Jounin reviews the adapter for clarity, scope, safety, and public/private boundaries.

A security reviewer is required when the adapter can execute shell commands, access the network, install dependencies, publish outputs, or touch credentials.

### 3. Limited approval

The adapter may be approved for a narrow mission type or a limited directory.

Approval must state:

- allowed paths;
- allowed operations;
- required validation;
- stop conditions;
- expiration or review trigger.

### 4. Use in a Mission Charter

The Mission Charter must explicitly name the adapter and the role it plays.

The adapter must not act merely because it exists.

### 5. Post-run review

After execution, the operator must report:

- commands or tools used;
- files read or changed;
- validation evidence;
- unresolved risks;
- whether the mission stayed within scope.

## Adapter types

### Coding assistant adapter

Used to generate, review, or modify code.

Default mode should be read-only or draft-only unless write permission is explicitly granted.

### Shell runner adapter

Used to run commands.

Requires strong path controls, explicit commands, and stop conditions.

### Local model adapter

Used to route prompts to a local model.

Must not assume the local model can access private files unless the Mission Charter allows it.

### Hosted model adapter

Used to call an external model provider.

Requires privacy review, especially when prompts may contain private context.

### CI adapter

Used to run tests, linting, evaluations, or release checks.

Must report evidence and avoid publishing secrets.

### Tool wrapper adapter

Used to wrap one specific tool, such as a converter, formatter, linter, parser, or evaluator.

The wrapper should expose narrow behavior rather than broad shell access.

## Required files for a proposed adapter

A proposed adapter should include:

```text
adapter_manifest.md
adapter_capabilities.md
adapter_safety_checklist.md
```

Optional files:

```text
README.md
examples/
evals/
tests/
```

## Public/private boundary

Public adapter contracts may describe generic patterns, commands, and safeguards.

They must not include:

- local Village content;
- private prompts;
- private memory;
- credentials;
- internal server names;
- client data;
- proprietary documents;
- copied source material from private literature;
- local dependency locks unless intentionally public.

Local adapters may live inside a private Village and remain ignored by Git.

## Local Village adapter convention

A local Village may define its own adapters under:

```text
alliance/<village-name>/adapters/
```

Local adapter dependencies should remain local.

Recommended local convention:

```text
alliance/<village-name>/.venv/
alliance/<village-name>/requirements.local.txt
alliance/<village-name>/requirements.lock.local.txt
```

The public repository should not require local Village dependencies.

## Stop conditions

Stop and ask before continuing if:

- the adapter would access private context not listed in the Mission Charter;
- the adapter would write outside approved paths;
- the adapter would run a destructive command;
- the adapter would install dependencies without approval;
- the adapter would publish generated content;
- the adapter would commit, push, tag, or release;
- the adapter would update memory or doctrine;
- the adapter behavior differs from its manifest.

## Review questions

Before approving an adapter, ask:

- Is the adapter's purpose narrow enough?
- Are allowed paths explicit?
- Are forbidden paths explicit?
- Are outputs safe?
- Is validation reproducible?
- Does it preserve local/private boundaries?
- Does it require network or shell access?
- Does it make authority ambiguous?
- Is there a clear rollback or cleanup path?

## Relationship to future runtime

This guide prepares the contract layer before runtime implementation.

Future runtime work should consume adapter manifests and enforce them mechanically.

Until then, adapter contracts are documentation and review artifacts, not automated controls.
