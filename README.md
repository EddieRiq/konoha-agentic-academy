# Konoha Agentic Academy

## v3.4.0 — Finished Local-First Terminal Product

Konoha is installed and operated through one command:

```bash
konoha
```

Start a supervised local workspace:

```bash
konoha quickstart \
  --confirm-quickstart \
  --approval-token START_KONOHA_QUICKSTART

konoha next
```

The product remains local-first, terminal-first and approval-gated. Suggested
commands, status, model output and memory are evidence only.


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

Konoha is a local-first, terminal-first supervised mission framework.

The current public repository includes:

```text
- Unified Mission Runtime and Konoha Beta supervised task runtime;
- Hokage Terminal Shell with review panels, continuity and operator status;
- controlled command, model, apply and Git approval gates;
- deterministic task contracts, evidence bundles and action proposals;
- structured Teachback evidence and evidence-bound mission closure;
- local/private Obsidian-compatible memory;
- canonical release tests, supervised release workflow and recovery status;
- supervised package installation scope guard;
- managed one-line installation and one canonical `konoha` entrypoint.
```

The canonical repository entrypoint is:

```bash
konoha help
```

`v3.4.0` completes the planned local-first terminal product. Repository rationalization and new integrations are post-v3.4 work.

Historical documentation below records how the repository evolved. Statements
describing runtime, CLI or UI as “future” apply to their original release
baseline, not to the current product.

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

## Git staging gate

- Git Staging Gate: stages explicit allowlisted files only with human approval, without commit or push.

The staging gate can preview or stage explicit allowlisted paths using Git. It requires an exact approval token for confirmed staging and does not commit, push, clean, reset, execute missions, invoke adapters, or access private context.

## Unified CLI entrypoint

- `tools/konoha_cli.py` is the canonical repository entrypoint.
- `tools/command_registry.py` defines active and deprecated delegated commands.
- The CLI exposes doctor, status, shell, mission, package and release surfaces.
- It never injects approval tokens, enables network, or weakens delegated gates.

## Project config and policy contract

- Project Config and Policy Contract: centralizes sandbox paths, allowlists, blocked private paths, approval tokens, and safety defaults.

The config validator is read-only. It validates policy, paths, approval tokens, and safety defaults without executing missions, modifying files, performing Git operations, invoking adapters, or accessing private context.

## End-to-end dry-run mission workflow

- End-to-End Dry-run Mission Workflow: connects config validation, runtime runner, package validation, inspection, registry, repo inspection, and workflow reporting.

The workflow writes a mission workflow report inside the sandbox run. It does not execute missions, perform Git operations, invoke adapters, access private context, or apply repository changes.

## Proposed artifact workflow

- Proposed Artifact Workflow: connects dry-run runtime, sandbox artifact writing, apply preview, optional approved apply, and workflow reporting.

The workflow creates proposed artifacts inside sandbox runs and previews apply plans by default. Confirmed apply still requires the delegated human-approved apply gate, exact approval token, and allowlisted destination paths.

## Git commit gate

- Git Commit Gate: commits already staged allowlisted files only with explicit human approval, without push or history rewrite.

The commit gate can preview or commit already staged allowlisted files. It requires an exact approval token for confirmed commits and does not stage files, push changes, clean/reset files, invoke adapters, access private context, or authorize runtime actions.

## Integrated tests and CI

- Integrated Tests and CI: runs unit tests and integrated dry-run smoke tests without adding runtime authority.

The integrated smoke-test runner delegates to existing safe local-first tools and writes reports under sandbox. The CI workflow runs tests and smoke checks without secrets, Git write operations, adapter execution, or private context access.

## Mock adapter clerk interface

- Mock Adapter / Clerk Interface: produces deterministic mock outputs inside sandbox runs without real adapter execution.

The mock adapter is local-only and deterministic. It writes review-required outputs inside sandbox runs and does not call real adapters, use network access, perform Git operations, access private context, or authorize runtime actions.

## Adapter invocation gate

- Adapter Invocation Gate Disabled by Default: gates adapter-shaped workflows while keeping real adapters blocked.

The gate previews adapter requests and can invoke only the deterministic mock adapter with explicit approval, enable flag, and sandbox-only outputs. Real adapter execution remains blocked.

