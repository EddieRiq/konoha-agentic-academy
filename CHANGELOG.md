## [4.2.1] — Natural Repository Study Conversations

Patch release on top of v4.2.0. This is a new post-v4.2.0 release; it is
unrelated to the earlier internal v4.2.1 engineering package label, whose
content shipped inside v4.2.0.

### Fixed

- A natural Spanish or multiline request such as “Mirá este repositorio y
  explicame…” could fall through into normal mission planning instead of
  repository comprehension. Such turns now reach the existing repository study
  through deterministic, conservative intent recognition.
- While a study is active, natural follow-ups (clarification, evidence
  requests, acknowledgements) continue that study instead of starting a
  mission.
- Novice explanations are evidence-backed: each repository statement carries
  its source locators, and missing evidence is reported as missing.
- Ordinary prose in the repository-root README is retained as purpose
  evidence; other Markdown keeps its previous command/flag-only extraction.
- Add an exact frozen novice journey regression with byte-exact,
  hash-verified human turns.

### Safety

- No LLM intent classifier; recognition uses fixed word lists, and any
  change/fix/add/run request still routes to a normal supervised mission.
- Repository-study turns do not invoke providers or mission planning.
- Repository study grants no authority. Ordinary acknowledgements such as
  “ok, gracias” do not close teachback; only exact `:entendido` closes
  repository understanding, and that closure grants no execution approval.

## [4.2.0] — Repository Comprehension, Supervised Learning and Conversational Integration

One integrated release. The earlier internal v4.2.0/v4.2.1 engineering
package labels (including gates C1/C2A/C2B/C3) were never separate releases.

### Repository comprehension and exact evidence

- Materialize every canonical required source with explicit bounds; retain one
  resolution mapping for both the executor gate and worker context.
- Load the exact original request from durable continuity and remove raw
  dependency output from worker prompts. Missing material pauses before invoke
  without consuming approval or fabricating provider evidence.
- Bind plans to the exact persisted RepositoryEvidencePack and its full-content
  hash. Stale, missing or corrupt approved evidence requires replanning; resume
  never reacquires it.
- Add generic, evidence-linked repository studies and a local terminal workflow.
- Refuse file aliases into excluded content and use descriptor-relative evidence
  reads; preserve tracked-deletion fingerprints and the failure-log boundary.

### Human repository teachback

- Extend the canonical teachback engine with a repository comprehension loop
  closed only by exact human `:entendido`, separate from execution and closure.

### Supervised recommendations and public-repository learning

- Build proposal-only self-improvement recommendations from retained evidence.
- Reuse local-model audit's validated/suppressed approach while distinguishing
  linked model suggestions from deterministic observations.
- Compare explicitly authorized local public repositories with provenance on
  both sides, after human repository teachback. Donor lessons carry compatibility,
  licensing and scope concerns; recommendations never authorize adoption.
- Keep acquisition from real remotes as a separate human/network boundary.

### Conversational CLI integration

- Route repository study, explanation, evidence display, private resume,
  recommendations and donor comparison through the existing `konoha`
  conversation (`understand this repository`, `:repo help`), reusing the same
  study and teachback APIs rather than a parallel engine.
- External local checkouts require a fresh exact `:repo authorize <challenge>`
  command; naming a path or answering `yes` grants nothing.
- `implement recommendation NUMBER` enters the existing supervised mission
  planning flow with the recommendation as evidence-only context; nothing is
  applied directly.

### Safety

- Repository routes do not probe or invoke providers, run tests or
  application code, or patch files.
- Repository understanding grants no execution approval and does not replace
  mission teachback or closure evidence.
- Recommendations remain `proposed` with `authorizes_action=false`; donor code
  is never copied or adopted by study.
- No automatic provider/family fallback was added.

### Known limitations

- Legacy plans that need repository evidence must be replanned; an absent
  evidence binding cannot authorize acquisition. Changed repository content
  requires a new planning transaction or study.
