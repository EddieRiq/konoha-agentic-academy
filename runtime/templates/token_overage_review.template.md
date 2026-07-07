# Token Overage Review Template

Status: template.

Use this template when a mission exceeds its planned token budget or repeatedly requires more context/model capacity than expected.

## Mission reference

- Mission ID:
- Mission title:
- Date:
- Owner:
- Reviewer:

## Original budget

| Budget area | Soft budget | Hard budget |
|---|---:|---:|
| Context intake |  |  |
| Work/reasoning |  |  |
| Output |  |  |
| Review |  |  |
| Total |  |  |

## Observed usage

- Usage source:
  - [ ] Measured
  - [ ] Adapter-reported
  - [ ] User-provided
  - [ ] Estimated
  - [ ] Unavailable
- Actual or estimated intake:
- Actual or estimated total:
- Number of retries:
- Number of model escalations:
- Reviewer involvement:

## Overage classification

- [ ] Justified
- [ ] Questionable
- [ ] Unacceptable
- [ ] Unknown

## Overage reason

Select all that apply:

- [ ] Safety review required full-source reading.
- [ ] Release or audit task required broad evidence.
- [ ] Capsule was stale or missing.
- [ ] Mission scope expanded.
- [ ] Model tier was too low.
- [ ] Prompt/capsule was insufficient.
- [ ] Agent loaded unrelated context.
- [ ] Repeated failed attempts increased cost.
- [ ] User requested additional work.
- [ ] Other:

## Safety impact

- Did budget pressure weaken safety?
  - [ ] No
  - [ ] Yes
- Did budget pressure cause skipped review?
  - [ ] No
  - [ ] Yes
- Did the agent access unauthorized private context?
  - [ ] No
  - [ ] Yes
- Did the mission continue after a hard stop without approval?
  - [ ] No
  - [ ] Yes

## Capability review

- Selected model tier:
- Was selected tier sufficient?
  - [ ] Yes
  - [ ] No
  - [ ] Partially
- Should this task be routed differently next time?
  - [ ] Same tier
  - [ ] Lower tier with stronger capsule/prompt
  - [ ] Higher tier
  - [ ] Split between lower tier worker and reviewer

## Improvement action

- Context capsule needed:
- Prompt reinforcement needed:
- Model routing update needed:
- Eval case needed:
- Budget policy update needed:
- Reviewer rule update needed:

## Decision

- [ ] Accept overage as justified.
- [ ] Accept but update routing/budget policy.
- [ ] Mark as inefficient and require future changes.
- [ ] Block this workflow until corrected.

## Reviewer notes

- Reviewer:
- Decision date:
- Notes:
