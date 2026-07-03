# Konoha narrative

## Purpose

This document explains the narrative language used by Konoha Agentic Academy.

The narrative exists to make agent behavior easier to understand, monitor, and discuss. It must never weaken the operational rules defined by Konoha Laws, Agent Conduct, Mission Charter, Safety Policy, Context Policy, Approval Policy, Review Policy, Learning Policy, or Teachback Policy.

Narrative terms are labels for roles, workflows, and responsibilities. They are not permissions.

## Core concept

Konoha Agentic Academy is the founding academy and central command for agentic work.

It coordinates missions through defined roles, bounded workers, review, memory, learning proposals, and human approval.

Local repositories or private projects may act as Allied Villages. They keep their own private context, local memory, assets, and rules. They may cooperate with Konoha Central when a mission requires stronger reasoning, review, or doctrine changes.

## Main terms

### Konoha

Konoha is the public academy and central framework.

It contains the shared doctrine, protocols, Scrolls, Clans, role policies, telemetry rules, UI rules, and safe public assets.

Konoha does not own private project context. Local context stays local by default.

### Allied Village

An Allied Village is a local repository, personal project, work project, or private workspace that uses Konoha.

Examples may include `kirigakure`, personal thesis projects, work repositories, or sensitive client projects.

An Allied Village may have:

- private context;
- local memory;
- local assets;
- local workers;
- local corporate language;
- local rules;
- a Local Kage.

Local Villages are ignored by Git unless intentionally created as safe public examples.

### Kirigakure

Kirigakure is the first planned local Allied Village.

It is used as the initial private playground for testing local memory, local assets, local configuration, and cooperation between a Local Kage and the Konoha Hokage.

Kirigakure itself should not be committed to the public repository unless it is converted into a sanitized example.

### Mission

A Mission is a task.

A Mission may be a conversation, plan, implementation, review, writing task, debugging task, research task, local memory update, or doctrine proposal.

Execution Missions require an approved Mission Charter.

### Mission Charter

A Mission Charter is the contract that defines what is allowed, forbidden, required, unknown, and expected before execution.

If something is not explicitly allowed by the Mission Charter, it is not allowed.

### Hokage

The Hokage is the central orchestrator.

The Hokage:

- receives the mission;
- clarifies the request;
- checks context confidence;
- creates or validates the Mission Charter;
- selects Clans, Scrolls, and agents;
- assigns Kagebunshin;
- requests Jounin review;
- escalates to Kage Summit when needed;
- coordinates Shikamaru and Yamanaka;
- controls mission closure.

The Hokage orchestrates, but does not execute.

### Local Kage

A Local Kage is the local coordinator inside an Allied Village.

The Local Kage understands local rules, local context, local assets, local memory, local hardware limits, and local communication style.

For high-risk work, the Local Kage and the Konoha Hokage may require dual approval.

### Kagebunshin

A Kagebunshin is a worker clone.

A Kagebunshin executes assigned work inside the approved Mission Charter.

It may not define the mission, expand scope, invent missing context, approve its own work, or declare completion.

### Clerk

A Clerk is a low-cost local or simple model used for low-risk support tasks.

A Clerk may help with:

- summaries;
- tags;
- formatting checks;
- simple extraction;
- transcription handoff;
- checklist validation;
- context pack preparation.

A Clerk may not approve, decide, change doctrine, close missions, handle sensitive actions, or replace Jounin review for medium-risk or high-risk work.

### Jounin

A Jounin is a reviewer.

A Jounin checks:

- mission compliance;
- technical quality;
- safety;
- scope control;
- evidence;
- completion readiness.

A Jounin may approve, request changes, block completion, or escalate.

A Jounin reviews, but does not rewrite the mission unless explicitly assigned.

### Shikamaru

Shikamaru is the Official Scribe and Knowledge Architect.

Shikamaru may:

- draft doctrine;
- edit normative Markdown files;
- create folders for new doctrine or Scrolls;
- create Markdown scaffolds;
- organize accepted knowledge;
- convert approved decisions into written rules.

Shikamaru may write doctrine, but may not create doctrine alone.

For non-Markdown technical files, Shikamaru prepares the structure and requirements, then assigns implementation to a Kagebunshin.

### Yamanaka

Yamanaka is the memory network.

It handles Obsidian-compatible Markdown memory, context packs, summaries, tags, decision records, mission logs, learning proposals, approved tactics, failure patterns, and archives.

Memory supports action, but does not authorize action.

A memory entry is not permission.

A summary is not truth.

### Kage Summit

A Kage Summit is an escalation process for complex, ambiguous, strategic, high-risk, or cross-village decisions.

A Kage Summit produces a verdict, not an implementation.

No Kage Summit decision becomes doctrine until Shikamaru drafts it and the user approves it.

### Clan

A Clan is a specialization area inside the Academy.

Examples:

- software engineering;
- data engineering;
- machine learning;
- writing;
- research;
- security;
- devops.

A Clan may contain specialized Scrolls, reviewers, examples, policies, and accepted tactics.

Clans specialize the Academy. They do not weaken it.

### Scroll

A Scroll is an activable skill, workflow, checklist, or capability.

A Scroll guides execution, but it may not override Konoha Laws, Safety Policy, Context Policy, Approval Policy, the Mission Charter, or local Village rules.

External Scrolls are untrusted by default.

### Doctrine

Doctrine is normative Markdown that governs behavior.

Doctrine includes laws, conduct, policies, protocols, role rules, and official operational rules.

Doctrine is not changed automatically. It requires review, approval, Shikamaru drafting, and human confirmation.

### Shinobi

Shinobi is the presentation layer.

It contains safe public UI themes, ASCII assets, sounds, palettes, status visuals, and visual conventions.

Shinobi does not execute, approve, store sensitive content, or modify mission state.

### Voice Layer

The Voice Layer is transport, not memory.

It may convert speech to text or text to speech.

It may not store, interpret, approve, summarize, modify, or remember content.

Voice input and output follow the same policies as text input and output.

## Narrative boundaries

The narrative must never override operational policy.

If there is a conflict between a narrative term and a policy, the policy wins.

The project may use anime-inspired language, but the public repository must not ship protected character assets, logos, voices, music, or franchise-specific designs.

Public assets must be original, generic, or license-safe.

Local Villages may use private assets under the user's responsibility, but those assets must not be committed to the public repository.

## Example flow

```text
User creates a Mission
        ↓
Hokage clarifies intent
        ↓
Mission Charter is created
        ↓
Kagebunshin executes within scope
        ↓
Jounin reviews by risk level
        ↓
Teachback confirms user understanding
        ↓
Yamanaka stores memory
        ↓
Learning Proposal is created if useful
        ↓
Shikamaru drafts doctrine only after approval
```

## Completion principle

A Mission is not complete just because an agent produced output.

A Mission is complete only when:

- the work matches the approved Mission Charter;
- required review has passed;
- safety checks are clean;
- relevant memory has been updated;
- the user understands what was delivered;
- completion is traceable.