- Evidence extraction is static, bounded and primarily Python-oriented.
- A provider may still return schema-valid but semantically weak evidence;
  provider output remains evidence only.

## [4.1.1] — Human Turn Integrity and Corrective Replanning Stability

- Deterministic exact-line framing for mission and requested-change block
  input, plus exact-line reads for control and authority responses (exit,
  approval, plan-approval challenges), closing ambiguity between free-form
  text and control input.
- A confirmed requested change requires a fresh feedback-confirmation nonce,
  and plan approval / `--plan-only` acceptance require a fresh
  plan-identity-bound challenge; deterministic corrective model retries
  remain internal, bounded, and never prompt the human.
- Bounded corrective retries are shared by initial planning and
  human-requested replanning through the same retry path, instead of two
  divergent implementations.
- Confirmed human authority (approval, rejection, requested changes) is kept
  strictly separate from deterministic validator evidence in continuity
  state; the two are never conflated into a single record.
- `validator_findings_history` is defensively copied before being folded
  into corrective continuity context, preventing newly recorded validator
  findings from appearing twice in the model-facing corrective retry
  context while durable findings remain recorded exactly once.
- `MissionPlan` is now imported at runtime in `tools/konoha_v4/conversation.py`
  (it was previously only referenced in annotations, never imported), so its
  type hints resolve correctly under `from __future__ import annotations`.
- `run()`'s top-level mission prompt now recognizes the full canonical
  `_EXIT_COMMANDS` set (including `q` and `:salir`) instead of a narrower
  duplicated literal, so every documented exit control actually exits.
- Expanded deterministic regression coverage across human-turn reading,
  approval-input stabilization, replanning contracts, and top-level exit
  handling.
- Supervised Claude → Codex/Jounin runtime smoke completed successfully
  ahead of this release.

### Known limitation

- A provider may return schema-valid but semantically weak evidence.
  Provider output remains evidence only; independent review may still block
  the mission. This is not fixed in v4.1.1.

## [4.1.0] — Supervised Technical Planning

- Adds native `konoha --plan-only`, a `tools/konoha_v4` CLI mode that
  produces, deterministically validates, displays and lets a human review
  and iterate on a technical MissionPlan without ever granting execution
  authority.
- `--plan-only` and `--resume` are mutually exclusive at the argument-parser
  level; omitting both keeps the existing executable conversational runtime
  as the unchanged default.
- Reuses the existing v4 build/validate/replanning machinery
  (`conversation.run()`, `_build_validated_plan()`, `_approval_loop()`)
  unchanged except for stopping at review acceptance instead of execution
  authority.
- Preserves the existing human requested-change / replanning loop, including
  confirmed-change provenance recorded via
  `MissionContinuityStore.record_requested_change()`.

### Safety

- Human acceptance in `--plan-only` mode means acceptance of the planning
  artifact only; `MissionPlan.approval` remains `status="pending"` and no
  `AssignmentApproval` is created or consumed.
- Continuity execution approval remains ungranted.
- No canonical executable `plan.json` is written, and `execution_state.json`
  is never created, since `--plan-only` never reaches the execution path.
- No assignment/executor invocation occurs in `--plan-only` mode.
- No `MissionPlan` or `ExecutionState` schema changes; `plan_hash` and
  `plan_identity` are unaffected.
- Normal executable conversational execution mode is unchanged.
- Legacy `run_technical_plan` remains registered, provider-routed, fail-closed
  and untouched.
- `fallback` remains declarative only; no automatic provider/family fallback
  was added.

## [4.0.2] — Runtime Continuity & Provider Integrity

- Re-probes the exact pending assignment provider immediately before every
  provider invocation instead of trusting approval-time readiness.
- Requires the exact approved Ollama model to be present in a fresh local
  model inventory before invocation.
- Pauses resumably on provider/model readiness failure using stable
  machine-readable diagnostics.
