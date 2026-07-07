# Runtime Validation Report

Status: draft  
Mission ID: `<mission_id>`  
Runtime package: `<package_reference>`  
Validation date: `<YYYY-MM-DD>`  
Reviewer: `<reviewer_name_or_role>`

## 1. Executive summary

Validation outcome: `<valid_for_review / conditional_revision_required / blocked>`

Summary:

```text
<one_to_three_sentences_describing_the_validation_result>
```

## 2. Runtime package reviewed

| Component | Status | Notes |
|---|---|---|
| Mission Intake | `<present/missing/na>` | `<notes>` |
| Dry-Run Execution Plan | `<present/missing/na>` | `<notes>` |
| Adapter Invocation Stub | `<present/missing/na>` | `<notes>` |
| Evidence Collection Stub | `<present/missing/na>` | `<notes>` |
| Runtime State | `<present/missing/na>` | `<notes>` |
| Model Routing Decision | `<present/missing/na>` | `<notes>` |
| Context Budget | `<present/missing/na>` | `<notes>` |
| Token Budget Enforcement | `<present/missing/na>` | `<notes>` |

## 3. Domain results

| Domain | Result | Notes |
|---|---|---|
| Mission alignment | `<pass/fail/conditional/na>` | `<notes>` |
| Authority boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Dry-run boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Public/private boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Context boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Model routing boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Token/resource boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Adapter boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Evidence boundary | `<pass/fail/conditional/na>` | `<notes>` |
| Runtime state boundary | `<pass/fail/conditional/na>` | `<notes>` |

## 4. Blockers

| Blocker ID | Severity | Domain | Description | Required resolution |
|---|---|---|---|---|
| `<B-001>` | `<critical/high/medium/low>` | `<domain>` | `<description>` | `<resolution>` |

## 5. Conditional findings

| Finding ID | Domain | Description | Recommended revision |
|---|---|---|---|
| `<F-001>` | `<domain>` | `<description>` | `<revision>` |

## 6. Evidence reviewed

| Evidence ID | Source | Supports | Notes |
|---|---|---|---|
| `<E-001>` | `<source>` | `<claim_or_check>` | `<notes>` |

## 7. Missing evidence

| Missing evidence | Impact | Required? |
|---|---|---|
| `<missing_evidence>` | `<impact>` | `<yes/no>` |

## 8. Safety conclusion

Select all that apply:

- `[ ]` No private content exposure found.
- `[ ]` No credential or secret exposure found.
- `[ ]` No execution request found.
- `[ ]` No file mutation request found.
- `[ ]` No Git operation request found.
- `[ ]` No automatic private context access found.
- `[ ]` No inferred authorization found.
- `[ ]` One or more safety blockers remain.

Notes:

```text
<safety_notes>
```

## 9. Cost and sufficiency conclusion

Select all that apply:

- `[ ]` Model tier appears sufficient for the dry-run task.
- `[ ]` Model tier should be escalated.
- `[ ]` Model tier could be demoted in future similar missions.
- `[ ]` Context budget appears reasonable.
- `[ ]` Context budget requires revision.
- `[ ]` Token hard stop was reached or likely to be reached.
- `[ ]` Capsule or prompt improvement is recommended.

Notes:

```text
<cost_and_sufficiency_notes>
```

## 10. Reviewer recommendation

Recommendation:

- `<accept_for_human_review>`
- `<revise_and_resubmit>`
- `<block>`

Rationale:

```text
<rationale>
```

## 11. Next action

Next action owner: `<owner>`  
Next action due: `<date_or_na>`

```text
<next_action>
```

## 12. Non-authorization statement

This report validates a dry-run runtime package only.

It does not authorize shell execution, file mutation, Git operations, adapter invocation, private context access, release actions, doctrine changes, or autonomous runtime behavior.
