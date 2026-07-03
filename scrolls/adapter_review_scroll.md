# Adapter Review Scroll

## Status

Draft.

## Purpose

This Scroll defines a safe, read-only workflow for reviewing adapters before they are trusted by the Academy or by a Local Village.

Adapters connect Konoha to external systems such as model providers, local runtimes, Git platforms, notification services, Obsidian vaults, voice tools, CI systems, package managers, and operating system interfaces.

Adapters are useful because they let the Academy work across different tools.

Adapters are risky because they cross a boundary.

## Core rule

Adapters connect systems.

They do not grant authority.

No adapter may authorize actions, expand mission scope, bypass safety, hide uncertainty, persist sensitive content by default, rewrite doctrine, or override local Village rules.

## When to use this Scroll

Use this Scroll when reviewing:

- a new adapter;
- a change to an existing adapter;
- an adapter imported from an external source;
- a local adapter created for an Allied Village;
- an adapter that connects to a private machine, vault, repo, API, model, service, or notification channel;
- an adapter involved in command execution, file access, memory, network access, credentials, telemetry, or UI events.

## What this Scroll is not

This Scroll is not permission to install, run, execute, publish, or trust an adapter.

This Scroll is not a security audit certificate.

This Scroll is not approval to connect to private services.

This Scroll does not replace the Safety Policy, Context Policy, Approval Policy, Review Policy, Marketplace rules, or Mission Charter.

## Required authority

Adapter review is read-only by default.

The reviewer may inspect adapter documentation, configuration examples, source code, declared capabilities, tests, metadata, and expected behavior.

The reviewer may not run the adapter, connect it to an external system, create credentials, call APIs, inspect local machines, write files, change configuration, or publish findings unless those actions are explicitly allowed by an approved Mission Charter.

## Inputs

Before review, collect:

- adapter name;
- source or origin;
- intended purpose;
- owner or maintainer;
- target system;
- declared capabilities;
- required permissions;
- configuration files;
- environment variables;
- expected inputs;
- expected outputs;
- data persisted by the adapter;
- logs or telemetry emitted by the adapter;
- dependency list;
- license;
- tests or validation examples;
- known limitations.

If any of these are missing, record the gap. Do not infer trust from missing information.

## Review workflow

### 1. Confirm mission scope

Confirm:

- what adapter is being reviewed;
- whether the review is for Academy public use or Local Village use;
- whether private context is involved;
- whether the adapter is read-only, write-capable, network-capable, execution-capable, or memory-capable;
- what the reviewer is allowed to inspect;
- what the reviewer is not allowed to inspect;
- what output is expected.

If the scope is unclear, stop and ask.

### 2. Identify trust boundary

Classify the adapter boundary.

Common boundaries:

- local filesystem;
- Git repository;
- GitHub, GitLab, or other remote Git provider;
- model provider API;
- local model runtime;
- Obsidian vault;
- notification service;
- voice input or output;
- shell or process execution;
- browser or web automation;
- database;
- cloud storage;
- CI/CD runner;
- package registry;
- telemetry sink.

An adapter that crosses more than one boundary has higher risk.

### 3. Review capability declaration

Check whether the adapter clearly declares what it can do.

Minimum declaration:

```yaml
name:
version:
status:
owner:
source:
license:
target_system:
capabilities:
permissions_required:
network_access:
filesystem_access:
command_execution:
memory_access:
telemetry:
sensitive_data_handling:
configuration:
failure_modes:
review_status:
```

The declaration must match the actual behavior.

If the adapter claims to be read-only but can write, execute, persist, or transmit data, mark it as blocked until clarified.

### 4. Review permissions

List the permissions requested by the adapter.

Separate them into:

- required for core function;
- optional;
- excessive;
- unclear;
- dangerous.

Examples of dangerous permissions:

- unrestricted filesystem access;
- shell execution;
- recursive directory scanning;
- access to home directories;
- access to `.env`, SSH keys, tokens, or credential stores;
- access to private Obsidian vaults without explicit path scope;
- outbound network access to unspecified hosts;
- write access to repositories;
- ability to push, publish, deploy, or delete resources;
- silent background execution;
- automatic persistence of prompts, outputs, logs, transcripts, or memory.

Dangerous permissions require explicit approval and review.

### 5. Review configuration and secrets

Check:

- whether secrets are required;
- where secrets are expected to live;
- whether `.env` or credential files are ignored by Git;
- whether examples use placeholders;
- whether logs redact secrets;
- whether errors can print tokens, passwords, paths, headers, or connection strings;
- whether configuration supports least privilege;
- whether local overrides are supported safely.

Adapters must not require hardcoded secrets.

Adapters must not commit local configuration.

Adapters must not print full credentials.

### 6. Review data handling

Identify what data the adapter reads, writes, sends, receives, caches, logs, or stores.

Classify data as:

- public;
- internal;
- local private;
- sensitive;
- secret;
- unknown.

For sensitive, secret, or unknown data, the adapter must have explicit handling rules.

Check whether the adapter:

- minimizes data;
- redacts logs;
- avoids storing raw prompts by default;
- avoids storing transcripts by default;
- supports dry-run mode when possible;
- has clear retention behavior;
- separates public Academy memory from Local Village memory;
- avoids leaking local paths or private project names into public outputs.

### 7. Review command execution

If the adapter can run commands, mark it high risk.

Check:

- command allowlist;
- command blocklist;
- argument validation;
- working directory control;
- environment variable handling;
- timeout behavior;
- dry-run support;
- logging;
- output redaction;
- exit-code handling;
- prompt injection risk;
- protection against command composition from untrusted model output.

No adapter should execute arbitrary model-generated commands without approval.

### 8. Review filesystem behavior

Check:

