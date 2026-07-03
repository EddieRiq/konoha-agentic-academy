# Kage Summit brief template

Use this template when a mission needs escalation to the Kage Summit.

A Kage Summit is required when a decision exceeds the authority, scope, confidence, safety level, or doctrine coverage of the active Mission Charter.

The brief must describe the decision needed. It must not implement the decision.

## Metadata

```yaml
brief_id: KS-BRIEF-YYYYMMDD-001
mission_id:
created_at:
created_by:
requested_by:
status: draft
related_village:
related_clan:
related_scroll:
risk_level: low | medium | high | critical
decision_type: scope | safety | doctrine | architecture | memory | external_content | local_context | other
```

## Mission reference

Link or describe the active Mission Charter.

```text
Mission Charter:
Mission owner:
Current mission mode:
Assigned agents:
```

## Reason for escalation

State why the current mission cannot continue without a Kage Summit.

Choose all that apply:

```text
[ ] Scope exceeds approved Mission Charter
[ ] Safety concern
[ ] Private or local context concern
[ ] Doctrine ambiguity
[ ] Doctrine change requested
[ ] External content or supply chain concern
[ ] Sensitive command or file operation
[ ] Conflicting policies
[ ] Low confidence with high impact
[ ] Architecture decision
[ ] Memory promotion decision
[ ] Other
```

## Decision needed

Write the smallest decision the council must make.

```text
The Kage Summit must decide whether:
```

## Background

Summarize only the context needed to decide.

Do not include secrets, private data, credentials, personal data, local paths, or raw sensitive content unless the Mission Charter explicitly allows it.

```text
Context:
```

## Evidence

List the evidence supporting the escalation.

Use paths, command outputs, diffs, logs, references, or prior decisions when available.

```text
Evidence:
1.
2.
3.
```

## Options considered

### Option A

```text
Description:
Benefits:
Risks:
Required approvals:
Review needed:
```

### Option B

```text
Description:
Benefits:
Risks:
Required approvals:
Review needed:
```

### Option C

```text
Description:
Benefits:
Risks:
Required approvals:
Review needed:
```

## Recommended option

The requesting agent may recommend an option, but the recommendation is not approval.

```text
Recommended option:
Reason:
Confidence:
Known uncertainty:
```

## Safety review

```text
Sensitive data involved: yes | no | unknown
Secrets involved: yes | no | unknown
External systems involved: yes | no | unknown
State-changing commands involved: yes | no | unknown
Doctrine change involved: yes | no | unknown
Local Village context involved: yes | no | unknown
```

If any value is `yes` or `unknown`, explain the control needed.

```text
Controls needed:
```

## Impact if approved

```text
Files or paths affected:
Agents affected:
Scrolls affected:
Clans affected:
Memory affected:
Local Villages affected:
Users affected:
```

## Impact if rejected

```text
What stops:
What can still continue:
Alternative safe path:
```

## Questions for the council

```text
1.
2.
3.
```

## Required verdict format

The Kage Summit must answer using the Kage Summit verdict template.

No implementation may start from this brief alone.
