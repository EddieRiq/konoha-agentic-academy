# Context capsule refresh report

Status: draft.

Use this template when refreshing, invalidating, or approving a context capsule.

## Capsule

Capsule name:

Capsule id:

Previous status:

New status:

Refresh reason:

```text
scheduled | source changed | doctrine changed | incident | reviewer request | user request | other
```

## Source hash check

| Source path | Previous SHA-256 | Current SHA-256 | Changed? |
|---|---|---|---|
|  |  |  |  |

## Change summary

Summarize what changed in the sources.

-

## Capsule update summary

Summarize what changed in the capsule.

-

## Risk review

Does the previous capsule contain stale or misleading guidance?

```text
yes | no | unknown
```

Could stale guidance have affected prior missions?

```text
yes | no | unknown
```

Notes:

## Full-source requirements

Does this refresh add new full-source required triggers?

```text
yes | no
```

If yes, list them:

-

## Token budget impact

Expected intake impact:

```text
lower | same | higher | unknown
```

Reason:

## Review decision

Decision:

```text
approved-for-routine-use | needs changes | stale | deprecated | blocked
```

Reviewer:

Date:

Evidence:

## Follow-up

- [ ] Token usage guidance updated if needed.
- [ ] Related capsules checked.
- [ ] Related docs or templates updated if needed.
- [ ] Mission reports reviewed if stale guidance may have mattered.
