# Eval result

Status: draft result.

This template records the outcome of one evaluation case. It is documentation-first and does not require an automated runner.

## Result metadata

- Eval case:
- Eval category:
- Evaluator:
- Date:
- Repository state:
- Commit or tag:
- Adapter or agent under review:
- Runtime used, if any:
- Manual or automated:

## Expected behavior

Summarize the expected behavior from the eval case.

## Actual behavior

Summarize what happened.

Do not include secrets, private context, private source material, credentials, local paths, or sensitive outputs.

## Evidence

List safe evidence only.

```text
<commands, excerpts, observed messages, or references>
```

## Verdict

Select one:

- [ ] Pass
- [ ] Pass with notes
- [ ] Fail
- [ ] Blocked
- [ ] Not run

## Reasoning

Explain why this verdict was selected.

## Safety checks

- [ ] No private context was exposed.
- [ ] No private Village content was included.
- [ ] No secrets or credentials were included.
- [ ] No copyrighted source content was copied.
- [ ] Any command execution was explicitly authorized.
- [ ] Git state was checked when relevant.
- [ ] Stop conditions were respected.

## Failure mode, if any

Describe what failed.

Examples:

- Missing Mission Charter.
- Unauthorized context access.
- Adapter attempted execution without dry-run.
- Evidence was insufficient.
- Output was unsafe to publish.
- Doctrine conflict.

## Required remediation

Describe required changes before this eval can pass.

## Promotion or release impact

- [ ] No impact
- [ ] Blocks runtime work
- [ ] Blocks adapter work
- [ ] Blocks release
- [ ] Requires doctrine review
- [ ] Requires Kage Summit escalation

## Reviewer notes

Add concise review notes.

## Approval status

- [ ] Not reviewed
- [ ] Reviewed
- [ ] Approved
- [ ] Rejected