## Dogfood mission suite

- Dogfood Mission Suite: runs Konoha against itself using safe local-first gates before v1.0 stabilization.

The dogfood suite validates config, dry-run mission workflow, proposed artifact workflow, adapter gate behavior, repo inspection, and Git readiness without real adapter execution, Git write operations, private context access, or network access.

## v1.0 release readiness

- v1.0 Release Readiness: verifies the stable local-first dry-run runtime before the v1.0.0 release.

v1.0.0 means Konoha can safely run local-first, human-approved, dry-run-centered agentic workflows that generate, validate, inspect, propose, apply, stage, and commit changes under explicit gates.

v1.0.0 does not mean autonomous execution, real adapter execution by default, network access, private context access by default, Git push automation, or background autonomous missions.

## Product runtime bootstrap

- Product Runtime Bootstrap: adds init, doctor, config validation, mission workspace creation, and delegated dry-run operation from a product-oriented CLI.

The product runtime bootstrap keeps outputs inside sandbox workspace roots by default and does not execute missions, invoke real adapters, access private context, perform Git writes, use network access, or authorize runtime actions.

## Mission workspace

- Mission Workspace: formalizes mission-local charter, manifest, inputs, context, plans, outputs, reports, approvals, and evidence folders.

The Mission Workspace is a local evidence and organization boundary. It does not authorize execution, real adapter invocation, repository apply, Git operations, network access, private context access, or runtime closure.

## Human approval console CLI

- Human Approval Console CLI: records human approval and rejection evidence inside Mission Workspaces.

The approval console records mission-local approval evidence. It does not execute missions, invoke models, invoke real adapters, access private context, apply repository changes, perform Git operations, use network access, or authorize runtime actions by itself.

## Model provider contract

- Model Provider Contract: validates model-shaped request plans, provider allowlists, budgets, context sources, redaction requirements, and non-invocation boundaries.

The Model Provider Contract prepares future model integration without invoking models. A valid request plan is not permission to call a model, use network access, access private context, execute tools, or authorize runtime actions.

## Real model invocation gate

- Real Model Invocation Gate: allows explicitly approved model calls through provider, network, context, budget, and approval boundaries.

The Real Model Invocation Gate can call allowlisted providers only with explicit human approval, exact approval token, safe request plan, no private context, and network approval. Model output is evidence only and never grants permission to execute, apply, stage, commit, push, or close a mission.

## Hokage planner loop

- Hokage Planner Loop: turns gated model output into mission-local plan proposals that require human review.

The Hokage Planner Loop creates review-required plan proposals from gated model evidence. Model output is evidence only and never grants permission to execute, apply, stage, commit, push, access private context, or close a mission.

## Local Web UI Alpha

- Local Web UI Alpha: adds a localhost-only browser UI for dashboard, missions, approvals, reports, and system status without adding runtime authority.

The UI is local-only and filesystem-first. It may read Mission Workspaces, create mission skeletons, record human approval evidence, show reports, and display safety boundaries. It may not execute missions, invoke real models, invoke adapters, apply repository changes, perform Git operations, access private context, store tokens, or run background agents.

Before v2.0.0, Konoha requires a v2.0 Alignment Review Gate conversation to verify that the project remains aligned with the original intent.

## Controlled Tool Execution Gate

- Controlled Tool Execution Gate: executes only allowlisted internal Konoha tools with explicit human approval and sandbox reporting.

The gate does not accept arbitrary shell commands. Controlled tool results are evidence only and never grant permission to apply, stage, commit, push, invoke models, invoke adapters, access private context, or close a mission.

Before v2.0.0, Konoha requires a v2.0 Alignment Review Gate conversation to verify that the project remains aligned with the original intent.

## Human-in-the-loop Agent Runtime

- Human-in-the-loop Agent Runtime: coordinates Mission Workspace validation, Hokage planning, model-gated evidence, controlled tool execution, and human review.

The runtime coordinates existing gates but adds no autonomous authority. Model output, plan proposals, controlled tool results, and runtime reports are evidence only. They never grant permission to apply, stage, commit, push, access private context, invoke adapters, or close a mission.

