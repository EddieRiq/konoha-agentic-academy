# Local Context Scroll

## Status

Draft.

## Purpose

This Scroll defines how an agent may work with local, private, or project-specific context without leaking it into the public Academy repository.

Use this Scroll when a mission involves:

- an Allied Village;
- local project files;
- private notes;
- Obsidian vaults;
- local memory;
- customer, company, or internal project context;
- machine-specific paths;
- ignored folders;
- context copied from another private repository.

## Core rule

Local context stays local by default.

No agent may read, copy, summarize, store, transmit, commit, or use local context unless the Mission Charter explicitly allows it.

## Authority

This Scroll does not grant permission by itself.

It must follow:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/safety/safety_policy.md`
4. `protocols/context/context_policy.md`
5. `protocols/approval/approval_policy.md`
6. `protocols/mission-charter/mission_charter.md`
7. `memory/yamanaka/yamanaka_memory_policy.md`
8. Local Village rules, when present

If any rule conflicts, the stricter rule wins.

## Default mode

Local context missions are read-restricted by default.

An agent may discuss expected structure, ask what context exists, and propose a context pack.

An agent may not inspect local folders, private files, ignored paths, or Obsidian vaults without explicit approval.

## Required Mission Charter fields

Before using local context, the Mission Charter must specify:

- context source;
- allowed paths;
- forbidden paths;
- allowed files or file patterns;
- whether summaries may be created;
- whether local memory may be updated;
- whether any content may be copied into the public repo;
- whether private context may be quoted;
- retention rules;
- review level;
- stop conditions.

If any field is missing, the agent must stop and ask.

## Context sources

Allowed context sources may include:

- files explicitly attached by the user;
- specific local paths approved in the Mission Charter;
- specific Obsidian notes approved in the Mission Charter;
- local Village memory notes;
- local project README files;
- sanitized excerpts pasted by the user;
- generated context packs approved for the mission.

Unapproved context sources are forbidden.

## Forbidden by default

The following are forbidden unless explicitly approved:

- `.env` files;
- credentials;
- tokens;
- private keys;
- SSH keys;
- database connection strings;
- customer data;
- personal data;
- raw production datasets;
- internal emails;
- contracts;
- payroll data;
- confidential business documents;
- ignored local folders;
- entire Obsidian vaults;
- entire home directories;
- browser profiles;
- chat exports;
- screenshots with private information;
- franchise-specific or copyrighted assets.

If sensitive content appears accidentally, the agent must stop and report the exposure without repeating the sensitive value.

## Context minimization

The agent must request the smallest useful context.

Prefer:

- file names instead of full files;
- schemas instead of raw data;
- anonymized samples instead of production records;
- aggregated outputs instead of row-level data;
- summaries with links instead of large copied blocks;
- hashes or checksums instead of file contents;
- selected excerpts instead of whole documents.

The agent must not ask for private data when a synthetic or anonymized example is enough.

## Context packs

A context pack is a bounded bundle of mission-specific information.

A context pack should include:

- mission ID;
- source list;
- scope;
- assumptions;
- key facts;
- relevant paths;
- excluded paths;
- freshness date;
- sensitivity level;
- owner;
- allowed use;
- expiration or review date.

A context pack is not permanent truth.

A context pack supports the mission, but it does not authorize actions.

## Local Village context

Allied Villages may maintain private context under ignored paths.

Public Academy agents must treat Village context as private unless the Mission Charter says otherwise.

Local Village context may include:

- project rules;
- local memory;
- private assets;
- machine-specific setup;
- local models;
- local workers;
- internal documentation;
- project-specific Scrolls.

No Local Village context may be promoted to the public Academy without human approval and sanitization.

## Public repo boundary

The public Academy repository must not receive:

- private project facts;
- company-specific details;
- customer information;
- private machine paths, unless genericized;
- local credentials;
- internal hostnames;
- proprietary data structures;
- private assets;
- copyrighted or franchise-specific materials;
- local memory notes not approved for publication.

When publishing a lesson from local context, convert it into a generic pattern.

## Safe transformation

Private context may be transformed into public guidance only when all conditions are met:

1. The Mission Charter allows the transformation.
2. Sensitive details are removed.
3. The lesson is general enough for public use.
4. The source owner approves publication.
5. Shikamaru drafts the doctrine or proposal.
6. Required review is completed.

Example:

```text
Unsafe:
Project X stores rejected loan records in path C:\Company\Risk\Clients\...

