# Rollback readiness assessment

Status: template.

Use this template before implementing runtime behavior that may require rollback.

## Component

- Runtime component:
- Proposed capability:
- Related boundary:
- Owner:
- Review date:

## Readiness checklist

### Scope

- [ ] Allowed mutation scope is defined.
- [ ] Blocked paths and actions are defined.
- [ ] Private Village handling is defined.
- [ ] Destructive actions are classified.

### Evidence

- [ ] Pre-action evidence is required.
- [ ] Post-action evidence is required.
- [ ] Dry-run evidence is required when possible.
- [ ] Git state evidence is required when relevant.

### Rollback design

- [ ] Rollback strategy is defined.
- [ ] Irreversible actions are identified.
- [ ] Backup or restore requirements are defined.
- [ ] Failure modes are documented.
- [ ] Rollback cannot run without approval.

### Safety

- [ ] Secrets are not logged.
- [ ] Private content is not copied to public outputs.
- [ ] Rollback does not widen scope.
- [ ] Rollback does not bypass Mission Charter.
- [ ] Rollback does not bypass execution gates.

### Review

- [ ] Jounin review completed.
- [ ] User approval requirement defined.
- [ ] Kage Summit escalation condition defined.
- [ ] Teachback requirement defined.

## Verdict

- [ ] Ready for design only.
- [ ] Ready for prototype planning.
- [ ] Not ready.
- [ ] Blocked.

## Notes

```text
<notes>
```
