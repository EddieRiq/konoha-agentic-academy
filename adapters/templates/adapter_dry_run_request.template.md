# Adapter dry-run request

Status: draft.

Use this template to request a dry-run before any adapter execution.

## Mission

- Mission ID:
- Mission Charter:
- Requester:
- Date:
- Adapter:
- Adapter profile:
- Permission level requested:

## Requested dry-run mode

Select one:

- [ ] Read-only dry-run
- [ ] Patch-planning dry-run
- [ ] Command-planning dry-run
- [ ] Release-planning dry-run
- [ ] Local-private dry-run
- [ ] Other:

## Objective

Describe what the adapter should simulate.

## Allowed scope

### Repository scope

Allowed paths:

```text
<paths>
```

Blocked paths:

```text
<paths>
```

### Local/private scope

Private context allowed?

- [ ] No
- [ ] Yes, explicitly allowed by Mission Charter

Allowed local/private paths:

```text
<paths>
```

Blocked local/private paths:

```text
<paths>
```

## Expected reads

Files or directories the adapter may inspect:

```text
<paths>
```

## Expected changes

Files or directories the adapter may propose changing:

```text
<paths>
```

## Proposed commands

Commands the adapter may propose but not execute:

```text
<commands>
```

## Constraints

- No execution during dry-run.
- No file modification during dry-run.
- No Git staging, commit, push, or tag.
- No dependency installation.
- No access to private context unless explicitly allowed.
- No publication of private or copyrighted material.

## Required evidence

- Mission Charter:
- Adapter manifest:
- Adapter permission matrix:
- Invocation request:
- Git status:
- Relevant guide or Scroll:
- Safety checklist:

## Stop conditions

Stop if:

- scope is ambiguous;
- requested action exceeds permission level;
- private context is not explicitly allowed;
- command side effects are unclear;
- files to be changed are not listed;
- rollback is unclear for risky action.

## Approval expectation

This dry-run may produce a recommendation, but it does not authorize execution.

Required approver for later execution:

```text
<approver>
```
