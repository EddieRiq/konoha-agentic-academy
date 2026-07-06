# Adapter pre-execution evidence

Status: draft.

Use this template before an adapter moves beyond read-only, dry-run, or propose-only mode.

## Invocation summary

Adapter:

Requested mode:

Mission Charter:

Allowed scope:

Excluded scope:

## Baseline checks

Git status, if applicable:

```text

```

Permission matrix reviewed:

```text

```

Execution gate reviewed:

```text

```

Dry-run result, if required:

```text

```

## Approval

Explicit user approval captured:

- [ ] Yes
- [ ] No

Approval text or reference:

```text

```

## Stop condition check

- [ ] No private context will be exposed.
- [ ] No secrets will be printed.
- [ ] No unrelated files will be touched.
- [ ] No destructive command is requested.
- [ ] Rollback path is known if changes are made.
- [ ] The request stays within the Mission Charter.

## Pre-execution verdict

- [ ] Proceed
- [ ] Proceed with constraints
- [ ] Dry-run only
- [ ] Block

Notes:

```text

```