- Revalidates readiness independently between assignments executed in the
  same process/session.
- Preserves v4.0.0 and v4.0.1 persisted-plan compatibility without changing
  MissionPlan, ExecutionState, plan_hash or plan_identity.

### Safety

- Provider readiness remains operational evidence only; it never grants or
  replaces human authority.
- A readiness failure does not invoke the provider, consume assignment
  approval, invoke fallback, substitute provider/model, or persist execution
  progress.
- Codex/Claude readiness currently proves provider-level executable/version
  availability only; it does not deterministically prove authentication or
  exact model availability.
- No automatic retry, fallback, provider substitution or Ollama model pull
  was added.
- Cross-session repository HEAD/worktree drift remains outside this patch.

## [4.0.1] — Mission Integrity Hardening

- Adds a structured mission constraint manifest (`mission_constraints`) for
  new provider-generated MissionPlans.
- Hokage deterministically validates supported structured constraints
  against the generated MissionPlan before approval/execution.
- Requires exact `source_text` provenance from authorized human mission or
  confirmed requested-change text; no fuzzy/paraphrase matching.
- Makes extracted constraints visible to the human during plan approval.
- Preserves v4.0.0 persisted-plan compatibility and legacy plan identity:
  `mission_constraints=None` plans keep producing their original hash.

### Safety

- Model extraction of `mission_constraints` remains proposal/evidence only;
  it does not claim complete deterministic understanding of arbitrary
  natural language.
- Human review remains required for semantic completeness of the extraction.
- No automatic fallback/failover was added.
- No new mutation or execution authority was added.

## [4.0.0] — Conversational Multi-Agent Operating Core

- Added Codex-led conversational mission conduction, constitutional Hokage validation, specialized agent families, real provider evidence, proportional plan approval and explicit-knowledge stops.

<!-- v3.5.0 -->
## [3.5.0] — Conversational Hokage Useful Product

### Added

- Real conversational repository-audit mission using local Ollama.
- Deterministic pre-model and post-patch validation.
- One-use model grants bound to mission action hashes.
- Suggested, validated and suppressed issue separation.
- Exact patch preview, changed paths, SHA-256 and approval gate.
- Controlled patch application without Git authorization.
- Private model-usage and audit memory at closure.

### Safety

- External network, model download, arbitrary shell and automatic Git remain
  blocked.

<!-- v3.5.0-slice3 -->
### Slice 3 — Review, Teachback and closure

- Added deterministic action-evidence validation.
- Added exact conversational human review approval.
- Added user-authored structured Teachback recording.
- Added separate exact mission closure approval.
- Added private Obsidian mission, decision and context-pack outputs.
- Added closed-mission continuity and returning-session behavior.
- Added canonical full-lifecycle CLI semantic smoke coverage.

<!-- v3.5.0-slice2 -->
### Slice 2 — Conversational action orchestration

- Added bounded conversational skills.
- Added exact action approvals bound to argument hashes.
- Connected approved actions to the supervised beta runtime.
- Added successful read-only execution and reentry coverage.
- Removed editable-install metadata from the working tree.

<!-- v3.5.0-slice1 -->
## Unreleased — v3.5.0

### Added

- Conversational `Mission>` entry for natural-language mission intake.
- Deterministic intent contracts and Mission Charter proposals.
- Exact Charter approval and rejection phrases.
- Compact private continuity state and Obsidian dashboard/handoff.
- Legacy menu recovery command: `konoha shell legacy`.

### Safety

- Charter approval does not authorize tools, models, patches, Git or network.
- Slice 1 performs no tool or model execution.

# Changelog

All notable changes to Konoha Agentic Academy are tracked in this file.

This project is early stage. Version numbers may be adjusted once the first public release process is defined.

## [Unreleased]

### Added



