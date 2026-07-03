# Agentic coding loop

This guide explains how Konoha turns coding experience into safer future coding behavior.

## Core idea

Kagebunshin writes code.

Jounin reviews code.

Shikamaru captures lessons.

The user approves doctrine.

## Why this exists

A coding agent should improve over time, but it must not silently rewrite its own rules.

The loop separates:

```text
private sources
mission experience
review findings
learning proposals
approved doctrine
agent instructions
```

## Roles

### Kagebunshin

The Kagebunshin executes approved code changes.

It follows the Mission Charter, project conventions, Scrolls, and local Village rules.

### Code Jounin

The Code Jounin reviews code against approved rules and rubrics.

It does not need to know every book or source. It needs an approved rubric.

### Shikamaru

Shikamaru records patterns, drafts learning proposals, and updates doctrine only when approved.

### Clerk

A Clerk may summarize, tag, cluster, or compare local notes.

A Clerk may not approve doctrine, access sensitive content without permission, or decide that a rule is now mandatory.

## Private literature flow

Private literature stays local.

A local source can produce:

```text
source card
notes
extracted principles
review rubric items
learning proposals
local doctrine drafts
```

Only distilled, license-safe, user-approved learning may become public doctrine.

## Coding loop

1. User requests code work.
2. Hokage creates or requests a Mission Charter.
3. Kagebunshin makes the approved change.
4. Code Jounin reviews against approved rubrics.
5. Gaps are reported with evidence.
6. Kagebunshin fixes approved issues.
7. Shikamaru records recurring lessons.
8. A learning proposal is created when useful.
9. User approves or rejects promotion.
10. Future missions start from the improved rules.

## What must not happen

Do not let an agent:

- copy private literature into public doctrine;
- update its own rules silently;
- claim a book requires a change without showing a distilled principle;
- use private notes as permission;
- keep expanding scope during review;
- treat review feedback as automatic doctrine.

## Example

A Python review finds repeated scripts with hidden global configuration.

The reviewer marks it as a finding.

Shikamaru creates a learning proposal:

```text
Problem:
Several scripts hide runtime paths in module-level globals.

Proposed rule:
Operational scripts should accept input and output paths through CLI arguments or config objects unless the local project explicitly defines a different pattern.

Evidence:
Mission A, Mission B, Mission C.

Scope:
Python clan or local Village rule.

Approval:
Pending user approval.
```

If approved, the rule enters the appropriate doctrine or rubric.

## Completion

The loop works when the next Kagebunshin starts with better instructions without losing safety, traceability, or user control.
