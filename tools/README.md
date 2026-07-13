# Tools

Konoha tools are auxiliary utilities that support orchestration, safety, context management, notifications, learning, and local setup.

Tools are not agents.  
Tools do not decide mission scope.  
Tools do not approve actions.  
Tools do not override doctrine.

They provide structured support for the Hokage, Local Kage, Kagebunshin, Jounin, Shikamaru, Clerks, and the UI.

## Core rule

Tools assist the mission flow.

They may not authorize actions, expand scope, modify doctrine, store sensitive content by default, or bypass the Mission Charter, Safety Policy, Context Policy, Approval Policy, Review Policy, or Teachback Policy.

## Purpose

The `tools/` directory exists for reusable helper scripts and utilities that make Konoha safer, more observable, more efficient, and easier to operate.

Examples:

- measuring context confidence;
- asking the user for missing information;
- sending local input-needed notifications;
- selecting an appropriate model tier;
- preparing learning proposals;
- sanitizing reports;
- inspecting machine capabilities with approval;
- validating local configuration;
- building context packs;
- checking files before commit.

## Tool categories

### Context tools

Context tools help the Hokage decide whether enough information exists to proceed.

Examples:

```text
context_score
context_pack_builder
source_tracker
missing_context_detector
```

Allowed actions:

- inspect approved context;
- identify missing information;
- create context summaries;
- calculate confidence signals;
- report uncertainty.

Forbidden actions:

- invent missing context;
- treat memory as permission;
- load private context without approval;
- silently include sensitive information in a Context Pack.

### User interaction tools

User interaction tools help Konoha ask for clarification, approval, or Teachback.

Examples:

```text
ask_user
confirm_intent
teachback_prompt
```

Allowed actions:

- ask specific questions;
- request approval;
- request Teachback;
- format the user's choices clearly.

Forbidden actions:

- assume consent;
- interpret silence as approval;
- pressure the user to approve;
- hide uncertainty behind confident language.

### Notification tools

Notification tools alert the user when a mission needs input.

Examples:

```text
notify_pending
notify_urgent
notification_scheduler
```

Allowed actions:

- send local notifications;
- play configured sounds;
- update UI status;
- escalate reminders according to urgency settings.

Forbidden actions:

- approve actions;
- modify mission state beyond notification metadata;
- send external messages without approval;
- bypass quiet hours unless explicitly configured.

### Routing tools

Routing tools help select a model, agent, rank, or review level.

Examples:

```text
budget_router
model_router
review_router
worker_selector
```

Allowed actions:

- recommend a worker type;
- recommend a model tier;
- estimate cost and capability needs;
- recommend review level.

Forbidden actions:

- assign permissions outside the Mission Charter;
- choose a higher-risk path without approval;
- treat model confidence as evidence;
- skip review because a model appears capable.

### Learning tools

Learning tools help convert mission experience into structured learning artifacts.

Examples:

```text
learning_proposal_builder
failure_pattern_extractor
tactic_candidate_builder
merge_learning
```

Allowed actions:

- summarize what happened;
- extract candidate tactics;
- prepare Learning Proposals;
- identify failures and repeated patterns.

Forbidden actions:

- modify doctrine;
- promote local learning to Academy doctrine;
- rewrite Scrolls;
- treat generated summaries as truth without review.

### Safety tools

Safety tools help detect risky content, risky commands, sensitive files, or unsafe diffs.

Examples:

```text
sanitize_report
secret_detector
dangerous_command_checker
asset_license_checker
diff_scope_checker
```

Allowed actions:

- detect obvious secrets;
- redact sensitive values from reports;
- warn about dangerous commands;
- flag unsafe assets;
- check whether diffs exceed mission scope.

Forbidden actions:

- print secrets;
- copy sensitive data to public memory;
- inspect forbidden files without approval;
- declare a mission safe without required review.

### Local setup tools

Local setup tools help initialize an Allied Village and recommend a safe local configuration.

Examples:

```text
machine_inspector
local_profile_builder
village_config_validator
ollama_model_checker
```

Allowed actions, with explicit human approval:

- run read-only machine inspection commands;
- detect OS, CPU, RAM, GPU, VRAM, disk, Git, Python, Node, Ollama, or LM Studio;
- recommend worker count;
- recommend local Clerk models;
- validate local config.

Forbidden actions:

- read project files unrelated to inspection;
- read credentials;
- read emails;
- install dependencies without approval;
- change configuration without Shikamaru drafting and user approval.

### Archive tools

Archive tools help move heavy context out of active memory while preserving traceability.

Examples:

```text
archive_mission_context
archive_manifest_builder
hash_context_bundle
```

Allowed actions:

- prepare archive manifests;
- compute hashes;
- move approved raw context to an approved archive location;
- leave a summary and pointer in Yamanaka Memory.

Forbidden actions:

- archive sensitive content without approval;
- copy local memory into the public repository;
- delete active context without confirmation;
- treat archived content as automatically approved context.

## Tool lifecycle

Tools follow a controlled lifecycle.

```text
proposed
draft
tested
active
revised
deprecated
archived
```

### Proposed

A tool idea exists, usually from a Learning Proposal or Kage Summit Verdict.

