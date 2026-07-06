# Adapter Invocation Contract

Status: public baseline.

This guide defines how Konoha may request work from an adapter without giving the adapter free execution authority.

An adapter invocation is a controlled request envelope. It is not permission by itself.

## Purpose

Adapter invocation exists to connect Konoha doctrine, Mission Charters, and adapter profiles through an explicit request and result format.

It should make the following clear before any adapter acts:

- what is being requested;
- which adapter is being invoked;
- what permission level applies;
- what files, folders, commands, tools, or context are in scope;
- whether execution is allowed or dry-run only;
- what evidence must be returned;
- what stop conditions apply.

## Core rule

Technical capability is not authorization.

An adapter may be technically able to read files, propose patches, run commands, call tools, or access local resources. It may only do so when the Mission Charter and adapter permission matrix explicitly allow it.

## Invocation layers

A valid invocation must reference:

```text
Mission Charter
Adapter manifest
Adapter capabilities
Adapter permission matrix
Invocation request
Approval state
Result contract
```

If any required layer is missing, the adapter must stop and ask for clarification.

## Invocation modes

### Read-only

The adapter may inspect explicitly allowed files or folders and return observations.

It must not modify files, generate patches, run commands, access private context, or create memory.

### Propose-only

The adapter may propose changes in text form or as a patch preview.

It must not apply patches, move files, delete files, execute commands, or publish results.

### Patch-authorized

The adapter may create or apply patches only within the files and folders named in the invocation request.

It must return a diff summary and validation evidence.

### Command-authorized

The adapter may run explicitly listed commands.

It must not generalize command permission to nearby commands.

For example, approval to run `pytest` is not approval to run `git push`, `rm`, `curl`, package managers, deploy commands, or secret-reading commands.

### Local-private

The adapter may access a local private Village only if the Mission Charter explicitly names the Village and the allowed paths.

Local-private access does not imply public publication rights.

### Release-authorized

The adapter may assist with release tasks only when the Mission Charter explicitly permits the specific release action.

Tag creation, release publication, changelog mutation, and push operations require explicit approval.

## Request envelope

Every invocation should declare:

```text
request_id
mission_id
adapter_id
adapter_profile
permission_level
mode
allowed_inputs
allowed_outputs
allowed_paths
allowed_commands
private_context_scope
approval_required
stop_conditions
evidence_required
expected_result
```

The request must be small enough for a reviewer to understand.

## Scope rules

Allowed scope must be explicit.

Examples of valid scopes:

```text
allowed_paths:
- docs/guides/adapter_contracts.md
- adapters/templates/
```

Examples of invalid scopes:

```text
allowed_paths:
- everything
- repo
- all docs
- whatever is needed
```

Broad scopes require a higher-level Mission Charter and stronger review.

## Private context rules

Private context is denied by default.

An invocation must not access:

- local Villages;
- private libraries;
- converted books;
- local memory;
- secrets;
- credentials;
- personal data;
- client data;
- internal project files;

unless the Mission Charter explicitly allows the exact path and purpose.

## Command rules

Commands are denied by default.

Allowed commands must be listed exactly.

Each command must have:

```text
purpose
working directory
expected output
risk level
approval state
```

The adapter must stop if a command needs network access, package installation, credential access, deletion, deployment, release publication, or Git mutation that was not explicitly approved.

## Dry-run rule

When possible, the first invocation should be dry-run.

A dry-run may produce:

- proposed plan;
- proposed diff;
- command list;
- risk assessment;
- expected evidence;
- stop condition review.

A dry-run must not execute mutating actions.

## Output contract

Every adapter result should include:

```text
request_id
adapter_id
mode_used
actions_taken
files_read
files_modified
commands_run
evidence
risks_found
stop_conditions_triggered
next_approval_needed
result_status
```

If the adapter stopped, it must explain why and what approval or clarification is needed.

## Evidence requirements

Evidence should be concrete.

Examples:

```text
git status output
diff summary
test command output
file paths changed
check-ignore output
line references
validation checklist
```

The adapter must not claim success without evidence.

## Stop conditions

The adapter must stop if:

- the invocation scope is ambiguous;
- requested action exceeds permission level;
- private context may be exposed;
- a command was not explicitly approved;
- Git mutation is requested without approval;
- release action is requested without approval;
- the adapter would need credentials or secrets;
- outputs may include copyrighted or private source content;
- the result cannot be validated.

## Relationship to Mission Charter

The Mission Charter is the authority for the mission.

The invocation request is a bounded instruction inside the Mission Charter.

If they conflict, the stricter rule wins.

## Relationship to adapters

Adapter profiles describe likely capabilities and risks.

Adapter permission matrices define default allowed and blocked behavior.

Invocation requests grant task-specific scope.

No adapter can expand its own authority.

## Review requirement

Invocation contracts should be reviewed before executable adapter implementations are introduced.

Review should verify:

- adapter identity;
- permission level;
- paths;
- commands;
- private context boundary;
- output contract;
- evidence requirements;
- stop conditions.

## Non-goals

This guide does not implement:

- adapter runtime;
- command runner;
- shell integration;
- API integration;
- CI automation;
- model routing;
- credential handling;
- release automation.

It only defines the public contract for future invocation.