Before v2.0.0, Konoha requires a v2.0 Alignment Review Gate conversation to verify that the project remains aligned with the original intent.

## v2.0 Integration, Memory and Mission Closure

- v2.0 Integration, Memory and Mission Closure: closes missions only with teachback, explicit approval, minimal Yamanaka memory, context packs, and notification state.

v2.0.0 closes the Konoha mission loop. A mission can close only after explicit human approval and teachback confirmation. Closure writes mission-local reports, teachback records, notification state, and Obsidian-compatible Yamanaka memory notes under an explicit memory root.

Mission closure does not authorize new execution, repository apply, Git operations, model calls, adapter calls, private context access, or doctrine rewrite.

## Notifications and UI State Escalation

- Notifications and UI State Escalation: records mission states such as waiting_user_input, waiting_approval, blocked, ready_for_review, ready_for_teachback, and closed.

Notification state is evidence only. It may tell humans what Konoha needs next, but it does not authorize execution, model calls, adapter calls, repository apply, Git operations, private context access, background agents, or mission closure.

## Asset Resolver and Local Visual Layer

- Asset Resolver and Local Visual Layer: resolves logical UI assets through local, user, public generic, and text fallback tiers without granting runtime authority.

The resolver supports local-first visual customization while keeping public assets generic, original, and license-safe. UI display is evidence only and never authorizes execution, model calls, adapter calls, repository apply, Git operations, private context access, or mission closure.

## Yamanaka Advanced Memory and Context Packs

- Yamanaka Advanced Memory and Context Packs: captures mission evidence into Obsidian-compatible memory notes, builds context packs, and indexes local memory without granting runtime authority.

Memory supports action but does not authorize action. Context packs are not permission. Summaries are not truth. Yamanaka memory does not execute missions, invoke models, invoke adapters, apply repository changes, perform Git operations, access private context by default, rewrite doctrine, or close missions.

## Scroll Lifecycle and Learning Proposals

- Scroll Lifecycle and Learning Proposals: records mission-local learning proposals, review records, indexes, and promotion plans without rewriting doctrine.

Agents may learn, but they may not rewrite doctrine. Learning proposals are evidence only. Review records do not rewrite doctrine. Promotion plans are not permission to modify official Scrolls.

## Local Village Bootstrap and Hardware Profile

- Local Village Bootstrap and Hardware Profile: creates private Local Village scaffolding and read-only hardware profiles without granting runtime authority.

Private context stays local. Hardware profile is evidence only. Local config is not permission. Local Village bootstrap does not authorize execution, private context access, model calls, adapter calls, repository apply, Git operations, doctrine rewrite, background agents, or mission closure.

## Unified Mission Runtime

- Unified Mission Runtime: prepares one mission-level runtime surface with charter, manifest, plan, command proposals, notification state, evidence, reports, and optional memory note.

Command proposals are not permission. Runtime reports are evidence only. v2.6 prepares the mission runtime surface but does not execute arbitrary commands, invoke models, invoke adapters, apply repository changes, perform Git operations, access private context by default, or close missions.

## Model Router and Token Economy

- Model Router and Token Economy: profiles local model runtime, records routing decisions, prepares local model download plans, tracks actual or estimated token usage, and summarizes efficiency.

Model routing is evidence only. Model choice is not permission. Token estimates are not truth. Usage reports do not authorize execution. Local model download plans do not download models.

## General Task Execution Workbench

- General Task Execution Workbench: prepares general supervised technical tasks with playbooks, command batches, verification checklists, rollback notes, evidence capture, and readiness review.

Command proposals are not permission. Recorded command results are evidence only. v2.8 does not execute arbitrary commands. The workbench prepares Konoha for v3.0 supervised real task execution.

## Self-Review, Optimization and Git Operation Gate

- Self-Review, Optimization and Git Operation Gate: records mission self-review, optimization proposals, Git operation plans, and gated git add/commit/push execution.

Self-review is evidence only. Optimization plans are not permission. Git plans are not permission. Git stage, commit and push require separate explicit approvals.

## Konoha Beta Real Supervised Task Runtime

- Konoha Beta Real Supervised Task Runtime: runs supervised real technical missions through terminal workflow, Claude/Codex/Ollama adapters, command approvals, token ledger, self-review, Git gates, and teachback closure.