- Finished the local-first terminal product with guided quickstart, evidence-based next actions, user-focused help and quiet managed distribution flows.
- Added v3.3.0 Installable Terminal Distribution with one-line managed installation, global `konoha`, explicit upgrade/uninstall and the supervised package-to-release wrapper.
- Added v3.2.6 Repository Consolidation, Teachback Closure and CLI Coherence with structured human Teachback evidence, execution/review-bound mission closure, idempotent conflict guards, a canonical command registry, aligned runtime manifests and terminal documentation.


























































































- Added v3.2.5 Package Installation Scope Guard with explicit direct paths, helper paths, exact union validation and idempotent reentry.
- Added v3.2.4 Supervised Release Recovery and Status with read-only reentry states, stale evidence detection and closed-release inspection.
- Added v3.2.3 Unified Supervised Release Gate with explicit RC/status transitions, single-run Git delivery and release closure.
- Added v3.2.2 Supervised Action Proposal with contract/evidence composition, bounded argv proposals, approval requirements and rollback validation.
- Added v3.2.1 Supervised Task Evidence Bundle with deterministic contract/source hashing, requirement coverage, claims, findings and unresolved evidence validation.
- Added v3.2.0 Supervised Task Contract Validator with normalized scope, operation, approval, evidence, review, completion, Teachback and stop-trigger policy validation.
- Added v3.1.6 Terminal Operator Baseline with a read-only `status` command for repository, mission, evidence and terminal context.
- Added v3.1.5 Hokage Shell Mission Continuity with deterministic mission inventory, validated latest selection, read-only resume snapshots, invalid-session reporting, schema, example, tests, guide, roadmap scope and review Scroll.
- Added v3.1.4 Release Readiness and Closure Guard with commit-bound canonical test evidence, local and remote Git/tag checks, GitHub Release state inspection, stable closure codes, schema, example, tests, guide, roadmap scope and review Scroll.
- Added v3.1.3 Canonical Release Test Gate with deterministic suite discovery, independent unittest execution, continue-after-failure behavior, aggregate summaries, sandbox-only JSON reports, tests, schema, example, guide, roadmap scope and review Scroll.
- Added v3.1.2 Sandbox Evidence Hygiene to keep generated runtime evidence under `sandbox/` local while preserving the public README and placeholder files.
- Added v3.1.1 Hokage Shell Review Panels with human summaries, Markdown step reports, review-latest-result flow, mission timeline view, on-demand JSON/patch-plan viewers, token summaries, suppressed issue visibility, tests, examples, guide, roadmap, and review Scroll.
- Added v3.1.0 Hokage Terminal Shell with terminal-first mission UI, persona selection, ASCII panels, deterministic repo scan, optional local model audit handoff, event logs, schemas, examples, guide, roadmap, review Scroll, and private Obsidian-compatible memory notes.
- Added v3.0.2 Repo Audit Deterministic Guard with model-suggested issues, deterministic marker validation, validated issues, suppressed possible false positives, guarded patch planning, schema update, tests, examples, guide, roadmap, and review Scroll.
- Added v3.0.1 Local Model Bootstrap, Repo Audit and Patch Flow with WSL/local computer profile, Ollama model recommendation, approved model download, local model repo consistency audit, documentation patch plan, schemas, tests, examples, guide, roadmap, and review Scroll.
- Added Konoha Beta Real Supervised Task Runtime with terminal mission runtime, Claude Code adapter, Codex adapter, Ollama adapter, command approval execution, token ledger, self-review, Git gates, teachback closure, schemas, tests, examples, guide, roadmap, and review Scroll.
- Added Self-Review, Optimization and Git Operation Gate with mission self-review, optimization plans, Git operation plans, gated stage/commit/push operations, schemas, tests, examples, guide, roadmap reference, and review Scroll.
- Added General Task Execution Workbench with mission initialization, general playbooks, command batch proposals, verification checklists, rollback notes, command result evidence recording, review reports, schemas, tests, examples, guide, and review Scroll.
- Added Model Router and Token Economy with model runtime profiling, routing decisions, local model download plans, token usage ledger, calibration, summaries, schemas, tests, examples, guide, and review Scroll.
- Added Unified Mission Runtime with mission-level charter, manifest, runtime plan, command proposals, notification state, evidence, reports, optional memory note, schemas, tests, examples, guide, and review Scroll.
- Added Local Village Bootstrap and Hardware Profile with private Village scaffolding, read-only hardware profile, local config schema, bootstrap report schema, tests, examples, guide, alliance template, and review Scroll.
- Added Scroll Lifecycle and Learning Proposals with mission-local learning proposals, lifecycle reviews, promotion plans, proposal indexing, schemas, templates, tests, examples, guide, and review Scroll.
- Added Yamanaka Advanced Memory and Context Packs with memory vault initialization, mission capture, context pack generation, memory indexing, schemas, tests, examples, guide, templates, and review Scroll.
- Added Asset Resolver and Local Visual Layer with logical asset resolution, generic public assets, local override support, asset schemas, tests, examples, guide, and review Scroll.
- Added Notifications and UI State Escalation with mission notification state manager, state event schema, state report schema, tests, examples, guide, and review Scroll.
- Added v2.0 Integration, Memory and Mission Closure with Mission Closure Gate, Teachback Record, minimal Yamanaka Memory, Context Pack generation, Notification State schema, tests, examples, guides, reference, and review Scroll.
- Added Human-in-the-loop Agent Runtime with delegated planning, model-gated evidence, controlled tool execution, runtime report schema, state schema, tests, examples, guide, and review Scroll.
- Added Controlled Tool Execution Gate with allowlisted internal tool execution, explicit approval token, plan schema, report schema, tests, examples, guide, and review Scroll.
- Added Local Web UI Alpha with localhost-only dashboard, Mission Workspace views, approval evidence recording, reports, system status, schemas, tests, examples, guide, and review Scroll.
- Added Hokage Planner Loop with planning-only model-evidence flow, plan proposal schema, planner report schema, tests, examples, guide, and review Scroll.
- Added Real Model Invocation Gate with explicit approval, provider calls, network approval, sandbox-only model outputs, schemas, tests, examples, guide, and review Scroll.
- Added Model Provider Contract with provider allowlists, model request plans, token/cost budgets, context-source rules, validation CLI, schemas, tests, examples, guide, and review Scroll.
- Added Human Approval Console CLI with mission status, inspection, approval, rejection, approval-event listing, evidence/report listing, schemas, tests, examples, guide, and review Scroll.
- Added Mission Workspace with mission-local charter, manifest, approval log, evidence structure, validation CLI, schemas, tests, examples, guide, and review Scroll.
- Added Product Runtime Bootstrap with init, doctor, config validation, mission workspace creation, delegated dry-run operation, report schema, tests, example report, guide, and review Scroll.
- Added v1.0 release-readiness baseline with readiness checker, report schema, tests, example report, capability matrix, release safety boundaries, guide, and review Scroll.
- Added Dogfood Mission Suite with safe delegated workflow checks, dogfood report schema, tests, example report, guide, and review Scroll.
- Added Adapter Invocation Gate Disabled by Default with mock-only approved invocation, real-adapter blocking, gate report schema, policy schema, tests, examples, guide, and review Scroll.
- Added Mock Adapter / Clerk Interface with deterministic sandbox-only mock outputs, invocation report schema, output schema, tests, examples, guide, and review Scroll.
- Added Integrated Tests and CI with integrated smoke-test runner, report schema, tests, example report, GitHub Actions workflow, guide, and review Scroll.
- Added Git Commit Gate with staged-file validation, approval token, commit report schema, tests, example report, guide, and review Scroll.
- Added Proposed Artifact Workflow with sandbox artifact workflow CLI, workflow report schema, tests, example report, guide, and review Scroll.
- Added End-to-End Dry-run Mission Workflow with mission workflow CLI, unified CLI mission command, workflow report schema, tests, example report, guide, and review Scroll.
- Added Project Config and Policy Contract with example config, config schema, read-only config validator, tests, example report, guide, and review Scroll.
- Added Unified CLI Entrypoint with allowlisted dispatch over existing Konoha tools, routing tests, CLI example, guide, and review Scroll.
- Added Git Staging Gate with explicit allowlisted staging, approval token, staging report schema, tests, example report, guide, and review Scroll.
- Added Git Read-only Gate with allowlisted Git inspection commands, readiness report schema, tests, example report, guide, and review Scroll.
- Added Human-approved Apply Plan Prototype with preview/apply CLI, explicit approval token, allowlisted destinations, apply report schema, tests, example report, guide, and review Scroll.
- Added Controlled Artifact Writer inside Sandbox with proposed outputs, sandbox apply plan schema, artifact write report schema, tests, example apply plan, guide, and review Scroll.
- Added Read-only Repo Inspector with public repo coherence checks, repo inspection report schema, tests, example report, guide, and review Scroll.
- Added Runtime Run Registry with read-only run listing, registry report schema, tests, example report, guide, and review Scroll.
- Added Dry-run Runtime Runner with sandbox orchestration, package generation, validation, inspection, run summary schema, tests, example summary, guide, and review Scroll.
- Added Local Sandbox Boundary with sandbox guard, sandbox run preparation CLI, sandbox run manifest schema, tests, example manifest, guide, and review Scroll.
- Added Read-only Runtime Inspector with package coherence checks, boundary inspection, JSON report output, tests, example report, guide, and review Scroll.
- Added Dry-run Package Builder CLI with package generation, validator-compatible output, tests, example package, guide, and review Scroll.
- Added Runtime Contract and Dry-run Validator MVP with runtime JSON schemas, read-only validator CLI, fixtures, tests, examples, guide, and review Scroll.
- Added Dry-run Mission Examples with public example packages, examples README, guide, and review Scroll.
- Added Runtime Package Assembly with package manifest, package index, package closure template, and package review Scroll.
- Added Runtime Trace Log with append-only trace log template, trace event template, and trace review Scroll.
- Added Runtime Validation Checklist with validation checklist template, validation report template, and validation review Scroll.
- Added First Runtime Skeleton with mission intake, dry-run execution plan, adapter invocation stub, evidence collection stub, runtime state template, and dry-run review Scroll.
- Added Token Budget Enforcement with soft limits, hard stops, overage review, and enforcement review Scroll.
- Added Context Capsule Lifecycle with capsule manifest, refresh report, stale detection, and review Scroll.
- Added Model Tier Matrix with tier assignment, capability review, escalation, and demotion templates.
- Added Model Routing and Token Governance baseline with context capsules, session resource probe, budget templates, token usage reporting, and review Scrolls.
- Added Runtime Audit Checklist with checklist template and review Scroll.
- Added Runtime Lifecycle baseline with lifecycle and closure report templates.
- Added Rollback Boundary with rollback request/result templates and readiness review.
- Added Git Operation Boundary with Git request/result templates and readiness review.
- Added Filesystem Mutation Boundary with mutation request/result templates and readiness review.
- Added Command Runner Boundary with command execution request/result templates and readiness review.
- Added Runtime Planning baseline with runtime README, planning guide, readiness templates, and review Scroll.
- Added Eval Runner Boundary guide, readiness template, and review Scroll.
- Added eval result and eval run report templates with result review Scroll.
- Added initial manual eval cases for behavior, safety, and adapter dry-run enforcement.
- Added Evaluation baseline with behavior, safety, adapter eval templates, guide, and review Scroll.
- Added Adapter Runtime Boundary guide, readiness template, and review Scroll.
- Added Adapter Dry-Run Protocol with request/result templates and review Scroll.
- Added Adapter Evidence Pack baseline with pre-execution, post-execution, and review templates.
- Added Adapter Execution Gate baseline with approval, logging, and review templates.
- Added Adapter Invocation Contract with request/result templates and review Scroll.
- Added permission matrices for Claude, Codex, and Ollama adapter profiles.
- Added Adapter Permission Matrix guide, template, and review Scroll.
- Added initial declarative adapter profiles for Claude, Codex, and Ollama.
- Added Adapter Contracts baseline with public templates, guide, and review Scroll.
- Added Local Knowledge Ingestion guide, Scroll, and Village templates.
- Added Local Village bootstrap Scroll for creating ignored local Allied Villages from public templates.
- Added public templates for local Allied Villages under lliance/templates/village/.
- Public/private boundary guide for local Villages, private literature, memory, assets, and ignored context.
- Root agent entrypoint with `AGENTS.md`.
- Mission templates for Mission Charters and Mission Reports.
- Kage Summit templates for briefs and verdicts.
- Yamanaka Memory templates for memory notes and learning proposals.
- Eval templates for generic cases and Scroll-specific cases.
- Initial operational Scrolls:
  - repo review;
  - documentation review;
  - mission planning;
  - Git safety;
  - local context handling;
  - sensitive data review;
  - teachback;
  - release readiness;
  - learning capture;
  - error triage;
  - dependency review;
  - adapter review;
  - tool review;
  - memory review;
  - publication safety;
  - release notes;
  - changelog maintenance;
  - code change;
  - code review;
  - Python code review;
  - Python project review;
  - refactoring;
  - test-first workflow;
  - private literature extraction;
  - doctrine update.
