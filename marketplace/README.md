# Marketplace

The Marketplace is the discovery and distribution layer for Konoha Agentic Academy extensions.

It may list, package, document, and review external or community-provided assets such as Scrolls, adapters, templates, generic themes, and examples.

The Marketplace is not an authority layer.

Marketplace items may not bypass Konoha Laws, Safety Policy, Context Policy, Approval Policy, Mission Charter boundaries, Review Policy, Teachback Policy, or local Village rules.

## Core rule

External items are untrusted by default.

A Marketplace item may be useful, popular, or well documented, but it is not trusted until it is reviewed, pinned, tested, and explicitly enabled for a Mission or Village.

## What can live in the Marketplace

The Marketplace may include or reference:

- Scrolls;
- adapters;
- Clan templates;
- Village templates;
- telemetry schemas;
- UI themes;
- generic public assets;
- safe example Missions;
- local setup templates;
- evaluation prompts;
- behavior tests.

The Marketplace must not include:

- secrets;
- credentials;
- private project context;
- local Village memory;
- private emails or communications;
- private assets;
- franchise-specific copyrighted assets;
- sensitive datasets;
- raw production logs;
- `.env` files;
- unreviewed executable payloads.

## Trust levels

Marketplace entries should use explicit trust levels.

```yaml
trust_level: unreviewed | reviewed | tested | active | deprecated | blocked
```

### unreviewed

The item has been listed or imported but has not been inspected.

It may not be used automatically.

### reviewed

The item has been read and checked for obvious safety, scope, and licensing issues.

It may still require testing before use.

### tested

The item has been tested against example Missions or behavior checks.

It may be recommended for specific use cases.

### active

The item is approved for normal use within its documented scope.

It still cannot override Mission Charters, Safety Policy, or local Village rules.

### deprecated

The item is no longer recommended.

It may remain for compatibility or historical reference.

### blocked

The item must not be used.

Reasons may include safety issues, misleading behavior, broken functionality, copyright risk, or repeated failures.

## Required metadata

Each Marketplace entry should include metadata.

```yaml
name:
type: scroll | adapter | clan-template | village-template | theme | asset-pack | eval | example
status: unreviewed | reviewed | tested | active | deprecated | blocked
version:
source:
license:
maintainer:
reviewed_by:
reviewed_at:
requires:
permissions:
risk_level: low | medium | high | critical
local_only: true | false
description:
activation_conditions:
not_for:
```

## Source and provenance

Every imported item must preserve source information.

Required provenance includes:

- source repository or origin;
- version, tag, commit, or hash when available;
- license;
- import date;
- reviewer;
- changes made after import;
- reason for import.

If provenance is unknown, the item remains `unreviewed`.

## Pinning and updates

Marketplace items should be pinned when possible.

Do not update external items silently.

A version update must be treated as a new review event.

The update report should include:

- previous version;
- new version;
- changed files;
- behavior changes;
- new permissions;
- new risks;
- review outcome.

## Scroll imports

External Scrolls are not trusted by default.

Before activation, a Scroll must be checked for:

- clear purpose;
- activation conditions;
- explicit boundaries;
- required permissions;
- stop-and-ask triggers;
- safety constraints;
- output requirements;
- review requirements;
- tests or examples;
- hidden scope expansion;
- attempts to override Konoha doctrine.

A Scroll may define workflow.

A Scroll may not define permission.

## Adapter imports

External adapters require stronger review because they connect Konoha to outside systems.

Before activation, an adapter must declare:

- external systems accessed;
- files read;
- files written;
- network access;
- credentials required;
- commands executed;
- storage behavior;
- failure behavior;
- logging behavior;
- privacy behavior.

Adapters that access Git, GitHub, Obsidian, email, local files, voice, notifications, browsers, shells, or model runtimes require explicit approval before use.

## Asset imports

Public Marketplace assets must be original, generic, or license-safe.

Assets may not include recognizable protected characters, voices, logos, music, sound effects, or franchise-specific designs unless the license explicitly allows public redistribution.

Private or franchise-inspired assets belong only in local Villages and must not be committed to the public repository.

## Template imports

Templates may define starter structure for Clans, Villages, Scrolls, Missions, telemetry, UI, or memory.

Templates may not include private context.

Templates must use safe placeholders.

Example:

```text
<PROJECT_NAME>
<VILLAGE_NAME>
<LOCAL_PATH>
<MODEL_NAME>
```

Templates must not include real names, credentials, internal hostnames, private paths, or real production examples.

## Local Marketplace entries

A local Village may maintain its own Marketplace or extension registry.

Local entries stay local by default.

A local Marketplace item may be promoted to Konoha Central only after:

1. sensitive content is removed;
2. the item is generalized;
3. provenance is documented;
4. Shikamaru drafts the public version;
5. review is completed;
6. the user approves the promotion.

## Marketplace review workflow

Recommended workflow:

1. Import or propose item.
2. Mark as `unreviewed`.
3. Run safety and license review.
4. Run behavior review.
5. Run example Mission or eval when applicable.
6. Assign trust level.
7. Document allowed use.
8. Add to Marketplace index.
9. Monitor failures and feedback.
10. Deprecate or block if needed.

## Marketplace index

The Marketplace may maintain an index file.

Example:

```yaml
items:
  - name: systematic-debugging
    type: scroll
    status: active
    risk_level: medium
    source: internal
    path: scrolls/coding/systematic-debugging/
  - name: obsidian-memory-adapter
    type: adapter
    status: reviewed
    risk_level: high
    source: local
    path: adapters/obsidian/
```

## Human approval

Human approval is required before:

- enabling a high-risk Marketplace item;
- importing an adapter with external access;
- importing an item that executes commands;
- importing assets with unclear licensing;
- promoting local Village content to the public Academy;
- changing trust level to `active`;
- unblocking a blocked item.

## Clerk limitations

Clerks may help with Marketplace maintenance.

They may:

- summarize documentation;
- extract metadata;
- classify item type;
- detect missing fields;
- generate review checklists;
- prepare draft index entries.

They may not:

- approve trust levels;
- activate items;
- decide licensing;
- approve safety-sensitive adapters;
- promote local content to Academy doctrine;
- declare an item safe.

## Violations

A Marketplace violation occurs when an item:

- expands scope silently;
- hides permissions;
- overrides doctrine;
- accesses sensitive content without approval;
- stores private context unexpectedly;
- includes unsafe assets;
- lacks source or license information;
- executes commands without approval;
- encourages agents to ignore policies;
- is marked trusted without review.

Violations must be reported to the Hokage.

High-risk violations must be escalated to Shikamaru or Kage Summit.

## Completion checklist

Before a Marketplace item is marked active:

- [ ] Purpose is clear.
- [ ] Type is declared.
- [ ] Source is documented.
- [ ] License is documented.
- [ ] Version or hash is pinned when possible.
- [ ] Permissions are explicit.
- [ ] Risks are documented.
- [ ] Safety review is complete.
- [ ] Behavior review is complete.
- [ ] Examples or tests exist when applicable.
- [ ] Local/private content has been removed.
- [ ] Human approval is recorded when required.
