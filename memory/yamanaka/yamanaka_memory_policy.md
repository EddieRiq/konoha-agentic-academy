# Yamanaka Memory Policy

## Purpose

The Yamanaka Memory Network defines how Konoha Agentic Academy stores, summarizes, retrieves, archives, and promotes knowledge across Academy-wide memory and Local Village memory.

Memory exists to help agents remember what happened, reduce context-window pressure, preserve traceability, and avoid forcing the user to manually remember past requests, decisions, explanations, and follow-ups.

Yamanaka Memory is not doctrine by default.

## Core rules

Memory supports action, but does not authorize action.

A memory entry is not permission.

A summary is not truth.

Local memory stays local by default.

Sensitive context must never be promoted to Academy memory unless it is sanitized, explicitly approved, and safe to share.

No agent may close a mission by relying on memory alone when the Mission Charter, user instruction, or observed evidence is missing.

## Memory scopes

### Academy memory

Academy memory belongs to the public or shared Konoha framework.

It may contain:

- reusable patterns;
- accepted tactics;
- general failure modes;
- doctrine proposals;
- Scroll improvement proposals;
- generic examples;
- sanitized case studies;
- framework decisions.

It must not contain:

- private project context;
- emails;
- credentials;
- proprietary data;
- personal data;
- client information;
- raw logs from sensitive projects;
- local assets;
- Local Village configuration.

### Local Village memory

Local Village memory belongs to a specific repo, project, organization, user, or machine.

It may contain:

- local decisions;
- project context;
- work requests;
- copied emails or message summaries;
- corporate language rules;
- user preferences;
- local mission logs;
- local context packs;
- local tactics;
- local archived references;
- local asset metadata.

Local Village memory is private by default and must be ignored by the public Konoha repository unless the user explicitly decides otherwise.

## Recommended storage format

Konoha memory should be stored as Obsidian-compatible Markdown with YAML frontmatter.

Obsidian is the recommended human interface.

Markdown and YAML are the source of truth for portability.

Konoha must not require Obsidian to function.

Other tools may read the same memory format, including VS Code, Foam, Logseq, local scripts, MCP servers, or local LLM tools.

## Recommended vault layout

### Academy vault

```text
memory/
  yamanaka/
    vault/
      00-inbox/
      10-missions/
      20-decisions/
      30-tactics/
      40-failures/
      50-scroll-proposals/
      60-context-packs/
      70-doctrine-proposals/
      90-archive/
```

### Local Village vault

```text
alliance/<village>/
  memory/
    vault/
      00-inbox/
      10-requests/
      20-decisions/
      30-missions/
      40-communications/
      50-context-packs/
      60-local-tactics/
      70-learning-proposals/
      90-archive/
```

## Memory entry types

### Raw mission log

Append-only record of what happened during a mission.

Raw logs may be archived outside active memory after the mission is summarized.

### Mission summary

Short record of what was requested, what was done, what was not done, what was approved, what remains open, and where raw context is archived.

### Decision record

A durable note for decisions that affect future behavior.

Decision records should include:

- decision;
- date;
- context;
- alternatives considered;
- reason;
- owner;
- scope;
- status.

### Tactic card

A reusable operational tactic learned from one or more missions.

A tactic card is not doctrine until it is reviewed and promoted.

### Failure pattern

A known failure mode, including trigger, symptoms, root cause, and prevention rule.

### Learning proposal

A proposed improvement to doctrine, Scrolls, protocols, or local rules.

Learning proposals follow `protocols/learning/learning_policy.md`.

### Context pack

A minimal, sourced, scoped context bundle prepared for a future mission or agent assignment.

Context packs reduce token usage by giving agents only the context they need.

## Required frontmatter

Every memory entry should include frontmatter when practical.

```yaml
type:
scope: academy | local
village:
mission_id:
created_at:
updated_at:
source:
created_by:
reviewed_by:
sensitivity: public | internal | private | confidential
status: draft | active | archived | promoted | rejected
tags:
links:
```

