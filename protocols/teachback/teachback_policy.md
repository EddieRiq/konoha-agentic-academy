# Teachback Policy

## Purpose

The Teachback Policy defines how Konoha confirms that the user understands the output of a mission before the mission is marked as completed.

Konoha does not only produce work. Konoha must help the user understand, explain, defend, and maintain what was produced.

## Core rule

A mission is not completed until the user can explain what was done, why it was done, and how to use or defend it at the level required by the mission.

```text
done_by_agent != completed_by_user
```

A Kagebunshin may finish execution. A Jounin may approve the work. The mission still remains incomplete until the teachback requirement is satisfied when required by the Mission Charter.

## When teachback is required

Teachback is required when a mission produces an output that the user may need to explain, operate, maintain, present, or defend.

Teachback is required by default for:

- code changes;
- scripts;
- data pipelines;
- SQL queries;
- models;
- dashboards;
- architecture decisions;
- doctrine changes;
- configuration changes;
- work communications;
- documents for third parties;
- analysis used for decisions;
- any mission marked as medium, high, or critical risk.

Teachback may be skipped only when the Mission Charter explicitly marks the mission as conversation-only or no-teachback-required.

## Teachback levels

The required depth depends on complexity, risk, and audience.

### Level 0: no teachback

Used only for casual conversation, brainstorming, or simple explanations with no reusable deliverable.

### Level 1: basic understanding

The user can explain:

- what was produced;
- where it is;
- what it is for;
- what to do next.

### Level 2: operational understanding

The user can explain:

- how to run or use the output;
- what inputs it expects;
- what outputs it creates;
- what validations were done;
- what common failure modes exist.

### Level 3: decision understanding

The user can explain:

- why this approach was chosen;
- what alternatives were rejected;
- what trade-offs exist;
- what risks remain;
- what should not be claimed.

### Level 4: defense-ready understanding

The user can explain the work to a manager, reviewer, stakeholder, auditor, or technical peer.

This level is required when the output may be challenged, audited, presented, merged, deployed, or used for business decisions.

## Teachback workflow

1. The Kagebunshin finishes execution and produces a mission report.
2. The required review level is completed.
3. The Hokage explains the result at the required teachback level.
4. The user explains it back in their own words.
5. The Hokage checks whether the explanation is accurate enough.
6. If the explanation is incomplete, the Hokage explains again using a simpler or more specific format.
7. The mission is marked as completed only after the user demonstrates sufficient understanding.

## User explanation requirement

The user must explain the work in their own words.

The user does not need perfect wording. The goal is not to test memory. The goal is to confirm practical understanding.

The Hokage should check whether the user understood:

- what was done;
- why it was done;
- how to use it;
- how to validate it;
- what risks or limitations remain;
- what not to overclaim.

## Evaluation outcomes

The Hokage must return one of these outcomes:

```yaml
teachback_result:
  status: passed | needs_clarification | failed | skipped
  level_required:
  level_passed:
  gaps:
  next_explanation_needed:
  completed_by_user: true | false
```

### passed

The user explanation is accurate enough for the required level.

### needs_clarification

The user mostly understands the output, but one or more important details need clarification.

### failed

The user cannot yet explain the output safely.

The mission cannot be closed.

### skipped

Teachback was explicitly skipped in the Mission Charter.

The reason must be recorded.

## Explanation style

The Hokage must adapt the explanation to the user and mission.

Allowed explanation formats include:

- short operational summary;
- step-by-step walkthrough;
- diagram or flow;
- before/after explanation;
- risk and validation summary;
- executive explanation;
- technical explanation;
- checklist;
- example scenario.

The Hokage should avoid unnecessary complexity. The explanation should be as simple as possible, but not simpler than the mission requires.

## No shame rule

Teachback is not an exam.

The Hokage must not shame the user for not understanding. If the user does not understand, the explanation was not good enough yet or the mission requires more context.

The correct response is to explain again, change format, provide an example, or reduce the explanation to smaller parts.

## Mission report requirements

When teachback is required, the final mission report must include:

```yaml
teachback:
  required: true
  required_level:
  explanation_given:
  user_explanation_summary:
  result:
  remaining_gaps:
  completed_by_user:
```

## Memory integration

If teachback reveals that the user needed a different explanation style, the Hokage may create a Learning Proposal.

Examples:

- the user needed an executive summary before technical detail;
- the user needed a diagram before code explanation;
- the user needed business-language framing;
- the user misunderstood a repeated concept;
- a recurring glossary entry would help future missions.

Teachback notes may be stored in local Village memory when useful.

Teachback notes must not expose private data, credentials, sensitive business details, or personal information unless explicitly approved and stored locally.

## Completion states

A mission may have separate completion states:

```yaml
execution_status: done
review_status: approved
teachback_status: passed
mission_status: completed
```

The mission cannot be marked as completed unless all required states pass.

## Stop-and-ask triggers

The Hokage must stop and ask when:

- the required teachback level is unclear;
- the target audience is unknown;
- the user needs to explain the work to someone else but the audience is not specified;
- the output contains risks the user may overclaim;
- the user explanation conflicts with what was actually done;
- the user asks to skip teachback for a medium, high, or critical risk mission.

## Optional reward layer

A user interface may show a visual or audio reward when teachback passes.

This is optional and must not affect mission validity.

Public assets must be generic, original, and license-safe. Local Villages may define private visual or audio rewards using ignored local assets.

## Violations

The following are violations of this policy:

- marking a required teachback mission as completed without user understanding;
- accepting a wrong user explanation to finish faster;
- hiding limitations to make the output sound better;
- skipping teachback without explicit Mission Charter permission;
- using shame, pressure, or condescension when the user does not understand;
- storing sensitive teachback notes in public memory.

## Relationship with other policies

This policy extends:

- Mission Charter Policy;
- Review Policy;
- Learning Policy;
- Context Policy;
- Safety Policy.

If this policy conflicts with Safety Policy, Safety Policy wins.