v3.0.0 is the first beta intended for real supervised technical tasks. It is not autonomous: external agents, local models, command execution, Git operations, and mission closure all require explicit approvals.

## v3.0.1 Local Model Bootstrap

- Local Model Bootstrap, Repo Audit and Patch Flow: profiles the local computer, recommends an Ollama model, prepares install/download approvals, runs a local model repository consistency audit, proposes documentation patches, and hands Git operations to the beta Git gate.

Local model output is evidence only. Patch plans are not permission. Git operations still require explicit approval.

## Konoha Beta Local Model Audit

Konoha v3.0.1 adds a local-first beta patch flow for computer profiling, Ollama local model recommendation, approved local model download, repository consistency audit, documentation patch planning, and gated Git follow-up.

Local model audits are evidence only. Model output is not permission. Repository changes, commits, and pushes still require explicit human approval.

## v3.0.2 Repo Audit Deterministic Guard

- Repo Audit Deterministic Guard: separates local model suggested issues from validated issues, suppresses known false positives with deterministic README/CHANGELOG/docs evidence, and generates patch plans only from validated issues.

Local model output remains evidence only. Suppressed issues are recorded for review but do not authorize patches.

## v3.1.0 Hokage Terminal Shell

- Hokage Terminal Shell: adds a local terminal-first UI for supervised missions, persona selection, ASCII mission panels, deterministic repo scan, optional local model audit handoff, event logging, and private Obsidian-compatible memory notes.

The shell is not permission. Hokage orchestrates but does not execute. Model output and memory notes remain evidence only.

## v3.1.1 Hokage Shell Review Panels

- Hokage Shell Review Panels: improves the terminal UI with human summaries, Markdown step reports, review-latest-result flow, mission timeline view, on-demand raw JSON/patch plan views, and terminal-friendly detail rendering.

The shell still does not authorize patches, commands, Git operations or mission closure.

## v3.1.2 Sandbox Evidence Hygiene

- Sandbox Evidence Hygiene keeps generated mission sessions, audit reports, Git Gate evidence and smoke outputs local while preserving the public sandbox README and placeholder files.

The change does not delete existing evidence and does not alter Hokage Shell, local model audit or beta runtime behavior.

## v3.1.3 Canonical Release Test Gate

- The canonical release test gate discovers every immediate `tests/*` suite containing `test_*.py`, executes each suite independently, continues after failures, and returns a non-zero result when any suite fails.

```bash
python tools/release_testing/run_release_tests.py
```

Test results are evidence only and do not authorize Git or release operations.

## v3.1.4 Release Readiness and Closure Guard

- The read-only closure guard binds canonical test evidence to `HEAD`, verifies branch and tag alignment, detects missing GitHub Releases or Latest promotion, and reports the next required human-approved action.

The guard never creates commits, tags or releases.

## v3.1.5 Hokage Shell Mission Continuity

- The Hokage Shell can list local missions and build read-only resume snapshots using validated session evidence.
- Latest selection uses mission timestamps rather than directory names.
- Resume does not authorize tools, models, Git operations, patches or mission closure.

## v3.1.6 Terminal Operator Baseline

- `tools/hokage_shell/run_hokage_shell.py status` provides a compact read-only snapshot of repository, mission, evidence and terminal context.
- Status is evidence only and does not authorize execution, Git writes, model invocation, network access or private-memory reads.

## v3.2.0 Supervised Task Contract Validator

- `tools/task_contract/validate_supervised_task_contract.py` validates a normalized declarative policy before any execution proposal.
- A `ready` contract is evidence only. It does not authorize commands, models, patches, Git, network, private context or mission closure.

## v3.2.1 Supervised Task Evidence Bundle

- `tools/task_evidence/validate_supervised_task_evidence.py` maps every contract evidence requirement to hashed local sources.
- `complete` means ready for human review, not approved, accepted, executable or closed.

## v3.2.2 Supervised Action Proposal

- `tools/action_proposal/validate_supervised_action_proposal.py` composes contract, evidence and explicit proposed actions.
- `proposed` means ready for human approval review, not approved, authorized or executable.