Safe:
When a mission uses a business-defined universe, preserve the universe as the base table and join other sources into it.
```

## Working with Obsidian

Obsidian is an interface for local memory, not a permission system.

An agent may not scan an entire vault by default.

Allowed access must be note-specific, folder-specific, or context-pack-specific.

When creating or updating memory notes, use Markdown and YAML frontmatter compatible with Obsidian.

Do not store sensitive raw content in memory unless the Mission Charter explicitly allows it.

## Working with local models and Clerks

Local Clerks may help summarize, tag, cluster, or compress local context.

They may not decide what is safe to publish.

They may not authorize a mission.

They may not access broader local context than the Mission Charter allows.

Their outputs must be treated as summaries, not truth.

## Machine-specific paths

Machine-specific paths may be used for execution, but public docs should avoid hardcoding them.

Prefer placeholders:

```text
<local_project_root>
<local_village_root>
<obsidian_vault>
<downloads_folder>
```

When helping a user copy files locally, commands may include the user's approved path if the action is local and not intended for public documentation.

## Evidence standard

When reporting from local context, the agent must distinguish:

- observed evidence;
- user-provided statements;
- derived conclusions;
- assumptions;
- missing context.

Do not write as if a summary is a source of truth.

## Stop conditions

The agent must stop when:

- the requested context is not explicitly approved;
- a file appears sensitive;
- a path is outside allowed scope;
- a local folder is ignored by Git and not approved;
- the mission requires reading secrets;
- the user asks to publish private content;
- the agent cannot separate public and private content;
- the context is stale or contradictory;
- the mission would require broad scanning of local files;
- the output would expose private details.

## Review

Local context missions require review when they involve:

- public publication;
- doctrine changes;
- learning promotion;
- private memory updates;
- local Village context;
- sensitive data;
- machine inspection;
- generated summaries used for future missions.

Use Jounin review or Kage Summit review based on risk.

## Mission report requirements

The final report must include:

- context sources used;
- context sources not used;
- sensitive content encountered, described without repeating secrets;
- whether local memory was updated;
- whether any public docs were changed;
- evidence links or local references;
- assumptions;
- unresolved questions;
- review status;
- teachback notes.

## Violations

Violations include:

- reading unapproved local files;
- copying private content into public docs;
- committing local memory accidentally;
- quoting sensitive content unnecessarily;
- treating summaries as truth;
- using context from one Village in another Village without approval;
- scanning a broad folder when only one file was approved;
- hiding uncertainty about context quality.

Violations must be reported and escalated according to the Safety Policy.

## Checklist before using local context

Before using local context, confirm:

- Mission Charter is approved.
- Allowed paths are explicit.
- Forbidden paths are explicit.
- Sensitive content handling is defined.
- Memory update permissions are defined.
- Public publication rules are defined.
- Review level is defined.
- Stop conditions are clear.

## Checklist before publishing anything derived from local context

Before publishing, confirm:

- no secrets are included;
- no personal data is included;
- no company-specific confidential detail is included;
- no private path is included unnecessarily;
- no copyrighted or franchise-specific asset is included;
- examples are generic or synthetic;
- local owner approval exists;
- required review is complete.

## Closing rule

When context is private, unclear, or broader than needed, stop.

Ask for the smallest useful context.

Wait for explicit approval.
