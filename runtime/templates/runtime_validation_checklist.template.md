# Runtime Validation Checklist

Status: draft  
Runtime mode: dry-run only  
Mission ID: `<mission_id>`  
Reviewer: `<reviewer_name_or_role>`  
Date: `<YYYY-MM-DD>`

## 1. Inputs reviewed

| Input | Present? | Location | Notes |
|---|---:|---|---|
| Mission Charter | `<yes/no>` | `<path_or_reference>` | `<notes>` |
| Mission Intake | `<yes/no>` | `<path_or_reference>` | `<notes>` |
| Dry-Run Execution Plan | `<yes/no>` | `<path_or_reference>` | `<notes>` |
| Adapter Invocation Stub | `<yes/no/not_applicable>` | `<path_or_reference>` | `<notes>` |
| Evidence Collection Stub | `<yes/no>` | `<path_or_reference>` | `<notes>` |
| Runtime State | `<yes/no>` | `<path_or_reference>` | `<notes>` |
| Model Routing Decision | `<yes/no/not_applicable>` | `<path_or_reference>` | `<notes>` |
| Context Budget | `<yes/no/not_applicable>` | `<path_or_reference>` | `<notes>` |
| Token Budget Enforcement | `<yes/no/not_applicable>` | `<path_or_reference>` | `<notes>` |

## 2. Mission alignment

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Mission objective is explicit | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Requested output is clear | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Plan stays within Mission Charter | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Assumptions are listed | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Ambiguity is marked as question or blocker | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 3. Authority boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Explicit approval requirements are preserved | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Capability is not treated as permission | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Model confidence is not treated as permission | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Memory/context does not authorize action | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Validation result does not authorize execution | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 4. Dry-run boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| No shell execution occurs | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| No file mutation occurs | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| No Git operation occurs | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| No dependency installation occurs | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| No network call occurs | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| No private context is accessed automatically | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Commands are proposed only, not executed | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 5. Public/private boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Public output is generic | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Private Village content is absent | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Private source text is not copied | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Ignored paths remain ignored | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Credentials/secrets are absent | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 6. Context boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Context sources are named | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Context intake is necessary | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Capsule status is valid or reviewed | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Stale capsules are blocked or refreshed | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Full-source fallback is defined when needed | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 7. Model routing boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Model tier is documented | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Tier is sufficient for task risk | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Escalation triggers are listed | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Demotion evidence exists when lower tier is used | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Model does not self-certify sufficiency | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 8. Token and resource boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Intake budget is stated | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Work budget is stated | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Output budget is stated | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Review budget is stated when required | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Soft limit is defined | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Hard stop is defined | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Overage path is defined | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 9. Adapter boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Adapter identity is explicit | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Requested capability is in contract | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Permission matrix is respected | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Invocation is stub-only | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Execution gate is not bypassed | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 10. Evidence boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Required evidence is listed | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Expected evidence is separated from collected evidence | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Missing evidence has impact statement | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Claims are tied to evidence | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 11. Runtime state boundary

| Check | Result | Evidence | Notes |
|---|---|---|---|
| Runtime state is descriptive only | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| State transitions are explicit | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Blockers are recorded | `<pass/fail/na>` | `<evidence>` | `<notes>` |
| Final state matches validation outcome | `<pass/fail/na>` | `<evidence>` | `<notes>` |

## 12. Blockers

| Blocker ID | Domain | Description | Required resolution |
|---|---|---|---|
| `<B-001>` | `<domain>` | `<description>` | `<resolution>` |

## 13. Open questions

| Question ID | Question | Owner | Required before next step? |
|---|---|---|---|
| `<Q-001>` | `<question>` | `<owner>` | `<yes/no>` |

## 14. Validation outcome

Choose one:

- `<valid_for_review>`
- `<conditional_revision_required>`
- `<blocked>`

Outcome selected: `<outcome>`

## 15. Reviewer decision

Reviewer decision:

- `<accept_dry_run_package_for_human_review>`
- `<request_revision>`
- `<block_until_resolved>`

Reason:

```text
<reason>
```

## 16. Explicit non-authorization statement

This checklist does not authorize execution, shell commands, file mutation, Git operations, adapter invocation, private context access, release actions, or doctrine changes.