Fields may be omitted only when they are not applicable.

Sensitive local memory must include `scope: local`.

## Context packs

A Context Pack must include:

```yaml
type: context_pack
scope:
village:
mission_id:
sources:
confidence:
open_questions:
expires_at:
```

And should contain:

- a short summary;
- explicit facts;
- decisions already made;
- constraints;
- allowed and forbidden assumptions;
- relevant links;
- unresolved questions.

A Context Pack must not hide uncertainty.

If a source is missing, stale, contradictory, or private, the Context Pack must say so.

## Local LLM and Clerk usage

Local models and Clerks may help with:

- summarization;
- tagging;
- clustering;
- formatting;
- extracting dates and owners;
- drafting context packs;
- detecting possible duplicates;
- preparing archive summaries.

They may not:

- approve memory;
- promote memory to doctrine;
- decide mission success;
- rewrite doctrine;
- expose sensitive memory;
- treat summaries as verified truth.

Any memory generated by a local model or Clerk must be marked as generated or assisted until reviewed.

## Archiving policy

Active memory should stay lightweight.

After a mission is closed, raw context may be moved to an archive location when:

- a mission summary exists;
- important decisions were extracted;
- relevant tactics or failures were captured;
- archive path or reference is recorded;
- sensitive content is protected;
- the user approved archival behavior when required.

A memory summary should preserve enough information to remember:

- what was requested;
- what was delivered;
- what was approved;
- what was deferred;
- where raw context lives;
- what to retrieve if the topic returns.

## Promotion policy

Local memory may be promoted to Academy memory only when:

- sensitive details are removed;
- the user approves promotion;
- the lesson is reusable beyond one Village;
- the evidence is clear;
- Shikamaru drafts the change;
- the required review level approves it.

Promotion may create:

- a doctrine proposal;
- a Scroll improvement;
- a tactic card;
- a failure pattern;
- a protocol update;
- a sanitized example.

Promotion must follow the Learning Policy and Scribe Policy.

## Email and communication memory

Local Villages may store user-provided emails, messages, or work requests only inside local memory.

Agents may:

- summarize requests;
- identify tasks, owners, dates, and pending responses;
- prepare drafts;
- link follow-ups to prior requests.

Agents may not:

- send messages without explicit human approval;
- expose private correspondence to Academy memory;
- invent sender intent;
- treat a draft as sent;
- store raw communication in public memory.

## Retrieval rules

When retrieving memory, agents must prefer:

1. current Mission Charter;
2. explicit user instruction;
3. local decision records;
4. local mission summaries;
5. relevant context packs;
6. accepted tactics;
7. archived raw context, only when needed and allowed.

Agents must not load entire memory by default.

They should retrieve the smallest sufficient set of notes.

## Stop-and-ask triggers

An agent must stop and ask when:

- memory contradicts the current user request;
- memory is the only source for a required permission;
- a memory entry is marked draft, stale, rejected, or uncertain;
- local memory would need to be shared outside the Village;
- sensitive data appears in a memory entry;
- raw archived context is needed but not authorized;
- a summary does not provide enough evidence;
- the agent cannot identify the source of a remembered fact.

## Memory and teachback

When a mission requires Teachback, memory closure should record whether the user confirmed understanding.

The mission should not be marked as completed only because the agent produced an output.

The memory entry should distinguish:

- `done_by_agent`;
- `reviewed`;
- `understood_by_user`;
- `completed`.

## Violations

The following are violations:

- promoting local memory to Academy memory without approval;
- treating summaries as verified facts;
- storing sensitive content in public memory;
- letting a Clerk approve memory;
- modifying doctrine based on raw mission logs without review;
- using memory as permission;
- hiding uncertainty in a context pack;
- archiving raw context without preserving a usable summary.

## Completion requirement

A mission that changes memory must record:

- what memory was created or updated;
- scope of the memory;
- sensitivity level;
- whether it was generated by an agent, Clerk, local model, or human;
- whether it was reviewed;
- whether any learning proposal was created;
- whether anything was archived.
