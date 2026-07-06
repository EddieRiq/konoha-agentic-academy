# Adapter Execution Gate review

Status: template.

Use this template before allowing an adapter invocation to move from read-only, dry-run, or propose-only behavior into real execution.

## Adapter

- Adapter name:
- Adapter profile:
- Adapter manifest:
- Adapter permission matrix:

## Mission

- Mission Charter:
- User-approved scope:
- Requested execution level:
- Requested action:

## Execution level

Select one:

- [ ] EG-0 Read-only
- [ ] EG-1 Propose-only
- [ ] EG-2 Patch-authorized
- [ ] EG-3 Dry-run command-authorized
- [ ] EG-4 Command-authorized
- [ ] EG-5 Git-authorized
- [ ] EG-6 Release-authorized
- [ ] EG-7 Private-context-authorized

## Approved paths

```text
<paths>
```

## Blocked paths

```text
<paths>
```

## Approved commands

```text
<commands>
```

## Blocked commands

```text
<commands>
```

## Private context

- Private context involved: yes/no
- Private path or source:
- Reason access is required:
- Publication allowed: no unless explicitly approved

## Dry-run or proposal evidence

```text
<evidence>
```

## Risk review

- [ ] Scope is explicit.
- [ ] Permission matrix allows this level.
- [ ] Mission Charter allows this action.
- [ ] Side effects are understood.
- [ ] Rollback plan exists when needed.
- [ ] Git actions are separately authorized.
- [ ] Release actions are separately authorized.
- [ ] Private context is excluded or explicitly authorized.
- [ ] No secrets or private source content will be exposed.

## Rollback plan

```text
<rollback plan>
```

## Stop conditions

Stop if:

- the adapter needs broader access than approved;
- the command or patch affects blocked paths;
- unexpected files change;
- private context appears in output;
- secrets or credentials appear;
- Git state changes unexpectedly;
- validation fails.

## Decision

- [ ] Deny
- [ ] Request clarification
- [ ] Approve with restrictions
- [ ] Approve exactly as requested

## Approval statement

```text
<explicit approval statement>
```

## Reviewer

- Reviewer:
- Date:
