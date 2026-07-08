# Roadmap

This roadmap describes the expected evolution of Konoha Agentic Academy.

It is not a commitment to implement every item in order. Work that changes doctrine, behavior, permissions, safety, memory, adapters, tools, local context, or public release status still requires the normal mission, approval, review, and teachback flow.

## Current status

Konoha Agentic Academy has its initial public doctrine and first operational workflows in place.

The repository currently includes:

```text
- foundational laws and agent conduct;
- mission, context, safety, approval, review, learning, teachback, and memory policies;
- role policies for Hokage, Kagebunshin, Jounin, Shikamaru, Council, UI, Shinobi, tools, adapters, Marketplace, Sandbox, and Allied Villages;
- mission, Kage Summit, memory, learning, and eval templates;
- initial public Clans for software engineering and Python;
- operational Scrolls for repo review, documentation review, planning, Git safety, coding, code review, Python review, refactoring, test-first work, local context, sensitive data review, teachback, release readiness, learning capture, error triage, dependency review, adapter review, tool review, memory review, publication safety, release notes, changelog maintenance, private literature extraction, and doctrine updates;
- guides for first mission walkthrough, local Village bootstrap, private literature handling, agentic coding loops, and repository audit;
- public contribution, asset, architecture, narrative, and changelog documentation.
```

## Guiding principle

Konoha should become usable before it becomes clever.

The next stages should focus on clear workflows, small executable examples, safe local usage, and reviewable behavior before adding automation, adapters, UI, or marketplace features.

## Phase 0: repository foundation

Status: mostly complete.

Goals:

```text
- establish the public repository structure;
- publish initial doctrine;
- define agent roles and authority boundaries;
- define public vs local/private boundaries;
- add AGENTS.md as the operational entrypoint;
- add templates and initial Scrolls;
- normalize line endings and public repo hygiene;
- keep the repository license clear.
```

Remaining checks:

```text
- verify .gitignore excludes local Allied Villages and private libraries;
- resolve naming inconsistencies;
- update general READMEs after new Clans, Scrolls, guides, and evals;
- run a release readiness review before tagging.
```

## Phase 1: manual mission workflow

Status: in progress.

Goals:

```text
- use Mission Charter template for real missions;
- use Mission Report template for closure;
- use Teachback before declaring completion;
- use Learning Proposal template after useful failures or repeated improvements;
- test read-only repo review with repo_review_scroll;
- test documentation review with documentation_review_scroll;
- test Git safety with git_safety_scroll.
```

Exit criteria:

```text
- at least one complete mission walkthrough exists;
- at least one mission report example exists;
- at least one review example exists;
- at least one teachback example exists;
- at least one learning proposal example exists or is intentionally deferred.
```

## Phase 2: coding workflow

Status: in progress.

Goals:

```text
- use the software engineering Clan as the general coding doctrine layer;
- use the Python Clan for reusable Python expectations;
- use code_change_scroll for bounded edits;
- use code_review_scroll and python_code_review_scroll for review;
- use test_first_scroll where tests are appropriate;
- use refactor_scroll for behavior-preserving cleanup;
- use error_triage_scroll before fixes;
- keep private project conventions inside local Villages.
```

Exit criteria:

```text
- one example coding Mission Charter exists;
- one example code review report exists;
- one Python review rubric exists as public example or local Village example;
- coding-related evals exist for stop-and-ask, review, and completion behavior.
```

## Phase 3: Allied Village bootstrap

Status: in progress.

Goals:

```text
- document local Village setup;
- define local AGENTS.local.md pattern;
- define local context pack pattern;
- define local memory pattern;
- define private literature pattern;
- define local review rubrics;
- verify .gitignore prevents local Village publication by default.
```

Exit criteria:

```text
- local_village_bootstrap.md is tested against an empty local folder;
- private_literature_library.md defines safe handling;
- local context Scroll is usable;
- publication safety Scroll catches local Village leaks.
```

## Phase 4: private literature to approved learning

Status: design complete, examples pending.

Goals:

```text
- keep books and paid material local;
- convert literature only into ignored local folders;
- extract principles without copying protected text;
- convert repeatable principles into local rubrics;
- promote only distilled, license-safe, user-approved learning;
- use Learning Proposal before doctrine updates.
```

Exit criteria:

```text
- one local private-library example structure exists;
- one extracted-principles example exists without copyrighted text;
- one review rubric example exists;
- one Learning Proposal example shows how a principle becomes a rule.
```

## Phase 5: evals

Status: templates added, cases pending.

Goals:

```text
- add eval cases for Mission Charter boundaries;
- add eval cases for Scroll behavior;
- add eval cases for coding review;
- add eval cases for publication safety;
- add regression evals for known failures.
```

Exit criteria:

```text
- eval_case_template.md is used by at least one behavior eval;
- scroll_eval_template.md is used by at least one Scroll eval;
- release readiness checks include eval status;
- high-risk Scrolls are not marked active without evals.
```

## Phase 6: adapters and tools

Status: policy and review Scrolls exist. Implementations deferred.

Goals:

```text
- define minimal adapter contracts;
- define minimal tool contracts;
- test adapters in read-only mode first;
- avoid making the Academy depend on a single vendor or tool;
- keep external tools untrusted by default.
```

Candidate adapters:

```text
- Claude Code;
- Codex;
- Ollama or local model runner;
- Obsidian;
- GitHub;
- notification tools;
- voice tools.
```

Exit criteria:

```text
- adapter capability declaration exists;
- adapter review examples exist;
- tool review examples exist;
- no adapter can grant authority.
```

## Phase 7: first public release

Status: not ready.

Before a first tagged release:

```text
- root README is current;
- AGENTS.md is current;
- CHANGELOG.md is current;
- docs/roadmap.md is current;
- .gitignore protects local Villages and private libraries;
- release_readiness_scroll is run;
- publication_safety_scroll is run;
- sensitive_data_review_scroll is run;
- basic evals exist or missing evals are documented;
- no private content is present;
- no copyrighted assets or literature are present;
- LICENSE is present and consistent with README.
```

## Future ideas

These are not approved scope yet:

```text
- visual dashboard for missions;
- local model routing;
- Obsidian sync;
- agent state telemetry;
- voice mode;
- marketplace metadata;
- runnable adapter examples;
- local Village starter kit;
- public demo missions;
- CI checks for docs and line endings.
```

## Out of scope for now

The following should not be prioritized until the manual workflow is clear:

```text
- autonomous execution across arbitrary repositories;
- automatic doctrine rewriting;
- automatic publication to external systems;
- marketplace auto-install;
- remote execution;
- background agents that act without a Mission Charter;
- collection of private local memory by default;
- committing local Village content to the public repository;
- publishing private literature or converted copyrighted sources;
- copyrighted anime or franchise assets.
```

## Roadmap maintenance

This roadmap should be updated when:

```text
- a phase is completed;
- a new phase becomes necessary;
- a planned item is removed or deferred;
- a release changes the current status;
- a learning proposal is approved and affects project direction.
```

Updates to this roadmap are documentation changes. They may not bypass doctrine, safety, approval, review, or release readiness requirements.

## v0.2.0 focus: Local Village templates

The next milestone focuses on public templates for local Allied Villages.

Planned baseline:

```text
alliance/templates/village/README.template.md
alliance/templates/village/AGENTS.local.template.md
alliance/templates/village/village_manifest.template.md
alliance/templates/village/local_context_pack.template.md
alliance/templates/village/private_boundary_checklist.md
alliance/templates/village/gitignore.template
```

This milestone does not include executable agent runtime, adapter implementation, or real private Village content.

### Local Village bootstrap Scroll

- Add scrolls/local_village_bootstrap_scroll.md to turn Village templates into a safe local bootstrap workflow.

### Local knowledge ingestion

- Document optional local knowledge ingestion for Allied Villages, including local venvs, source cards, principle cards, and promotion boundaries.

### Adapter contracts baseline

- Define adapter contracts before implementing runtime integrations, including manifests, capabilities, safety checklists, and review flow.

### Initial adapter profiles

- Add declarative adapter profiles for Claude, Codex, and Ollama before implementing executable integrations.

### Adapter permission matrix

- Define adapter permission levels before executable integrations, separating technical capability from authorization.

### Adapter profile permission matrices

- Apply explicit permission matrices to Claude, Codex, and Ollama adapter profiles before executable integration.

### Adapter invocation contract

- Define adapter invocation contracts with request envelopes, result envelopes, dry-run behavior, evidence, and approval gates.

### Adapter execution gate baseline

- Define execution gates before runtime implementation, including approval checks, dry-run evidence, command scope, rollback notes, and execution logs.

### Adapter evidence pack baseline

- Define adapter evidence packs before runtime implementation, including pre-execution evidence, post-execution evidence, command records, Git status, and privacy checks.

### Adapter dry-run protocol

- Define adapter dry-run protocol before runtime implementation, ensuring adapters can simulate actions and produce evidence before execution.

### Adapter runtime boundary

- Define adapter runtime boundaries before implementing executable integrations, making clear that v0.3.0 remains declarative and non-executing.

### Evaluation baseline

- Define evaluation templates and review flow before implementing automated eval runners or runtime behavior.

### Initial manual eval cases

- Add initial manual eval cases for Mission Charter enforcement, private-context stop conditions, and adapter dry-run requirements.

### Eval result templates

- Add eval result templates for recording individual eval outcomes and grouped eval run reports before automated runners exist.

### Eval runner boundary

- Define eval runner boundaries before implementing automated eval execution, including safety, privacy, reproducibility, and reporting requirements.

### Runtime planning baseline

- Define runtime planning baseline before executable implementation, including runtime plans, readiness checks, safety boundaries, rollback expectations, and adapter lifecycle constraints.

### Command runner boundary

- Define command runner boundaries before implementing any command execution component, including scope, approval, evidence, rollback, and blocked command categories.

### Filesystem mutation boundary

- Define filesystem mutation boundaries before implementing file creation, editing, movement, overwrite, or deletion behavior.

### Git operation boundary

- Define Git operation boundaries before implementing add, commit, push, tag, release, branch, or history-changing behavior.

### Rollback boundary

- Define rollback boundaries before implementing risky runtime behavior, including rollback plans, recovery evidence, residual risk, and approval gates.

### Runtime lifecycle baseline

- Define runtime lifecycle before executable implementation, including planning, boundary checks, dry-run, approval, execution, evidence, validation, rollback readiness, and closure.

### Runtime audit checklist

- Add runtime audit checklist before runtime release checkpoints or executable runtime proposals.

### Model routing and token governance baseline

- Define model routing and token governance before runtime skeleton, including context capsules, resource probes, token reports, capability review, and escalation/demotion rules.

### Model tier matrix

- Define model tier matrix before runtime skeleton, including Clerk, Draft Worker, Specialist Worker, Reviewer/Jounin, and Orchestrator/Hokage levels.

### Context capsule lifecycle

- Define context capsule lifecycle before runtime skeleton, including source hashes, stale detection, refresh reports, authority boundaries, and full-source fallback.

### Token budget enforcement

- Define token budget enforcement before runtime skeleton, including soft limits, hard stops, overage review, escalation triggers, and capsule/prompt improvements.

### First runtime skeleton

- Define first runtime skeleton after model routing governance, using dry-run-only mission intake, execution planning, adapter stubs, evidence stubs, and runtime state.

### Runtime validation checklist

- Define runtime validation checklist after the first runtime skeleton, including dry-run package validation, blockers, revisions, and review readiness.

### Runtime trace log

- Define runtime trace logging after runtime validation, including append-only trace events, blockers, evidence references, approvals, and supersession.

### Runtime package assembly

- Define runtime package assembly after trace logging, including package manifest, package index, closure record, validation report, trace log, and governance records.

### Dry-run mission examples

- Add public dry-run mission examples after runtime package assembly, using generic scenarios with no private context, no execution, and complete package records.

### Runtime contract and dry-run validator MVP

- Add the first read-only runtime validator after dry-run mission examples, using JSON schemas, fixtures, tests, and explicit non-execution boundaries.

### Dry-run package builder CLI

- Add a dry-run package builder CLI after the read-only validator, generating schema-valid package JSON without mission execution, Git operations, adapter calls, or private context access.

### Read-only runtime inspector

- Add a read-only runtime inspector after the dry-run package builder, checking package coherence, traceability, safety boundaries, and review readiness without modifying files.

### Local sandbox boundary

- Add a local sandbox boundary after the read-only inspector, preparing controlled dry-run run folders and manifests without shell execution, Git operations, adapter calls, or private context access.

### Dry-run runtime runner

- Add a dry-run runtime runner after the local sandbox boundary, orchestrating sandbox preparation, package generation, validation, inspection, and run summary creation without mission execution.

### Runtime run registry

- Add a runtime run registry after the dry-run runtime runner, listing sandbox run history, pass/fail states, blockers, and safety boundaries without modifying files.

### Read-only repo inspector

- Add a read-only repo inspector after the runtime run registry, checking public repository coherence, risky patterns, examples, and safety boundaries without modifying files.

### Controlled artifact writer inside sandbox

- Add a controlled artifact writer after the read-only repo inspector, writing proposed outputs and apply plans only inside sandbox runs without applying changes to the repository.

### Human-approved apply plan prototype

- Add a human-approved apply plan prototype after the controlled artifact writer, previewing sandbox proposals and applying only allowlisted files with explicit approval.

### Git read-only gate

- Add a Git read-only gate after the human-approved apply plan prototype, inspecting repository readiness with allowlisted read-only Git commands before any future Git write gate.

### Git staging gate

- Add a Git staging gate after the Git read-only gate, allowing explicit human-approved staging of allowlisted files without commit or push.

### Unified CLI entrypoint

- Add a unified CLI entrypoint after the Git staging gate, exposing existing safe local-first tools through one allowlisted command surface without adding new runtime authority.

### Project config and policy contract

- Add a project config and policy contract after the unified CLI, centralizing sandbox paths, allowlists, blocked private paths, safety defaults, and approval tokens.

### End-to-end dry-run mission workflow

- Add an end-to-end dry-run mission workflow after the project config contract, connecting config validation, runtime runner, package validation, inspection, registry, repo inspection, and workflow reporting.

### Proposed artifact workflow

- Add a proposed artifact workflow after the end-to-end dry-run mission workflow, connecting sandbox artifact writing, apply preview, optional approved apply, and workflow reporting.

### Git commit gate

- Add a Git commit gate after the Git staging gate, allowing explicit human-approved commits of already staged allowlisted files without push, staging, clean, reset, or history rewrite.

### Integrated tests and CI

- Add integrated tests and CI after the Git commit gate, running unit tests and safe dry-run smoke checks without Git write operations, secrets, adapters, or private context access.

### Mock adapter / Clerk interface

- Add a mock adapter / Clerk interface after integrated tests and CI, producing deterministic sandbox-only outputs without real adapter execution, network access, or private context access.

### Adapter invocation gate disabled by default

- Add an adapter invocation gate after the mock adapter interface, keeping real adapters disabled by default while allowing explicitly approved mock adapter invocation inside sandbox runs.

### Dogfood mission suite

- Add a dogfood mission suite after the adapter invocation gate, using Konoha safe local-first gates as final pre-1.0 evidence before stable release.

### v1.0.0 stable local-first dry-run runtime

- Stabilize v1.0.0 after the Dogfood Mission Suite as the stable local-first dry-run runtime release.

### v1.1.0 Product Runtime Bootstrap

- Add Product Runtime Bootstrap after v1.0.0 to provide init, doctor, config validation, mission workspace creation, and delegated dry-run operation before model and UI work.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.2.0 Mission Workspace

- Add Mission Workspace after Product Runtime Bootstrap to formalize mission-local charter, manifest, inputs, context, plans, outputs, reports, approvals, and evidence before approval-console and model work.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.3.0 Human Approval Console CLI

- Add Human Approval Console CLI after Mission Workspace to define mission status, inspection, approval, rejection, evidence listing, and report listing before model-provider work.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.4.0 Model Provider Contract

- Add Model Provider Contract after Human Approval Console CLI to define provider allowlists, request plans, token budgets, cost limits, redaction checks, and context-source rules before real model invocation gates.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.5.0 Real Model Invocation Gate

- Add Real Model Invocation Gate after Model Provider Contract to permit explicitly approved model calls while preserving sandbox-only outputs and model-output non-authority.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.6.0 Hokage Planner Loop

- Add Hokage Planner Loop after Real Model Invocation Gate to turn gated model evidence into mission-local plan proposals before UI work.

UI implementation remains gated: present draft, screens, stack, permissions, and file plan before creating UI files.

### v1.7.0 Local Web UI Alpha

- Add Local Web UI Alpha after Hokage Planner Loop, using a localhost-only UI for mission review, approval evidence, reports, and system status without adding new runtime authority.

The UI draft was reviewed before implementation. Future UI expansion must preserve no-new-authority boundaries.

Before v2.0.0, pause for a v2.0 Alignment Review Gate conversation before generating v2.0.0 files.

### v1.8.0 Controlled Tool Execution Gate

- Add Controlled Tool Execution Gate after Local Web UI Alpha to allow explicitly approved execution of fixed internal Konoha tools without arbitrary shell, network access, Git operations, repository apply, real model invocation, or private context access.

Before v2.0.0, pause for a v2.0 Alignment Review Gate conversation before generating v2.0.0 files.

### v1.9.0 Human-in-the-loop Agent Runtime

- Add Human-in-the-loop Agent Runtime after Controlled Tool Execution Gate to coordinate planning, model-gated evidence, controlled tool execution, and human review before the v2.0 Alignment Review Gate.

Before v2.0.0, pause for a v2.0 Alignment Review Gate conversation before generating v2.0.0 files.

### v2.0.0 Integration, Memory and Mission Closure

- Release v2.0.0 as Integration, Memory and Mission Closure after the v2.0 Alignment Review Gate, closing missions only with teachback, explicit approval, memory notes, context packs, and safety boundaries.

### v2.1.0 Notifications and UI State Escalation

- Add Notifications and UI State Escalation after v2.0 mission closure, making waiting_user_input, waiting_approval, blocked, ready_for_review, ready_for_teachback, and closed states explicit.

### v2.2.0 Asset Resolver and Local Visual Layer

- Add Asset Resolver and Local Visual Layer after notification state escalation, enabling local-first visual customization through logical asset names and generic public fallbacks.

### v2.3.0 Yamanaka Advanced Memory and Context Packs

- Add Yamanaka Advanced Memory and Context Packs after the asset resolver, strengthening local memory with mission evidence capture, context pack generation, and memory indexing.
