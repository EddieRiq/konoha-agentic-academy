# Local Village bootstrap

This guide explains how to create a private Allied Village for local project context.

A Local Village is a workspace that connects private context, local memory, project-specific rules, tools, and optional local models to Konoha Agentic Academy without committing sensitive material to the public repository.

## Core rule

Local Village context stays local by default.

Do not commit private client context, internal project notes, credentials, personal data, proprietary files, local memory, private assets, machine-specific paths, or generated outputs unless they have been explicitly reviewed and approved for publication.

## When to create a Local Village

Create a Local Village when a project needs context that should not live in the public Academy repository.

Examples:

- private work projects;
- internal documentation;
- client-specific rules;
- local Obsidian vaults;
- personal operating notes;
- local model configuration;
- private assets;
- project-specific Mission history;
- sensitive logs or diagnostics;
- experiments that are not ready for publication.

Do not create a Local Village just to store generic documentation that belongs in the public Academy.

## Recommended local path

For the first local village, use:

```text
alliance/kirigakure/
```

Kirigakure is the first example Allied Village. Other local villages may use different names, but they must follow the same safety rules.

## Git safety

Before creating a Local Village, confirm that the local village path is ignored by Git.

Recommended `.gitignore` entries:

```gitignore
# Local Allied Villages
alliance/kirigakure/
alliance/*/local/
alliance/*/memory/
alliance/*/private/
alliance/*/secrets/
alliance/*/assets/
alliance/*/outputs/
alliance/*/.env
alliance/*/.env.*
```

Then verify:

```bash
git check-ignore -v alliance/kirigakure/
```

If Git does not report an ignore rule, stop and fix `.gitignore` before adding any private files.

## Minimal folder structure

A Local Village can start small.

```text
alliance/kirigakure/
  README.md
  AGENTS.local.md
  mission_charters/
  mission_reports/
  context/
    packs/
    raw/
  memory/
    notes/
    learning_proposals/
    archive/
  assets/
  outputs/
  tools/
  adapters/
  secrets/
```

Keep the structure simple. Add folders only when they are needed.

## Folder purpose

### `README.md`

Explains what the Local Village is for.

It should include:

- project name or local village purpose;
- owner;
- allowed use;
- forbidden use;
- links to relevant public Academy doctrine;
- local safety notes;
- local context boundaries.

Do not include secrets or personal data.

### `AGENTS.local.md`

Defines local instructions for agents.

It may add stricter rules than the public Academy, but it may not weaken Academy rules.

It should include:

- required local files to read;
- local paths that are allowed;
- local paths that are forbidden;
- available tools;
- local review rules;
- stop-and-ask triggers;
- sensitive data rules.

### `mission_charters/`

Stores approved local Mission Charters.

Use the public template:

```text
missions/templates/mission_charter_template.md
```

### `mission_reports/`

Stores completed mission reports.

Use the public template:

```text
missions/templates/mission_report_template.md
```

### `context/packs/`

Stores curated context packs for agents.

A context pack is a small, explicit bundle of relevant context. It should be sourced, scoped, and limited to the mission.

### `context/raw/`

Stores raw local context when needed.

Raw context can be large, messy, or sensitive. Agents should not read it unless the Mission Charter explicitly allows it.

### `memory/notes/`

Stores local memory notes.

Use:

```text
memory/yamanaka/templates/memory_note_template.md
```

### `memory/learning_proposals/`

Stores local learning proposals.

Use:

```text
memory/yamanaka/templates/learning_proposal_template.md
```

A local learning proposal does not become Academy doctrine unless it is reviewed, drafted by Shikamaru, and approved by the user.

### `assets/`

Stores local assets.

Private, franchise-specific, copyrighted, client-specific, or internal assets must stay local.

### `outputs/`

Stores generated files, reports, drafts, logs, or temporary deliverables.

Review outputs before publishing or copying them into the public repository.

### `tools/`

Stores local helper scripts.

Local tools may help execution, but they do not grant authority.

### `adapters/`

Stores local adapter configuration.

Adapters connect systems. They do not grant authority.

### `secrets/`

Stores secret references only if needed.

Prefer external secret managers or `.env` files that are ignored by Git. Do not store credentials in Markdown.

## Bootstrap steps

### 1. Create the folder

PowerShell:

```powershell
New-Item -ItemType Directory -Force ".\alliance\kirigakure"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\mission_charters"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\mission_reports"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\context\packs"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\context\raw"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\memory\notes"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\memory\learning_proposals"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\memory\archive"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\assets"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\outputs"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\tools"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\adapters"
New-Item -ItemType Directory -Force ".\alliance\kirigakure\secrets"
```

WSL or Linux:

```bash
mkdir -p alliance/kirigakure/{mission_charters,mission_reports,assets,outputs,tools,adapters,secrets}
mkdir -p alliance/kirigakure/context/{packs,raw}
mkdir -p alliance/kirigakure/memory/{notes,learning_proposals,archive}
```

