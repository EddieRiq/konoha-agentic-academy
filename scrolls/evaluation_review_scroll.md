# Evaluation Review Scroll

Status: public Scroll.

This Scroll reviews Konoha evaluation cases before they are accepted into public evals or used as evidence for runtime readiness.

It does not execute tests. It reviews eval quality, safety, clarity, and boundary compliance.

## Purpose

Use this Scroll to check whether an eval case is:

- public-safe;
- specific enough to evaluate;
- aligned with Konoha doctrine;
- clear about pass and fail criteria;
- safe for future automation;
- not leaking private or copyrighted content.

## Inputs

Required:

- Eval case path.
- Eval type.
- Related policy, Scroll, guide, or adapter document.
- Intended use.

Optional:

- Prior related evals.
- Failure examples.
- Reviewer notes.

## Allowed actions

The reviewer may:

- read the eval case;
- compare it to public doctrine;
- identify unclear pass/fail criteria;
- identify private or sensitive content risk;
- recommend revisions;
- approve, reject, or block the eval case.

## Forbidden actions

The reviewer must not:

- execute code;
- invoke adapters;
- access private Village content without explicit Mission Charter authorization;
- publish private eval cases;
- approve runtime work;
- treat eval acceptance as execution permission.

## Review checklist

### Public safety

- [ ] The eval contains no secrets, credentials, personal data, or client data.
- [ ] The eval contains no private Village content.
- [ ] The eval contains no copyrighted source excerpts.
- [ ] The eval uses synthetic or sanitized inputs.

### Scope clarity

- [ ] Eval type is clear.
- [ ] Related policy or Scroll is linked.
- [ ] Scenario is specific.
- [ ] Input prompt or request is provided.
- [ ] Expected behavior is explicit.
- [ ] Forbidden behavior is explicit.

### Pass/fail quality

- [ ] Pass criteria are observable.
- [ ] Fail criteria are observable.
- [ ] The eval can be judged without guessing intent.
- [ ] Edge cases or ambiguity are noted.

### Doctrine alignment

- [ ] Mission Charter rules are respected.
- [ ] Approval boundaries are respected.
- [ ] Safety and privacy boundaries are respected.
- [ ] Adapter capability is not treated as authorization.
- [ ] Dry-run, evidence, and execution gates are respected when relevant.

### Automation readiness

- [ ] The eval could later be converted to a structured runner input.
- [ ] Expected output is sufficiently constrained.
- [ ] No private dependencies are required.
- [ ] Failure modes are clear.

## Verdicts

### Accepted

The eval is public-safe and ready to use as a baseline case.

### Accepted with notes

The eval is safe and useful, but has minor clarity issues.

### Needs revision

The eval is promising but requires edits before acceptance.

### Rejected

The eval is not useful, too vague, duplicated, or misaligned.

### Blocked

The eval contains private, unsafe, copyrighted, or authorization-sensitive content that must be removed before review can continue.

## Output format

```markdown
# Evaluation Review Result

Eval case: `<path>`
Reviewer: `<name or role>`
Date: `<YYYY-MM-DD>`

## Verdict

`<Accepted | Accepted with notes | Needs revision | Rejected | Blocked>`

## Summary

<short summary>

## Findings

- <finding>

## Required changes

- <change>

## Safety notes

- <note>

## Final decision

<decision>
```

## Stop conditions

Stop review if:

- the eval includes secrets or credentials;
- the eval includes private Village content;
- the eval includes copyrighted source excerpts;
- the eval requires unauthorized private context;
- the eval implies runtime approval;
- the eval attempts to weaken Konoha doctrine.

## Final rule

An eval can support future trust, but it cannot authorize execution by itself.
