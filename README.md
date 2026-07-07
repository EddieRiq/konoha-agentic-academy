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
- **Allied Villages** hold local and private project context.
- **Kage Summit** handles complex or strategic decisions.

The theme is playful. The operating rules are strict.

## Core principle

> If it is not explicit, do not assume it. Stop and ask.

Konoha is designed to reduce hallucinations, uncontrolled edits, hidden assumptions, context-window overload, unsafe automation, and private context leakage.

## Current status

This repository contains the public Academy baseline:

```text
- foundational doctrine;
- mission, approval, safety, context, review, learning, memory, and teachback protocols;
- role policies for Hokage, Kagebunshin, Jounin, Shikamaru, and Council;
- public Clans for reusable specialization;
- Scrolls for bounded workflows;
- templates for missions, reviews, memory, learning, and evals;
- guides for first use, local villages, coding loops, and private literature handling.
```

Runtime automation, UI implementation, marketplace sync, adapters, and local model orchestration are intentionally deferred until the manual workflow is clear and reviewable.

## Repository map

```text
konoha-agentic-academy/
  AGENTS.md
  CHANGELOG.md
  README.md
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

This public repository must not contain private project context, credentials, work data, emails, local assets, copyrighted assets, local literature, private memory, or sensitive context.

## Public Academy vs local Villages

Konoha is the central Academy.

Local repositories or private workspaces are treated as **Allied Villages**. A local Village may contain private rules, project context, local memory, local models, local literature, local assets, and local configurations.

Local Village content stays local by default.

Example:

```text
alliance/kirigakure/
  AGENTS.local.md
  context/
  doctrine/
  memory/
  private-library/
  review-rubrics/
  assets/
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
12. Context is minimized and scoped.

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

## Doctrine, Scrolls, Clans, and learning

Konoha separates behavior into four layers:

```text
Doctrine = Markdown rules that govern behavior.
Clans    = reusable specialization domains.
Scrolls  = bounded workflows selected for a mission.
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

## Coding and review loop

Coding work is handled through bounded missions.

General engineering behavior lives in:

```text
clans/software-engineering/README.md
```

Python-specific behavior lives in:

```text
clans/python/README.md
```

Reusable coding workflows live in:

```text
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
scrolls/python_project_scroll.md
scrolls/refactor_scroll.md
scrolls/test_first_scroll.md
scrolls/error_triage_scroll.md
scrolls/dependency_review_scroll.md
```

The intended loop is:

```text
Kagebunshin writes or changes code within the Mission Charter.
Jounin reviews code against approved doctrine, Scrolls, and local rules.
Shikamaru records repeatable lessons as proposals.
The user approves any doctrine or convention update.
Future missions start from the approved rule.
```

Private books, paid material, converted sources, and local technical literature stay local. Only distilled, license-safe, user-approved principles may be promoted into public doctrine.

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
- copyrighted or franchise-specific assets;
- local literature or converted copyrighted sources.

Public assets must be original, generic, or license-safe.

Franchise-inspired or private assets may exist only in local Villages ignored by Git.

## Recommended reading order

Start here:

```text
AGENTS.md
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
missions/README.md
scrolls/README.md
clans/README.md
memory/yamanaka/yamanaka_memory_policy.md
alliance/README.md
sandbox/README.md
tools/README.md
adapters/README.md
telemetry/README.md
ui/README.md
shinobi/README.md
```

Then use the guides:

```text
docs/guides/README.md
docs/guides/first_mission_walkthrough.md
docs/guides/local_village_bootstrap.md
docs/guides/agentic_coding_loop.md
docs/guides/private_literature_library.md
docs/guides/repository_audit_checklist.md
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

## Public/private boundary

Konoha keeps public doctrine separate from local context.

Local Allied Villages, private literature, converted sources, local memory, secrets, private assets, and project-specific files stay local by default.

See [Public/private boundary](docs/guides/public_private_boundary.md).

## Local Village templates

Konoha includes public templates for creating local Allied Villages without committing private context.

See `alliance/templates/village/`.

A real Village, such as `alliance/kirigakure/`, must stay local and ignored by Git unless explicitly designed for public release.

