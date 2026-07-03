# Roadmap

This roadmap describes the expected evolution of Konoha Agentic Academy.

It is not a commitment to implement every item in order. It is a planning document. Any work that changes doctrine, behavior, permissions, safety, memory, adapters, tools, or public release status still requires the normal mission, approval, review, and teachback flow.

## Current status

Konoha Agentic Academy has its initial public doctrine in place.

The repository currently includes:

- foundational laws and agent conduct;
- mission, context, safety, approval, review, learning, teachback, and memory policies;
- role policies for Hokage, Kagebunshin, Jounin, Shikamaru, Council, UI, Shinobi, tools, adapters, Marketplace, and Allied Villages;
- initial templates for missions, Kage Summit, memory notes, and learning proposals;
- initial operational Scrolls for repo review, documentation review, planning, Git safety, local context, sensitive data review, teachback, release readiness, learning capture, error triage, dependency review, adapter review, tool review, memory review, publication safety, release notes, and changelog maintenance;
- public contribution, asset, architecture, narrative, and changelog documentation.

## Guiding principle

Konoha should become usable before it becomes clever.

The next stages should focus on clear workflows, small executable examples, safe local usage, and reviewable behavior before adding automation, adapters, UI, or marketplace features.

## Phase 0: repository foundation

Status: mostly complete.

Goals:

- establish the public repository structure;
- publish initial doctrine;
- define agent roles and authority boundaries;
- define public vs local/private boundaries;
- add AGENTS.md as the operational entrypoint;
- add templates and initial Scrolls;
- normalize line endings and public repo hygiene;
- keep the repository license clear.

Exit criteria:

- README renders correctly;
- LICENSE is present;
- AGENTS.md points agents to the right documents;
- the main doctrine files are committed;
- no private local Village content is committed;
- no sensitive data, secrets, internal paths, or copyrighted franchise assets are included.

## Phase 1: usable mission workflow

Status: next priority.

Goals:

- create example mission records using the existing templates;
- show how a user request becomes a Mission Charter;
- show how review and teachback close a mission;
- add a small set of example mission reports;
- document the difference between planning, execution, review, teachback, and learning;
- create a minimal end-to-end walkthrough.

Recommended additions:

```text
missions/examples/
  0001_repo_review/
    mission_charter.md
    mission_report.md
    teachback.md

docs/guides/
  first_mission_walkthrough.md
  mission_lifecycle_example.md
```

Exit criteria:

- a new user can understand how to run a mission without guessing;
- every example keeps execution bounded by a Mission Charter;
- examples do not require private context;
- examples are safe for a public repository.

## Phase 2: local Village bootstrap

Status: planned.

Goals:

- define a safe local bootstrap pattern for Allied Villages;
- document how to create a private Village without committing it;
- define local context packs;
- define a local Obsidian-compatible memory layout;
- define how local learnings can be proposed for public promotion;
- add example `.gitignore` patterns for local Villages.

Recommended additions:

```text
alliance/templates/
  local_village_README_template.md
  local_kage_policy_template.md
  local_context_pack_template.md

docs/guides/
  local_village_bootstrap.md
```

Exit criteria:

- users can create a local Village safely;
- local memory stays local by default;
- public repo content remains generic;
- local overrides do not weaken Academy policy.

## Phase 3: example Scroll execution

Status: planned.

Goals:

- provide worked examples for initial Scrolls;
- show expected inputs and outputs;
- define review requirements per Scroll;
- add example reports for read-only repo review, documentation review, and sensitive data review;
- avoid adding automation before the manual workflow is clear.

Recommended additions:

```text
scrolls/examples/
  repo_review_example.md
  documentation_review_example.md
  sensitive_data_review_example.md

docs/guides/
  using_scrolls.md
```

Exit criteria:

- a user can apply a Scroll manually;
- agents can follow Scroll instructions without inventing permissions;
- outputs are reviewable and traceable.

## Phase 4: minimal tool contracts

Status: planned.

Goals:

- define tool interface contracts before implementing tools;
- specify expected inputs, outputs, permissions, and failure modes;
- keep tools as helpers, not authorities;
- avoid tool behavior that silently stores sensitive content.

Candidate tool contracts:

```text
tools/contracts/
  ask_user_contract.md
  context_score_contract.md
  sanitize_report_contract.md
  notify_pending_contract.md
  budget_router_contract.md
  merge_learning_contract.md
```

Exit criteria:

- each tool contract states what the tool may and may not do;
- no tool grants authority;
- tool outputs are compatible with mission reports and review.

## Phase 5: adapter contracts

Status: planned.

Goals:

- define adapter contracts for external systems;
- document capability declarations;
- define safe defaults for local, CLI, memory, Git, notification, and voice adapters;
- keep adapters replaceable.

Candidate adapter contracts:

```text
adapters/contracts/
  codex_adapter_contract.md
  claude_code_adapter_contract.md
  ollama_adapter_contract.md
  obsidian_adapter_contract.md
  git_adapter_contract.md
  notification_adapter_contract.md
  voice_adapter_contract.md
```

Exit criteria:

- adapters declare capabilities explicitly;
- external systems do not gain authority through integration;
- local/private context remains protected;
- adapters fail closed when scope is unclear.

## Phase 6: evaluation suite

Status: planned.

Goals:

- add behavioral eval cases for core laws and policies;
- test common failure modes;
- test that agents stop and ask instead of assuming;
- test that tools, adapters, and Scrolls do not override authority;
- test sensitive data and publication safety behavior.

Recommended additions:

```text
evals/cases/
  no_assumption_jutsu.md
  mission_charter_required.md
  sensitive_data_stop.md
  local_context_boundary.md
  doctrine_change_requires_approval.md
  memory_does_not_authorize.md
```

Exit criteria:

- core behaviors have regression tests;
- failed evals block promotion of related Scrolls or adapters;
- eval results are documented.

## Phase 7: first public release

Status: planned.

Goals:

- run release readiness review;
- run publication safety review;
- update CHANGELOG.md;
- prepare release notes;
- tag the first public release;
- keep release scope honest.

Candidate version:

```text
v0.1.0
```

Release readiness criteria:

- README, LICENSE, AGENTS.md, CHANGELOG.md, and roadmap are present;
- core doctrine is internally consistent;
- templates and initial Scrolls are present;
- no private context or sensitive data is committed;
- no copyrighted franchise assets are committed;
- examples are public-safe;
- release notes describe what exists and what does not exist yet.

## Later ideas

These are intentionally not immediate priorities.

Possible later work:

- simple CLI for creating mission folders from templates;
- local-first UI prototype;
- Obsidian vault helpers;
- local model Clerk workflows;
- notification integration;
- voice transport layer prototype;
- marketplace metadata format;
- automated eval runner;
- example Allied Village bootstrap script;
- GitHub issue templates;
- pull request templates;
- contributor onboarding examples.

These ideas should not be treated as approved scope until a Mission Charter is created and approved.

## Out of scope for now

The following should not be prioritized until the manual workflow is clear:

- autonomous execution across arbitrary repositories;
- automatic doctrine rewriting;
- automatic publication to external systems;
- marketplace auto-install;
- remote execution;
- background agents that act without a Mission Charter;
- collection of private local memory by default;
- committing local Village content to the public repository;
- copyrighted anime or franchise assets.

## Roadmap maintenance

This roadmap should be updated when:

- a phase is completed;
- a new phase becomes necessary;
- a planned item is removed or deferred;
- a release changes the current status;
- a learning proposal is approved and affects project direction.

Updates to this roadmap are documentation changes. They may not bypass doctrine, safety, approval, review, or release readiness requirements.
