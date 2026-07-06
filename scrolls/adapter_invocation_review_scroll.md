# Adapter Invocation Review Scroll

Status: public Scroll.

This Scroll reviews whether an adapter invocation request is safe, bounded, and ready to execute or propose work.

## Purpose

Use this Scroll before asking any adapter to act under a declared invocation request.

The review verifies that capability, permission, scope, evidence, and stop conditions are explicit.

## Required inputs

- Mission Charter.
- Adapter manifest.
- Adapter capabilities.
- Adapter permission matrix.
- Adapter invocation request.
- Relevant approval records.
- Expected output contract.

## Roles

### Hokage

Confirms that the invocation aligns with the Mission Charter.

The Hokage does not execute adapter work.

### Local Kage

Confirms local boundary rules, especially for Allied Villages and private context.

### Jounin

Reviews permission, scope, risks, evidence, and stop conditions.

### Kagebunshin or adapter executor

Acts only after the invocation request is approved and only within declared scope.

## Review checklist

### 1. Identity

- [ ] Adapter identity is explicit.
- [ ] Adapter profile exists.
- [ ] Adapter permission matrix exists.
- [ ] Request ID is present.
- [ ] Mission ID or Mission Charter reference is present.

### 2. Mode

- [ ] Invocation mode is selected.
- [ ] Requested action fits the selected mode.
- [ ] Technical capability is not treated as authorization.

### 3. Scope

- [ ] Allowed paths are explicit.
- [ ] Disallowed inputs are explicit.
- [ ] Allowed outputs are explicit.
- [ ] Scope is narrow enough to review.
- [ ] Broad phrases such as "everything" or "whatever is needed" are not used.

### 4. Commands

- [ ] Commands are denied by default.
- [ ] Any allowed command is listed exactly.
- [ ] Working directory is defined.
- [ ] Expected output is defined.
- [ ] Mutating commands have explicit approval.

### 5. Git and release

- [ ] Git permissions are explicit.
- [ ] `git push` is denied unless specifically approved.
- [ ] Tag creation is denied unless specifically approved.
- [ ] Release publication is denied unless specifically approved.

### 6. Private context

- [ ] Private context is denied by default.
- [ ] Any local Village access is explicitly named.
- [ ] Private files are not assumed available.
- [ ] No secrets or credentials are requested.
- [ ] No copyrighted source content will be copied into public outputs.

### 7. Evidence

- [ ] Evidence requirements are explicit.
- [ ] Validation steps are reproducible.
- [ ] The adapter must report files read, files modified, and commands run.
- [ ] The result format is defined.

### 8. Stop conditions

- [ ] Stop conditions are listed.
- [ ] The adapter must stop on ambiguous scope.
- [ ] The adapter must stop when needing unapproved commands.
- [ ] The adapter must stop when private context or credentials may be exposed.

## Verdicts

### Approved

The invocation may proceed exactly as written.

### Approved with restrictions

The invocation may proceed only with additional restrictions named by the reviewer.

### Needs revision

The invocation request must be rewritten before adapter work begins.

### Blocked

The invocation is unsafe, unauthorized, or incompatible with Konoha doctrine.

## Stop immediately if

- adapter identity is unclear;
- invocation mode is missing;
- allowed paths are ambiguous;
- private context boundary is unclear;
- command execution is implied but not listed;
- Git mutation is implied but not approved;
- release action is implied but not approved;
- expected output could leak private or copyrighted content.

## Required report

The review report must include:

```text
reviewed_request:
adapter:
mode:
verdict:
restrictions:
risks:
required_changes:
approval_needed:
```

## Completion rule

This Scroll is complete only when the user can explain:

- what the adapter is being asked to do;
- what it is not allowed to do;
- what evidence it must return;
- when it must stop.