- allowed root paths;
- blocked paths;
- symlink behavior;
- recursive traversal;
- hidden files;
- generated files;
- overwrite behavior;
- temp file cleanup;
- binary file handling;
- large file handling;
- file extension filters;
- path normalization;
- path traversal protection.

Adapters must not access private directories by default.

Adapters must not follow paths into ignored Local Villages unless explicitly allowed.

### 9. Review network behavior

Check:

- whether outbound network access is required;
- destination hosts;
- protocols;
- authentication method;
- retries;
- timeouts;
- rate limits;
- telemetry;
- error reporting;
- dependency downloads;
- update checks.

Outbound network access to unknown destinations is not acceptable for trusted use.

Auto-update behavior must be explicit.

### 10. Review memory and telemetry behavior

Check:

- what events the adapter emits;
- whether telemetry includes sensitive content;
- whether telemetry can be disabled;
- whether memory writes require approval;
- whether local memory is separated from public Academy memory;
- whether summaries are clearly marked as summaries;
- whether raw context is stored.

Telemetry observes. It does not authorize.

Memory supports action. It does not authorize.

### 11. Review dependency risk

Check:

- direct dependencies;
- transitive dependency exposure;
- package manager;
- lockfile;
- version pinning;
- license compatibility;
- install scripts;
- post-install hooks;
- binary downloads;
- native extensions;
- abandoned packages;
- dependency confusion risk.

If dependency risk is unclear, use the Dependency Review Scroll.

### 12. Review failure modes

The adapter must fail safely.

Check behavior when:

- credentials are missing;
- permissions are insufficient;
- network is unavailable;
- target service changes API;
- rate limit is hit;
- output is malformed;
- filesystem path is missing;
- command fails;
- adapter receives unsafe input;
- user cancels;
- model output is ambiguous.

Failing safely means stopping, reporting evidence, and asking for approval when needed.

### 13. Review tests and evals

Check whether there are tests for:

- read-only mode;
- denied permission;
- invalid config;
- missing credentials;
- secret redaction;
- path restrictions;
- blocked command execution;
- network timeout;
- malformed response;
- dry-run behavior;
- logging safety.

Adapters that can write files, run commands, access networks, or handle sensitive data require stronger tests.

### 14. Assign review status

Use one of these statuses:

```text
unreviewed
reviewed-with-gaps
tested-limited
approved-for-local-use
approved-for-academy-use
deprecated
blocked
```

Do not mark an adapter as approved unless the evidence supports it.

A Local Village may approve an adapter for local use without making it approved for Academy public use.

## Risk levels

### Low risk

Read-only adapter with no network access, no secret access, no memory writes, no command execution, and limited filesystem scope.

### Medium risk

Adapter with limited network access, limited write behavior, local configuration, or telemetry without sensitive content.

### High risk

Adapter with command execution, repository write access, memory writes, access to private context, access to credentials, or broad filesystem/network permissions.

### Blocked risk

Adapter that hides behavior, requires hardcoded secrets, transmits unknown data, executes arbitrary commands, bypasses approvals, stores sensitive content by default, or cannot be inspected.

## Stop conditions

Stop the review and ask for guidance if:

- the adapter requires credentials that were not explicitly approved;
- the adapter accesses private paths;
- the adapter can execute shell commands;
- the adapter can write, delete, push, deploy, or publish;
- the adapter can transmit data externally;
- the adapter stores prompts, transcripts, outputs, or memory by default;
- the adapter behavior does not match its declaration;
- the source or license is unclear;
- dependency risk is unclear;
- there is any sign of obfuscated behavior;
- private or sensitive content appears in examples, logs, tests, or documentation.

## Adapter review report

Use this structure:

```markdown
# Adapter review report

## Adapter

- Name:
- Source:
- Version:
- Target system:
- Review date:
- Reviewer:
- Mission ID:

## Scope reviewed

## Intended use

## Declared capabilities

## Observed capabilities

## Trust boundaries

## Permissions requested

## Data handling

## Secrets and configuration

## Filesystem behavior

## Network behavior

## Command execution

## Memory and telemetry

## Dependencies

## Tests and evals

## Failure modes

## Risks

## Missing information

## Required approvals

## Recommendation

Status:

Reason:

## Evidence

- File:
- Section:
- Command output:
- Test:
- Diff:
```

## Allowed outputs

The reviewer may produce:

- an adapter review report;
- a risk classification;
- a list of missing information;
- a list of required approvals;
- a recommendation;
- a follow-up Mission Charter draft.

The reviewer may not silently modify the adapter.

## Approval before activation

Before an adapter becomes active, the Academy or Local Village must have:

- clear purpose;
- declared capabilities;
- scoped permissions;
- reviewed configuration;
- reviewed secret handling;
- reviewed filesystem behavior;
- reviewed network behavior;
- reviewed memory and telemetry behavior;
- reviewed dependencies;
- review status;
- required tests;
- explicit approval.

## Completion checklist

Before closing the review, confirm:

- [ ] Adapter purpose is clear.
- [ ] Source and license are known.
- [ ] Capabilities are declared.
- [ ] Actual behavior matches declared behavior.
- [ ] Trust boundaries are identified.
- [ ] Permissions are scoped.
- [ ] Secrets are not hardcoded.
- [ ] Sensitive data handling is explicit.
- [ ] Filesystem access is limited.
- [ ] Network behavior is known.
- [ ] Command execution risk is reviewed.
- [ ] Memory and telemetry behavior is reviewed.
- [ ] Dependencies are reviewed or routed to Dependency Review Scroll.
- [ ] Failure modes are documented.
- [ ] Tests or evals are identified.
- [ ] Recommendation is evidence-based.
- [ ] Required approvals are listed.
