# Changelog

All notable changes to Konoha Agentic Academy are tracked in this file.

This project is early stage. Version numbers may be adjusted once the first public release process is defined.

## [Unreleased]

### Added








































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
