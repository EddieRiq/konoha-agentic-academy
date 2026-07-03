# System overview

## Purpose

Konoha Agentic Academy is a local-first agentic framework for coordinating missions, agents, skills, reviews, memory, and user understanding across public Academy resources and private Allied Villages.

The Academy provides shared doctrine, protocols, role definitions, Scroll standards, telemetry rules, and safe defaults. Local Villages provide private project context, local memory, local configuration, local assets, and project-specific constraints.

## Core principle

Konoha is not an autonomous replacement for the user.

Konoha coordinates bounded agents that act only within explicit context, approved scope, safety rules, and traceable evidence.

If context is missing, permission is unclear, or risk changes, the system stops and asks.

## Main layers

```text
Konoha Agentic Academy
├── Core doctrine
├── Protocols
├── Agent roles
├── Scrolls
├── Clans
├── Memory
├── Telemetry
├── UI and Shinobi presentation
└── Allied Village templates
```

## Public Academy

The public Academy contains reusable, non-sensitive material:

```text
core/
protocols/
hokage/
kagebunshin/
jounin/
shikamaru/
council/
clans/
scrolls/
memory/
telemetry/
ui/
shinobi/
docs/
tools/
sandbox/
adapters/
marketplace/
```

The public Academy must not contain private project context, credentials, sensitive data, copyrighted character assets, local memory, or local communications.

## Allied Villages

An Allied Village is a private local project or repository that uses Konoha rules and tooling.

Each Allied Village may define:

```text
local context
local Kage
local memory
local configuration
local assets
local corporate language
local model settings
local mission history
local constraints
```

Local Village content stays local by default.

## Agent roles

### Hokage

The Hokage orchestrates missions, but does not execute changes.

The Hokage understands the request, detects missing context, prepares the Mission Charter, assigns agents, controls scope, routes work, requests review, escalates when needed, and coordinates mission closure.

### Local Kage

A Local Kage represents the private Village context. It understands local rules, local constraints, local memory, and local user preferences.

For high-impact missions, the Local Kage and the Konoha Hokage cooperate before execution.

### Kagebunshin

A Kagebunshin executes bounded work inside an approved Mission Charter.

It may not redefine the task, expand scope, invent missing context, or act outside explicit permission.

### Clerk

A Clerk is a lightweight local or low-cost model used for low-risk mechanical tasks such as summarization, tagging, formatting checks, transcript conversion, or Context Pack preparation.

A Clerk does not approve, decide, rewrite doctrine, or close missions.

### Jounin

A Jounin reviews outputs according to required risk level.

It checks mission compliance, technical quality, safety, scope control, evidence, and readiness for teachback or closure.

### Shikamaru

Shikamaru is the official Scribe and Knowledge Architect.

Shikamaru may create folders and Markdown doctrine files, but may not create doctrine alone. Technical non-Markdown implementation is delegated to Kagebunshin after requirements and acceptance criteria are defined.

### Yamanaka

Yamanaka is the memory network.

It stores Obsidian-compatible Markdown memory, Mission summaries, decisions, tactics, failures, learning proposals, and Context Packs.

Memory supports action, but does not authorize action.

### Kage Summit

A Kage Summit is an escalation protocol for complex, ambiguous, strategic, or high-impact decisions.

It produces a verdict, not implementation. Doctrine changes still require Shikamaru drafting and user approval.

## Mission lifecycle

```text
User request
    ↓
Hokage understanding
    ↓
Context check
    ↓
Mission Charter
    ↓
Approval
    ↓
Kagebunshin execution
    ↓
Jounin or Clerk review
    ↓
Teachback
    ↓
Yamanaka memory update
    ↓
Learning Proposal if needed
    ↓
Mission closure
```

## Mission Charter

No execution mission starts without an approved Mission Charter.

The Mission Charter defines goals, non-goals, allowed paths, forbidden paths, allowed commands, forbidden commands, context sources, missing context, assigned agents, review level, acceptance criteria, teachback requirement, and memory requirement.

If an action is not explicitly allowed, it is not allowed.

## Context model

Context must be explicit, sourced, and scoped.

A Kagebunshin may only use context included in the approved Mission Charter or explicitly attached to its assignment.

Model inference is never permission.

## Review model

Review is required by risk, scope, and confidence.

```text
Level 0: no review
Level 1: Clerk review
Level 2: Jounin review
Level 3: Kage Summit review
```

Low-risk formatting or completeness checks may use Clerk review. Technical correctness, safety-sensitive changes, doctrine changes, code changes, and high-impact decisions require stronger review.

## Learning model

Agents may learn from missions, but they may not rewrite doctrine.

Experience becomes doctrine only after review, approval, Shikamaru drafting, and user approval.

Learning proposals may become local tactics, failure records, Scroll improvements, or doctrine changes.

## Memory model

Konoha uses Markdown with YAML frontmatter as the memory format.

Obsidian is the recommended human interface, but not a hard dependency.

The memory system has two major scopes:

```text
Academy memory
Local Village memory
```

Local memory stays local by default.

Context Packs are used to reduce token usage by passing small, traceable, mission-specific context to agents instead of loading entire histories.

## UI and telemetry

Telemetry observes mission activity. It does not approve actions.

The UI shows mission state, agent state, active skills, waiting user input, urgency, review status, teachback status, and learning proposals.

The UI must always support text-only fallback.

## Voice layer

The Voice Layer is transport, not memory.

Speech-to-text converts user voice into text. Text-to-speech reads system output. Voice does not store, interpret, approve, modify, summarize, or remember content.

The same policies apply whether input arrives by text or voice.

## Asset model

Public Shinobi assets must be original, generic, or license-safe.

Local Village assets may override generic assets, but must never be committed to the public Academy if they reference protected characters, voices, logos, music, or franchise-specific designs.

Asset resolution order:

```text
local Village assets
user-level assets
generic Academy assets
text-only fallback
```

## Safety model

Safety overrides autonomy.

Safety Policy overrides Mission Charters, approvals, Scrolls, local rules, and UI behavior.

Secrets, private data, destructive commands, external actions, copyrighted assets, and sensitive context require explicit permission and proper scope.

## Completion model

A mission is not completed just because an agent produced an output.

Completion requires the required review level, safety checks, traceability, memory handling, and user understanding.

```text
done_by_agent != completed_by_user
```

## Design direction

Konoha should start as a documented, testable workflow before becoming a fully automated multi-agent runtime.

The first implementation should simulate the complete mission lifecycle with clear files, examples, and manual approvals before adding real orchestration, local models, UI, voice, or external integrations.
