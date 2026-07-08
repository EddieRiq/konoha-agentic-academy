# Real Model Invocation Gate Review Scroll

Use this Scroll before approving any real model invocation.

## Review checklist

- Mission workspace exists.
- Sandbox run exists.
- Model Provider Contract is public and valid.
- Request plan has a clear purpose.
- Provider is allowlisted.
- Model is appropriate for the task.
- Token budget is acceptable.
- Estimated cost is acceptable.
- Request does not contain private context.
- Prompt does not contain credentials or secret-like strings.
- Network access is explicitly required and explicitly approved.
- Human approval token is present only at invocation time.
- Model output is treated as proposal/evidence only.

## Blockers

Block invocation if any of these are true:

- private context is requested;
- prompt contains secrets;
- provider is not allowlisted;
- cost exceeds budget;
- token budget exceeds contract;
- approval token is missing or wrong;
- network approval is missing for real providers;
- request implies execution authority;
- request asks model to approve, apply, stage, commit, push, or close mission.

## Closure

A model response does not close a mission.

Mission closure still requires evidence review, human approval, and teachback.