## Runtime planning

- Runtime planning baseline for future non-autonomous execution architecture.

The current runtime layer is planning-only. Konoha does not yet include executable runtime, autonomous command execution, or automatic Git operations.

## Model routing and token governance

- Model routing and token governance baseline for safe, sufficient, cost-aware intelligence.

Konoha optimizes for safe, sufficient intelligence, not maximum intelligence by default.

## First runtime skeleton

- First runtime skeleton baseline for dry-run-only mission planning.

The first runtime skeleton is documentation-first and dry-run only. It does not execute shell commands, mutate files, perform Git operations, or access private context automatically.

## Dry-run mission examples

- Dry-run mission examples baseline with public, generic, non-executable runtime package examples.

The examples show how Mission Intake, Dry-Run Execution Plan, Validation Report, Trace Log, and Runtime Package Assembly fit together without executing actions.

## Runtime contract and dry-run validator

- Runtime Contract and Dry-run Validator MVP: first read-only executable validator for dry-run runtime packages.

The validator reads dry-run package JSON, validates runtime schemas, checks safety boundaries, and exits with a clear pass/fail result. It does not execute shell commands, mutate files, perform Git operations, invoke adapters, or access private context.

## Dry-run package builder

- Dry-run Package Builder CLI: generates valid dry-run runtime package JSON for validator review.

The builder creates dry-run package JSON in an explicit output folder. It does not execute missions, run shell commands, perform Git operations, invoke adapters, or access private context.

## Read-only runtime inspector

- Read-only Runtime Inspector: inspects dry-run runtime packages for coherence, boundaries, traceability, and review readiness.

The inspector reads dry-run package JSON and reports structural, traceability, and safety boundary findings. It does not modify files, execute commands, perform Git operations, invoke adapters, or access private context.

## Local sandbox boundary

- Local Sandbox Boundary: prepares controlled dry-run sandbox run folders and manifests without mission execution.

The sandbox boundary allows controlled creation of dry-run run folders and manifests inside the local sandbox. It does not execute missions, run shell commands, perform Git operations, invoke adapters, access private context, or write outside the sandbox boundary.

## Dry-run runtime runner

- Dry-run Runtime Runner: orchestrates sandbox preparation, package generation, validation, inspection, and run summary creation.

The runner orchestrates the safe dry-run toolchain inside the sandbox. It does not execute missions, run shell commands, perform Git operations, invoke adapters, access private context, or write outside the sandbox boundary.

## Runtime run registry

- Runtime Run Registry: lists dry-run sandbox runs, states, blockers, and safety boundaries without mutation.

The registry reads sandbox run folders and reports run status, missing artifacts, blockers, and safety boundaries. It does not execute missions, modify files, perform Git operations, invoke adapters, or access private context.

## Read-only repo inspector

- Read-only Repo Inspector: inspects public repository coherence, risky patterns, examples, and safety boundaries without mutation.

The repo inspector reads allowlisted public repository areas and reports coherence, risky patterns, executable examples, and public/private boundary signals. It does not modify files, execute commands, perform Git operations, invoke adapters, or access private context.

## Controlled artifact writer

- Controlled Artifact Writer inside Sandbox: writes proposed artifacts and apply plans only inside sandbox runs.

The artifact writer creates proposed outputs, apply plans, and write reports inside sandbox runs only. It does not apply files to the repository, execute missions, perform Git operations, invoke adapters, or access private context.

## Human-approved apply plan

- Human-approved Apply Plan Prototype: previews and applies sandbox proposed artifacts to allowlisted repo paths only with explicit approval.

The apply plan prototype reads sandbox apply plans, previews proposed changes, and can copy approved artifacts to allowlisted repository paths only with explicit human approval. It does not execute missions, perform Git operations, invoke adapters, or access private context.

## Git read-only gate

- Git Read-only Gate: inspects Git status, tracked files, changed paths, and private-boundary signals without Git write operations.

The gate uses allowlisted read-only Git commands to inspect repository readiness. It does not stage files, create commits, publish changes, clean files, invoke adapters, execute missions, or access private context.
