# Adapters

Adapters connect Konoha Agentic Academy to external runtimes, tools, and interfaces without making the Academy depend on any single vendor, model, CLI, editor, or service.

Adapters are integration boundaries. They translate Konoha doctrine, Mission Charters, Scrolls, telemetry, and local configuration into the format expected by a specific tool.

They must not create new authority.

## Core rule

Adapters connect Konoha to external systems.

They may not authorize actions, expand mission scope, bypass safety, rewrite doctrine, hide uncertainty, store sensitive content by default, or override local Village rules.

If an adapter cannot operate within Konoha policies, it must stop and report the limitation.

## Purpose

Adapters exist to support integrations such as:

- Codex;
- Claude Code;
- Ollama;
- LM Studio;
- Obsidian;
- GitHub;
- local notification systems;
- local speech-to-text and text-to-speech tools;
- terminal UI or dashboard interfaces;
- future MCP servers or local automation tools.

The Academy core should remain portable. A Mission should be understandable even if one adapter is unavailable.

## What belongs here

This folder may contain:

- setup guides;
- adapter contracts;
- runtime-specific configuration templates;
- install scripts;
- mapping rules between Konoha concepts and runtime concepts;
- examples of safe integration;
- capability matrices;
- troubleshooting notes;
- adapter validation checklists.

Examples:

```text
adapters/
  codex/
    README.md
    AGENTS.template.md
    config.example.toml

  claude-code/
    README.md
    CLAUDE.template.md
    settings.example.json

  ollama/
    README.md
    model_profiles.example.yml

  obsidian/
    README.md
    vault_template/

  notifications/
    README.md
    notification_config.example.yml

  voice/
    README.md
    voice_config.example.yml
```

## What does not belong here

Adapters must not contain:

- private project context;
- secrets;
- API keys;
- `.env` files;
- credentials;
- local memory;
- private emails;
- proprietary files;
- copyrighted local assets;
- raw mission logs from a Local Village;
- doctrine changes that were not approved by Shikamaru and the user.

Private adapter configuration belongs in a Local Village or user-level configuration directory.

## Adapter authority

An adapter may:

- translate configuration;
- launch approved runtimes;
- expose approved commands;
- read approved files;
- format telemetry events;
- route outputs to approved interfaces;
- report limitations;
- request approval when needed.

An adapter may not:

- decide mission goals;
- approve a Mission Charter;
- expand allowed paths;
- add commands to the allowlist;
- bypass sandbox settings;
- suppress warnings;
- store private data by default;
- promote memory to doctrine;
- modify doctrine;
- declare a Mission complete.

## Runtime mappings

Adapters should map Konoha concepts to runtime-specific concepts.

Examples:

```text
Konoha Mission Charter -> Codex task instructions
Konoha Laws -> AGENTS.md top-level rules
Kagebunshin assignment -> subagent prompt or task packet
Scroll -> runtime skill
Yamanaka Context Pack -> attached context summary
Telemetry event -> JSONL event or UI update
Approval request -> runtime approval prompt
```

The mapping must be explicit. If a runtime cannot represent a Konoha rule, the adapter must document the gap.

## Capability declaration

Every adapter should declare its capabilities.

Example:

```yaml
adapter: codex
status: draft
supports:
  mission_charter: true
  subagents: true
  sandbox: true
  approvals: true
  scrolls: true
  telemetry: partial
  voice: false
requires:
  local_config: true
  user_approval_for_external_actions: true
limitations:
  - "Telemetry support depends on runtime hooks or wrapper scripts."
```

## Local configuration

Adapters may include public examples, but real configuration should live outside the public repository.

Recommended locations:

```text
~/.konoha/
alliance/<village>/
.konoha.local/
```

Public examples should use `.example`, `.template`, or placeholder values.

Examples:

```text
config.example.yml
AGENTS.template.md
CLAUDE.template.md
model_profiles.example.yml
```

Real files such as these must not be committed:

```text
.env
config.local.yml
secrets.yml
credentials.json
private_context.md
```

## Model and worker routing

Adapters may expose available models or runtimes to the Hokage.

They may report:

- installed local models;
- available remote models;
- context window limits;
- approximate cost tier;
- tool availability;
- sandbox support;
- approval support;
- hardware requirements.

They may not choose a higher-risk model or broader permission level unless the Mission Charter and Approval Policy allow it.

Model selection remains controlled by the Hokage and the approved configuration.

## Local models

Adapters for local model runtimes, such as Ollama or LM Studio, should prioritize low-risk tasks:

- summarization;
- classification;
- tagging;
- formatting;
- context pack preparation;
- Clerk review;
- simple scaffolding;
- draft generation.

Local models acting as Clerks may not approve technical correctness, safety-sensitive work, doctrine changes, or Mission completion.

## Obsidian and memory adapters

Obsidian adapters must treat Markdown memory as structured memory, not as unrestricted authority.

They may:

- read approved memory entries;
- create draft notes when allowed;
- prepare context packs;
- tag and link notes;
- generate summaries;
- expose graph relationships.

They may not:

- treat memory entries as permission;
- promote local memory to Academy doctrine;
- write sensitive memory to the public repository;
- store raw private content unless explicitly allowed;
- modify doctrine unless acting through Shikamaru workflow.

## Voice adapters

Voice adapters may connect speech-to-text and text-to-speech tools to the UI.

They must follow the Voice Layer Policy.

Core constraint:

```text
Voice Layer is transport, not memory.
```

Voice adapters may not store audio, store transcripts by default, interpret intent, approve actions, or modify outputs.

## Notification adapters

Notification adapters may alert the user when input is needed.

They may:

- play a configured sound;
- show a desktop notification;
- send a local terminal alert;
- escalate reminder level based on approved urgency settings.

They may not:

- spam the user beyond configured limits;
- expose sensitive mission content in notification previews;
- send notifications to external services without approval;
- continue escalation during quiet hours unless explicitly allowed.

## Git and GitHub adapters

Git adapters may help inspect or prepare work.

Allowed by default when approved by the Mission Charter:

- `git status`;
- `git diff`;
- reading branch information;
- preparing commit summaries.

Human approval is required for:

- commit;
- push;
- pull requests;
- branch deletion;
- force push;
- destructive cleanup;
- changing remote configuration.

## Adapter lifecycle

Adapters should move through these stages:

```text
draft
tested
active
revised
deprecated
archived
```

An adapter should not become active until it has:

- a clear purpose;
- documented capabilities;
- documented limitations;
- safety constraints;
- example configuration;
- validation checklist;
- review by Jounin or equivalent;
- user approval if it affects execution.

## Validation checklist

Before activating an adapter, verify:

- it does not require secrets in the public repository;
- it respects Mission Charter boundaries;
- it respects Safety Policy;
- it respects Approval Policy;
- it reports limitations clearly;
- it does not silently widen permissions;
- it does not store sensitive content by default;
- it supports text-only fallback when applicable;
- it logs telemetry safely when enabled;
- it can be disabled without breaking the Academy core.

## Adapter failure

If an adapter fails, it must:

1. stop the affected action;
2. report the failure clearly;
3. avoid retry loops that may cause damage or cost;
4. preserve the Mission Charter boundaries;
5. ask the Hokage for next steps if the failure blocks the Mission.

The adapter must not silently switch to a more permissive or external tool.

## Violations

Adapter violations include:

- bypassing approval;
- broadening permissions;
- reading forbidden files;
- leaking sensitive content;
- storing private data by default;
- hiding runtime limitations;
- modifying doctrine;
- executing external actions without approval;
- treating memory as permission;
- declaring Mission completion.

Violations must be reported to the Hokage and, when relevant, reviewed by Jounin or escalated to Kage Summit.

## Relationship to other doctrine

This file extends:

- `core/laws/KONOHA_LAWS.md`;
- `core/conduct/AGENT_CONDUCT.md`;
- `protocols/approval/approval_policy.md`;
- `protocols/context/context_policy.md`;
- `protocols/safety/safety_policy.md`;
- `protocols/mission-charter/mission_charter.md`;
- `protocols/review/review_policy.md`;
- `sandbox/README.md`;
- `tools/README.md`;
- `ui/voice/voice_layer_policy.md`;
- `memory/yamanaka/yamanaka_memory_policy.md`.

If there is a conflict, safety and explicit user approval win.

## Adapter contract templates

- `templates/`: public adapter contract templates for manifests, capabilities, and safety review.

## Initial adapter profiles

- `claude/adapter_manifest.md`: declarative profile for Claude-style coding assistants.
- `codex/adapter_manifest.md`: declarative profile for Codex-style coding assistants.
- `ollama/adapter_manifest.md`: declarative profile for local Ollama-style model execution.

## Adapter permissions

- `templates/adapter_permission_matrix.template.md`: template for declaring adapter permission levels and approval boundaries.

## Adapter profile permissions

- `claude/adapter_permission_matrix.md`: permission matrix for Claude-style coding assistant adapters.
- `codex/adapter_permission_matrix.md`: permission matrix for Codex-style coding assistant adapters.
- `ollama/adapter_permission_matrix.md`: permission matrix for local Ollama-style model adapters.

## Adapter invocation templates

- `templates/adapter_invocation_request.template.md`: request envelope template for controlled adapter invocation.
- `templates/adapter_invocation_result.template.md`: result template for adapter outputs, evidence, and status reporting.

## Adapter execution gate templates

- `templates/adapter_execution_gate.template.md`: template for approving or blocking adapter execution.
- `templates/adapter_execution_log.template.md`: template for recording execution evidence, status, and outcomes.

## Adapter evidence templates

- `templates/adapter_evidence_pack.template.md`: template for collecting complete adapter invocation evidence.
- `templates/adapter_pre_execution_evidence.template.md`: template for documenting evidence before adapter execution.
- `templates/adapter_post_execution_evidence.template.md`: template for documenting evidence after adapter execution.

## Adapter dry-run templates

- `templates/adapter_dry_run_request.template.md`: template for requesting a non-mutating adapter dry-run.
- `templates/adapter_dry_run_result.template.md`: template for reporting dry-run findings, proposed actions, risks, and required approvals.