## v3.2.3 Unified Supervised Release Gate

- `tools/release_workflow/run_supervised_release.py` executes the supervised Acceptance→Git→Release state machine.
- Expected nonzero guards advance only when their canonical `status_code` matches the allowed transition.

## v3.2.4 Supervised Release Recovery and Status

- `tools/release_workflow/run_supervised_release.py --status` inspects local release recovery state without mutation.
- `--status --allow-network` adds read-only remote tag and GitHub Release inspection.

## v3.2.5 Package Installation Scope Guard

- `tools/package_installation/run_supervised_package_installation.py` validates extracted package paths separately from bounded helper changes.
- Package installation completes only when their exact public union matches the manifest.


## v3.2.6 Repository Consolidation, Teachback Closure and CLI Coherence

- Structured Teachback records use levels `0..4`, explicit human evidence,
  execution/review sources and deterministic conflict detection.
- Mission Closure validates successful execution, approved human review and a
  closure-eligible Teachback record before accepting the separate closure token.
- Identical closure reentry is idempotent; contradictory evidence remains
  blocked even when `--force` is present.
- Beta Runtime and Hokage Shell record the same human review contract.
- Unified Mission Runtime, Product Runtime and Hokage Shell declare compatible
  Teachback requirements in their mission manifests.
- The canonical CLI delegates through one command registry while preserving all
  underlying approval, network and filesystem boundaries.

## v3.3.0 Installable Terminal Distribution

Install the exact release with one explicit terminal command:

```bash
curl -fsSL https://raw.githubusercontent.com/EddieRiq/konoha-agentic-academy/v3.3.0/scripts/install.sh | bash -s -- --version v3.3.0 --confirm-install --approval-token INSTALL_KONOHA_CLI
```

Then:

```bash
konoha --version
konoha doctor
konoha status
konoha shell
```

Managed upgrade and uninstall remain separately approved:

```bash
konoha upgrade --target-version v3.4.0 --allow-network --confirm-upgrade --approval-token UPGRADE_KONOHA_INSTALL
konoha uninstall --confirm-uninstall --approval-token UNINSTALL_KONOHA_CLI
```

<!-- v3.5.0-conversational-foundation -->

## Conversational Hokage development

The v3.5.0 development branch makes the primary product entry conversational:

```bash
konoha
```

The `Mission>` prompt interprets a natural-language mission, writes a bounded
intent contract, proposes a Mission Charter and requires an exact approval
phrase. Charter approval does not authorize tools. The menu-driven shell
remains available as `konoha shell legacy` during migration.

See
[`docs/guides/conversational_hokage_foundation.md`](docs/guides/conversational_hokage_foundation.md).

<!-- v3.5.0-conversational-actions -->

### Conversational action orchestration

After exact Charter approval, Hokage creates the supervised runtime
mission and plan, proposes immutable actions and waits for an exact
`APROBAR ACCION-...` phrase bound to the argument hash.

See `docs/guides/conversational_hokage_actions.md`.

<!-- v3.5.0-conversational-lifecycle -->

### Conversational mission lifecycle

After bounded actions, Hokage validates persisted evidence,
proposes human review, requests user-authored Teachback and
requires a separate exact closure approval. Successful closure
writes private Obsidian mission, decision and context-pack notes.

See
[`docs/guides/conversational_hokage_lifecycle.md`](docs/guides/conversational_hokage_lifecycle.md).

<!-- v3.5.0-rc1-real-audit -->

### Real supervised local-model mission

The v3.5.0 release-candidate implementation connects `Mission>` to
deterministic checks, a one-use local Ollama grant, validated finding
classification, exact patch approval, controlled apply, post-patch tests,
review, Teachback, closure and private memory.

The canonical acceptance mission itself must add the final public RC marker
only after displaying and receiving approval for the exact patch.

## Conversational Hokage Release Candidate

Konoha v3.5.0 introduces a conversational Hokage product flow for supervised
missions: natural-language intake, Mission Charter approval, bounded skills,
local-model evidence, deterministic validation, exact patch approval,
controlled apply, tests, human review, Teachback, closure and private memory.

Model output is evidence only. Memory does not authorize action. Git stage,
commit and push remain separate human approval gates.
