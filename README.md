# Konoha Agentic Academy

Konoha Agentic Academy is a local-first framework for coordinating agentic work through missions, bounded workers, reviewers, doctrine, memory, and human approval.

It uses a Naruto-inspired operating model:

- **Hokage** orchestrates missions.
- **Kagebunshin** execute bounded work.
- **Jounin** review outputs.
- **Shikamaru** writes doctrine.
- **Yamanaka** manages memory.
- **Clans** specialize capabilities.
- **Scrolls** define reusable workflows.
- **Allied Villages** hold local/private project context.
- **Kage Summit** handles complex or strategic decisions.

The theme is playful. The operating rules are strict.

## Core principle

> If it is not explicit, do not assume it. Stop and ask.

Konoha is designed to reduce hallucinations, uncontrolled edits, hidden assumptions, context-window overload, and unsafe automation.

## What this repository contains

This public repository contains the general Academy structure:

```text
konoha-agentic-academy/
  adapters/
  alliance/
  clans/
  core/
  council/
  docs/
  evals/
  hokage/
  jounin/
  kagebunshin/
  marketplace/
  memory/
  missions/
  protocols/
  sandbox/
  scrolls/
  shikamaru/
  shinobi/
  telemetry/
  tools/
  ui/
```

It should not contain private project context, credentials, work data, emails, local assets, copyrighted assets, or sensitive memory.

## Public Academy vs local Villages

Konoha is the central Academy.

Local repositories or private workspaces are treated as **Allied Villages**. A local Village may contain private rules, project context, local memory, local models, local assets, and local configurations.

Local Village content stays local by default.

Example:

```text
alliance/kirigakure/
  config/
  memory/
  assets/
  private/
```

Local Villages should be ignored by Git unless the user explicitly chooses to publish a safe template or example.

## Foundational laws

The full laws live in:

```text
core/laws/KONOHA_LAWS.md
```

The most important ones are:

1. No Assumption Jutsu.
2. Safety overrides autonomy.
3. Evidence before action.
4. Mission Charter before execution.
5. The Hokage orchestrates, but does not execute.
6. Kagebunshin execute within bounds.
7. Review is required by risk.
8. Shikamaru writes doctrine, but does not create doctrine alone.
9. Agents may learn, but may not rewrite doctrine.
10. Local context stays local by default.
11. Memory supports action, but does not authorize action.
12. The user must understand what was delivered.

When in doubt:

```text
Stop.
State the uncertainty.
Ask the smallest useful question.
Wait for explicit confirmation.
```

## Mission lifecycle

A mission follows this flow:

```text
User request
  ↓
Hokage understanding
  ↓
Missing-context check
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
Completion
```

A mission is not complete just because an agent produced output.

```text
done_by_agent != completed_by_user
```

The user must understand what was done, why it was done, and how to use or defend it at the required level.

## Doctrine, Scrolls, and learning

Konoha separates behavior into three layers:

```text
Doctrine = Markdown rules that govern behavior.
Scrolls  = reusable skills or workflows.
Memory   = mission history, decisions, summaries, failures, and tactics.
```

Agents may propose improvements, but they may not rewrite doctrine.

Learning becomes doctrine only after:

```text
Learning Proposal
  ↓
Hokage review
  ↓
Kage Summit when needed
  ↓
Shikamaru drafting
  ↓
Human approval
  ↓
Jounin review
```

## Memory

Konoha uses Obsidian-compatible Markdown with YAML frontmatter as the preferred memory format.

Obsidian is recommended as a human interface, but Konoha does not depend on Obsidian.

Memory has two major scopes:

```text
Academy Memory
- general patterns
- reusable tactics
- public decisions
- Scroll improvements

Local Village Memory
- private project context
- requests
- communications
- local decisions
- local summaries
```

A memory entry is not permission. A summary is not truth.

## Local models and Clerks

Konoha can use local or low-cost models as **Clerks** for low-risk tasks:

- summarizing logs;
- classifying notes;
- tagging memory;
- preparing context packs;
- checking Markdown structure;
- drafting low-risk text;
- reducing token usage for stronger agents.

Clerks do not approve missions, modify doctrine, decide safety, or close work.

## UI, telemetry, and voice

Konoha supports an oversight-first interface model.

Telemetry reports what is happening. It does not authorize actions.

The UI may show:

- active missions;
- active agents;
- current Scroll;
- waiting user input;
- urgency;
- review state;
- teachback state;
- learning proposals.

The Shinobi theme may use generic ASCII art, terminal visuals, safe sounds, and local asset overrides.

The Voice Layer is transport, not memory:

```text
Speech-to-text only converts voice to text.
Text-to-speech only reads text aloud.
```

Voice does not approve, interpret, store, summarize, or remember content.

## Safety

The public repository must not include:

- credentials;
- `.env` files;
- tokens;
- private data;
- project data;
- local memory;
- work emails;
- private assets;
- copyrighted or franchise-specific assets.

Public assets must be original, generic, or license-safe.

Franchise-inspired or private assets may exist only in local Villages ignored by Git.

## Current status

This repository is in early design and scaffolding stage.

The current focus is doctrine, structure, policies, and operating model.

Runtime implementation, adapters, UI, local model routing, and Obsidian automation will come later.

## Recommended reading order

Start here:

```text
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
docs/narrative.md
docs/architecture/system_overview.md
```

Then review the mission flow:

```text
protocols/mission-charter/mission_charter.md
protocols/approval/approval_policy.md
protocols/context/context_policy.md
protocols/safety/safety_policy.md
protocols/review/review_policy.md
protocols/teachback/teachback_policy.md
```

Then review roles:

```text
hokage/orchestration_policy.md
kagebunshin/worker_policy.md
jounin/reviewer_policy.md
shikamaru/scribe_policy.md
council/kage_summit_policy.md
```

Then review supporting systems:

```text
memory/yamanaka/yamanaka_memory_policy.md
scrolls/README.md
clans/README.md
alliance/README.md
telemetry/README.md
ui/README.md
shinobi/README.md
```

## Contributing

Contribution rules live in:

```text
docs/contributing/contribution_guide.md
docs/contributing/code_of_conduct.md
docs/contributing/asset_contribution.md
```

External Scrolls, adapters, templates, and assets are untrusted by default.

## License

This project is licensed under the MIT License.