- Public Clans for:
  - software engineering;
  - Python.
- Guides for:
  - first mission walkthrough;
  - local Village bootstrap;
  - private literature library handling;
  - agentic coding loop;
  - repository audit checklist.
- Project roadmap.

### Changed

- Root README updated to reflect MIT license, coding workflow, public Clans, guides, and private literature boundary.
- Scrolls README updated to document the current flat Scroll layout and future nested layout.
- Clans README updated to reflect active public Clans and naming conventions.
- Evals README updated to reference templates and coding workflow evals.
- Roadmap updated with current manual, coding, Allied Village, private literature, eval, adapter, and release-readiness phases.

### Deprecated

- Nothing deprecated yet.

### Removed

- No removals recorded yet.

### Fixed

- Resolved intended Clan naming direction: use `software-engineering`, not `software_engineering`.

### Security

- Clarified that private books, paid material, converted sources, proprietary docs, local literature, local memory, credentials, work data, and private Village context must not be committed to the public repository.

## [0.1.0] - 2026-07-03

### Added


- Initial public doctrine for Konoha Agentic Academy.
- Core laws and agent conduct.
- Hokage, Kagebunshin, Jounin, Shikamaru, Council, Scroll, Clan, Memory, UI, Shinobi, Telemetry, Adapter, Tool, Marketplace, Sandbox, and Mission documentation.
- Foundational protocols for:
  - approval;
  - context;
  - learning;
  - mission charter;
  - review;
  - safety;
  - teachback.
- Public contribution documentation.
- Asset contribution policy.
- Code of conduct.
- System overview and narrative documentation.
- MIT license declaration through the repository license.

### Notes

- This release establishes the public structure and doctrine baseline.
- Local Allied Village content is intentionally excluded from the public repository.
- External items remain untrusted by default.
- Execution remains bounded by Mission Charter, Safety Policy, Context Policy, Approval Policy, Review Policy, and Teachback Policy.

## [3.5.1]

- Aligned package, runtime and managed-installer versions.
- Added a release-blocking canonical version contract.

## [3.6.0]

- Added constitutional authority and deterministic contracts.
- Added supervised environment bootstrap, provider discovery and hardware analysis.
- Added mission classification, provider/model proposals and economy estimates.
- Added anti-loop, Jōnin review, telemetry and Teachback contracts.
- Added supervised private village initialization.
- Rebuilt the README and release documentation.
