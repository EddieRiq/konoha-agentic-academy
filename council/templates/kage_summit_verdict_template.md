# Kage Summit verdict template

Use this template to record the decision of a Kage Summit.

A Kage Summit verdict is a decision record. It is not implementation, doctrine, or permission to bypass safety.

No verdict becomes doctrine until Shikamaru drafts the change and the user explicitly approves it.

## Metadata

```yaml
verdict_id: KS-VERDICT-YYYYMMDD-001
brief_id:
mission_id:
created_at:
created_by:
status: approved | rejected | approved_with_conditions | deferred | escalated
risk_level: low | medium | high | critical
decision_type: scope | safety | doctrine | architecture | memory | external_content | local_context | other
```

## Decision

Write the decision in plain language.

```text
The Kage Summit decided:
```

## Scope of decision

This verdict applies only to the scope written here.

```text
Applies to:
Does not apply to:
Expires when:
```

## Conditions

List required conditions before any agent may act on this verdict.

```text
[ ] Mission Charter updated
[ ] Human approval received
[ ] Local Kage approval received
[ ] Jounin review required
[ ] Safety review required
[ ] Context pack updated
[ ] Sandbox required
[ ] Tests or evals required
[ ] Memory note allowed
[ ] Learning proposal allowed
[ ] Doctrine draft required
[ ] Other
```

Details:

```text
Conditions:
```

## Approved actions

List the exact actions allowed.

If an action is not listed here and not present in the approved Mission Charter, it is not allowed.

```text
Allowed actions:
1.
2.
3.
```

## Forbidden actions

List actions that remain forbidden.

```text
Forbidden actions:
1.
2.
3.
```

## Required changes to Mission Charter

```text
Required Mission Charter changes:
```

## Required review

```text
Review level: none | Clerk | Jounin | Kage Summit
Reviewer:
Review scope:
```

## Required evidence

The executing agent must provide this evidence before closure.

```text
Evidence required:
1.
2.
3.
```

## Safety notes

```text
Sensitive data involved: yes | no
Secrets involved: yes | no
External systems involved: yes | no
State-changing commands involved: yes | no
Doctrine change involved: yes | no
Local Village context involved: yes | no
```

Controls:

```text
Safety controls:
```

## Memory and learning

```text
Memory update allowed: yes | no
Learning proposal allowed: yes | no
Doctrine draft required: yes | no
Public promotion allowed: yes | no
```

Notes:

```text
Memory and learning notes:
```

## Rationale

Explain why the council chose this decision.

```text
Rationale:
```

## Dissent or uncertainty

Record disagreement or uncertainty instead of hiding it.

```text
Dissent:
Uncertainty:
Follow-up needed:
```

## Teachback requirement

State what the user must understand before the mission can be closed.

```text
The user must be able to explain:
1.
2.
3.
```

## Final authority check

```text
[ ] This verdict does not override the Safety Policy
[ ] This verdict does not override explicit user denial
[ ] This verdict does not grant permissions outside its written scope
[ ] This verdict does not become doctrine by itself
[ ] This verdict requires Mission Charter alignment before execution
```

## Closing statement

```text
Verdict:
Next required action:
Who must act:
Who must review:
```
