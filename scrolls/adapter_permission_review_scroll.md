# Adapter permission review Scroll

Status: public Scroll.

Use this Scroll to review adapter permissions before implementation, before increasing an adapter's authority, or before allowing an adapter to execute a sensitive mission.

## Purpose

Adapter permission review prevents tools from becoming authority.

An adapter may expose capabilities, but Konoha decides whether those capabilities may be used.

## Inputs

Required inputs:

- adapter manifest;
- adapter capabilities declaration;
- adapter safety checklist;
- requested permission level;
- intended mission or use case;
- file access scope;
- command access scope;
- private context policy;
- logging policy;
- rollback plan.

Optional inputs:

- previous review notes;
- eval results;
- test outputs;
- threat model;
- release plan.

## Required reading

Before using this Scroll, review:

- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/approval/approval_policy.md`
- `protocols/safety/safety_policy.md`
- `docs/guides/public_private_boundary.md`
- `docs/guides/adapter_contracts.md`
- `docs/guides/adapter_permission_matrix.md`

## Review steps

### 1. Identify requested level

Record:

- requested maximum permission level;
- default permission level;
- minimum viable permission level;
- reason for each requested capability.

If the requested level is higher than needed, reduce it.

### 2. Check capability fit

For each capability, ask:

- Is it required for the mission?
- Is it explicitly approved?
- Can it be replaced with a lower-risk alternative?
- Does it touch private context?
- Does it require command execution?
- Does it require network access?
- Does it require credentials?

Missing justification means the capability is not approved.

### 3. Check file scope

Confirm:

- exact allowed paths;
- exact denied paths;
- whether ignored folders are involved;
- whether generated files are public or local;
- whether output could include private content.

The adapter may not infer file access from tool availability.

### 4. Check command scope

Classify every command as:

- read-only;
- validation;
- write/edit;
- dependency installation;
- Git operation;
- network operation;
- destructive operation;
- release operation.

Commands outside the approved list are denied.

### 5. Check private boundary

Private context requires explicit local-private authorization.

Review:

- ignored Allied Villages;
- local memory;
- private literature;
- local assets;
- outputs;
- credentials;
- environment files;
- user-specific paths.

No adapter may publish or commit private content.

### 6. Check logging

Logs should be useful but safe.

Verify:

- no secrets are printed;
- no credentials are captured;
- private paths are not exposed unnecessarily;
- large private content is not copied into logs;
- logs are stored in the approved location.

### 7. Decide permission level

Possible decisions:

- approve at requested level;
- approve at lower level;
- approve with constraints;
- block pending clarification;
- reject.

Document the decision and reason.

## Stop conditions

Stop the review if:

- the adapter asks to grant itself permission;
- the Mission Charter is missing;
- the adapter needs secrets or credentials;
- public/private boundary is unclear;
- command behavior is not understood;
- the user cannot explain what will happen;
- a release action is requested without release review;
- the adapter contradicts Konoha laws.

## Output format

```markdown
# Adapter permission review

## Adapter

- Name:
- Requested level:
- Approved level:

## Scope

Allowed paths:

Denied paths:

Allowed commands:

Denied commands:

## Private boundary

Private access approved: yes/no

Notes:

## Decision

Decision:

Reason:

Constraints:

## Required follow-up

- [ ] Update manifest
- [ ] Update capabilities
- [ ] Update safety checklist
- [ ] Add eval
- [ ] Escalate to Kage Summit
```

## Completion

The review is complete only when:

- the permission level is explicit;
- denied actions are explicit;
- stop conditions are explicit;
- the user understands the boundary;
- the decision is recorded.