### 2. Confirm Git ignore

```bash
git check-ignore -v alliance/kirigakure/
```

Expected result: Git prints the ignore rule that protects the folder.

If there is no output, stop.

### 3. Create `README.md`

Start with:

```md
# Kirigakure

Kirigakure is a private Allied Village connected to Konoha Agentic Academy.

This folder may contain local context, private memory, local tools, local adapters, private assets, and project-specific mission records.

This folder must stay out of the public repository.
```

### 4. Create `AGENTS.local.md`

Start with:

```md
# Local agent instructions

Read the public `AGENTS.md` first.

This file adds local rules for Kirigakure. It may make Academy rules stricter, but it may not weaken them.

Local context stays local by default.

No agent may read, summarize, copy, modify, publish, or archive local context unless the action is explicitly allowed by an approved Mission Charter.
```

### 5. Create the first context pack

Use a small file under:

```text
alliance/kirigakure/context/packs/
```

Recommended naming:

```text
context_pack_<project>_<purpose>.md
```

Example:

```text
context_pack_repo_review_backend_scoring.md
```

A context pack should include:

- mission-relevant facts;
- source references;
- allowed use;
- forbidden use;
- freshness;
- sensitivity level;
- open questions.

### 6. Create the first Mission Charter

Use:

```text
missions/templates/mission_charter_template.md
```

Store the local copy under:

```text
alliance/kirigakure/mission_charters/
```

Do not begin execution until the charter is approved.

## Local Kage

Each Local Village may have a Local Kage.

The Local Kage coordinates local context, local agents, local memory, and local tools.

The Local Kage may not override:

- Konoha laws;
- safety policy;
- context policy;
- approval policy;
- review policy;
- mission charter requirements;
- user approval;
- public repository publication rules.

When local rules conflict with Academy rules, the stricter rule wins.

## Local memory

Local memory belongs to the Local Village.

It may support future missions, but it does not authorize actions.

Before writing memory, confirm:

- the Mission Charter allows memory writing;
- the note has a clear source;
- sensitive content is minimized;
- no secrets are stored;
- the note does not convert a lesson into doctrine;
- the user can review the memory entry.

## Local tools and models

A Local Village may use local tools or local models.

Examples:

- local summarizers;
- file classifiers;
- embedding search;
- Obsidian helpers;
- local LLMs;
- notification scripts;
- project-specific validators.

These tools are assistants, not authorities.

They may not approve actions, expand scope, bypass review, publish content, or change doctrine.

## Publication boundary

Before moving anything from a Local Village to the public Academy repository, run a publication safety review.

Use:

```text
scrolls/publication_safety_scroll.md
scrolls/sensitive_data_review_scroll.md
```

Check for:

- credentials;
- personal data;
- internal project details;
- private paths;
- proprietary documentation;
- copyrighted assets;
- private memory;
- local decisions presented as public doctrine;
- generated outputs with hidden sensitive content.

## Common violations

These are violations:

- committing `alliance/kirigakure/`;
- copying local memory into public docs without review;
- using private context to write public doctrine without sanitization;
- letting an agent inspect local folders without explicit permission;
- storing credentials in Markdown;
- treating a local learning proposal as approved Academy doctrine;
- using local copyrighted assets in public examples;
- publishing internal project structure by accident.

## Minimal readiness checklist

Before using a Local Village:

```text
[ ] Local path exists.
[ ] Local path is ignored by Git.
[ ] README.md exists.
[ ] AGENTS.local.md exists.
[ ] Sensitive folders are ignored.
[ ] No secrets are stored in Markdown.
[ ] First context pack is scoped.
[ ] First Mission Charter is drafted.
[ ] User approval is required before execution.
[ ] Publication safety review is required before moving anything public.
```

## Related doctrine

Read these before using a Local Village:

```text
AGENTS.md
alliance/README.md
protocols/context/context_policy.md
protocols/safety/safety_policy.md
protocols/approval/approval_policy.md
memory/yamanaka/yamanaka_memory_policy.md
scrolls/local_context_scroll.md
scrolls/publication_safety_scroll.md
scrolls/sensitive_data_review_scroll.md
```

## Final rule

A Local Village may make agents more useful.

It may not make them less bounded.

## Public templates

The recommended starting point for a local Village is:

```text
alliance/templates/village/
```

Copy the templates into the local Village and rename them as needed.

Recommended mapping:

```text
README.template.md -> README.md
AGENTS.local.template.md -> AGENTS.local.md
village_manifest.template.md -> village_manifest.md
local_context_pack.template.md -> context/local_context_pack.md
private_boundary_checklist.md -> private_boundary_checklist.md
gitignore.template -> .gitignore
```

The generated local Village must remain ignored by Git unless explicitly approved for publication.