### Draft

Shikamaru creates the folder, Markdown description, purpose, boundaries, and acceptance criteria.

### Tested

A Kagebunshin implements and tests the tool in a sandbox or local environment.

### Active

The tool is approved for use in missions.

### Revised

The tool is updated after learning, review, or bug fixes.

### Deprecated

The tool should no longer be used, but is kept for traceability.

### Archived

The tool is removed from active flows and preserved only for history.

## Tool structure

Recommended structure:

```text
tools/
  <tool-name>/
    README.md
    examples/
    tests/
    src/
```

For simple tools, this may be enough:

```text
tools/
  <tool-name>/
    README.md
```

The `README.md` must define:

```yaml
name:
status:
purpose:
inputs:
outputs:
allowed_actions:
forbidden_actions:
requires_approval:
safety_notes:
related_policies:
acceptance_criteria:
```

## Tool creation

Shikamaru may create tool folders and Markdown documentation.

For non-Markdown technical files, Shikamaru prepares:

- purpose;
- requirements;
- boundaries;
- expected inputs and outputs;
- safety constraints;
- acceptance criteria;
- test expectations.

A Kagebunshin implements the technical files only after approval.

## Tool execution

A tool may run only when:

- the Mission Charter allows it;
- the required context is available;
- the action is within the tool's documented purpose;
- required approval has been granted;
- Safety Policy does not block the action.

If any condition is missing, the tool must not run.

## Tool outputs

Tool outputs are not automatically truth.

A tool output may be used as:

- evidence candidate;
- summary candidate;
- recommendation;
- warning;
- checklist result;
- structured input for Hokage review.

A tool output may not be used as:

- permission;
- doctrine;
- final approval;
- proof of completion;
- replacement for Jounin review when review is required.

## Local tools

Allied Villages may define local tools.

Local tools may support:

- private workflows;
- local corporate communication;
- local memory;
- local assets;
- local model routing;
- local machine constraints.

Local tools stay local by default.

They must not be committed to the public Academy unless:

- sensitive content is removed;
- the tool is generalized;
- Shikamaru drafts the contribution;
- review confirms it is safe;
- the user approves the promotion.

## Tool security

Tools must follow the Safety Policy.

Tools must not:

- read `.env` files unless explicitly approved;
- print secrets;
- transmit data externally without approval;
- execute destructive commands without approval;
- install packages without approval;
- bypass sandbox rules;
- modify doctrine;
- modify Mission Charters;
- modify memory promotion status;
- approve their own outputs.

## Tool telemetry

When a tool runs, it should emit structured telemetry when supported.

Minimum event fields:

```yaml
event_type:
tool_name:
mission_id:
agent:
started_at:
completed_at:
status:
inputs_summary:
outputs_summary:
sensitive_content_involved:
approval_reference:
```

Telemetry must not include raw secrets or sensitive content by default.

## Tool review

Tools require review based on risk.

Low-risk documentation-only tools may receive Clerk review.

Tools that execute commands, inspect files, modify state, access memory, process sensitive data, or affect mission routing require Jounin review.

Tools that change safety, approval, doctrine, model routing, or memory promotion behavior require Kage Summit review.

## Violations

A tool violates policy if it:

- runs without mission approval;
- expands scope;
- modifies doctrine;
- accesses forbidden files;
- stores sensitive content without approval;
- hides errors;
- invents results;
- treats its output as approval;
- bypasses review;
- fails silently.

Violations must be reported to the Hokage and recorded according to the Learning Policy and Yamanaka Memory Policy.

## Completion checklist

Before a tool becomes active:

- purpose is explicit;
- inputs and outputs are documented;
- allowed and forbidden actions are documented;
- approval requirements are documented;
- safety risks are documented;
- tests or validation steps exist;
- telemetry behavior is defined;
- review level is assigned;
- Shikamaru has drafted documentation;
- required approval has been granted.

## Canonical release test gate

- `release_testing/run_release_tests.py`: discovers and executes each immediate test suite independently, aggregates results, and optionally writes a JSON report under `sandbox/`.

## Release readiness and closure guard

- `release_closure/check_release_closure.py`: binds test evidence to a commit and detects incomplete local, remote-tag and GitHub Release states without mutation.

## Hokage Shell mission continuity

- `hokage_shell/mission_continuity.py`: validates local mission sessions, lists valid and invalid missions, and builds read-only reentry snapshots.

## Hokage terminal operator status

- `hokage_shell/operator_status.py`: builds a local, read-only operator snapshot without creating workspace or memory directories.

## Supervised task contract validator

- `task_contract/validate_supervised_task_contract.py`: validates declarative task scope, operations, approvals, evidence, review, completion and Teachback without execution.

## Supervised task evidence validator

- `task_evidence/validate_supervised_task_evidence.py`: validates contract-linked evidence coverage, source hashes, claims, findings and unresolved items without collection or execution.

## Supervised action proposal validator

- `action_proposal/validate_supervised_action_proposal.py`: validates contract/evidence references, scope, argv, approvals, risk and rollback without execution.

## Unified supervised release workflow

- `release_workflow/run_supervised_release.py`: composes beta Git gates, canonical tests and release closure into one token-gated workflow.
