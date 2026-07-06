# {{VILLAGE_NAME}}

This folder is a local Allied Village for Konoha Agentic Academy.

It is designed for private project context, local memory, local agents, local tools, project-specific conventions, and ignored assets.

This Village must stay local unless the repository owner explicitly decides to publish a safe, sanitized subset.

## Rule

Local Village context stays local by default.

A Village may specialize Konoha doctrine, but it may not weaken it.

## Required reading

Before any agent uses this Village, it must read:

```text
AGENTS.md
docs/guides/public_private_boundary.md
alliance/README.md
alliance/templates/village/README.template.md
```

Inside this Village, agents must also read:

```text
AGENTS.local.md
village_manifest.md
private_boundary_checklist.md
```

If the mission involves code, agents must read the relevant Clan and Scroll files, for example:

```text
clans/software-engineering/README.md
clans/python/README.md
scrolls/code_change_scroll.md
scrolls/code_review_scroll.md
scrolls/python_code_review_scroll.md
```

## Recommended local structure

```text
{{VILLAGE_SLUG}}/
  README.md
  AGENTS.local.md
  village_manifest.md
  private_boundary_checklist.md
  local_context_pack.md

  context/
    project_overview.md
    architecture.md
    conventions.md
    commands.md
    risks.md

  doctrine/
    coding_conventions.md
    data_conventions.md
    review_rubrics.md

  memory/
    local/
    learning-proposals/
    decisions/

  private-library/
    books/
    papers/
    articles/

  assets/
    private/
    local-overrides/

  tools/
    local/

  adapters/
    local/

  outputs/
  tmp/
```

## What belongs here

Use this Village for:

```text
- private project context;
- local paths and environment notes;
- local coding conventions;
- private literature and converted sources;
- project-specific rubrics;
- private memory;
- local assets;
- local tools;
- ignored generated outputs;
- local model notes;
- local adapter configuration.
```

## What does not belong here

Do not store:

```text
- secrets in plain text;
- passwords;
- access tokens;
- private keys;
- customer data;
- personal identifiers;
- unredacted logs;
- production credentials;
- copyrighted content intended for publication;
- files that should be committed to the public Academy repo.
```

If sensitive content is needed for work, keep it outside Git and refer to it through safe summaries, local paths, or user-approved context packs.

## Git boundary

This Village should be ignored by the public repository.

Before adding private files, verify:

```bash
git check-ignore -v alliance/{{VILLAGE_SLUG}}/README.md
git check-ignore -v alliance/{{VILLAGE_SLUG}}/private-library/example/source.md
git check-ignore -v alliance/{{VILLAGE_SLUG}}/.env
```

If a private Village file is not ignored, stop and fix `.gitignore` before continuing.

## Agent behavior

Agents working inside this Village must:

```text
- follow the root AGENTS.md;
- follow AGENTS.local.md;
- work only within an approved Mission Charter;
- avoid assumptions;
- avoid publishing private context;
- use local doctrine only within this Village;
- escalate conflicts to the user;
- report evidence instead of confidence;
- stop when scope or sensitivity is unclear.
```

## Learning flow

Local experience does not automatically become Academy doctrine.

The promotion path is:

```text
mission evidence
local memory note
learning proposal
local review
user approval
safe distilled rule
optional public Academy contribution
```

Private literature is evidence, not doctrine.

Only distilled, license-safe, user-approved principles may be promoted.

## Setup checklist

```text
[ ] Rename this folder to the local Village slug.
[ ] Copy README.template.md to README.md.
[ ] Copy AGENTS.local.template.md to AGENTS.local.md.
[ ] Copy village_manifest.template.md to village_manifest.md.
[ ] Copy local_context_pack.template.md to local_context_pack.md.
[ ] Copy private_boundary_checklist.md as-is or adapt locally.
[ ] Copy gitignore.template to .gitignore if using a nested local Git repo.
[ ] Confirm root .gitignore ignores this Village.
[ ] Run git check-ignore checks.
[ ] Add local context only after the boundary is verified.
```
