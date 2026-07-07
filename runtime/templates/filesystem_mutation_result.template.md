# Filesystem Mutation Result

Status: template.

Use this template after an approved filesystem mutation.

## Result metadata

- Request ID:
- Mission ID:
- Executor:
- Date:
- Adapter/runtime component:
- Execution mode:

## Authorization check

- Mission Charter referenced:
- Filesystem mutation request referenced:
- Execution gate referenced:
- Approved scope respected?
  - [ ] yes
  - [ ] no

If no, describe variance and stop further work.

## Mutations performed

### Files created

```text
<file-list>
```

### Files modified

```text
<file-list>
```

### Files moved or renamed

```text
<old-path> -> <new-path>
```

### Files deleted

```text
<file-list>
```

### Directories created or deleted

```text
<directory-list>
```

## Evidence

### Before evidence

```text
<reference or paste safe evidence>
```

### After evidence

```text
<reference or paste safe evidence>
```

### Diff or summary

```text
<safe diff summary or reference>
```

## Validation

Commands or checks performed:

```text
<validation evidence>
```

Validation result:

- [ ] pass
- [ ] pass with notes
- [ ] needs changes
- [ ] blocked

## Git status

If applicable:

```text
<git status output>
```

## Private-context check

- Private content exposed?
  - [ ] no
  - [ ] yes
- Local private paths modified?
  - [ ] no
  - [ ] yes
- Public/private boundary preserved?
  - [ ] yes
  - [ ] no

Notes:

```text
<notes>
```

## Rollback status

- Rollback needed?
  - [ ] no
  - [ ] yes
- Rollback available?
  - [ ] yes
  - [ ] no
- Rollback performed?
  - [ ] not needed
  - [ ] yes
  - [ ] no

Notes:

```text
<rollback notes>
```

## Final result

- [ ] completed
- [ ] completed with notes
- [ ] partially completed
- [ ] blocked
- [ ] reverted

## Reviewer notes

```text
<reviewer notes>
```
