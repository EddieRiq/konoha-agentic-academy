# Contribution guide

This guide defines how contributors may propose changes to Konoha Agentic Academy without weakening its safety, traceability, or doctrine.

## Core rule

Contributions must improve the Academy without bypassing its laws.

A contribution may add structure, examples, Scrolls, documentation, tests, schemas, tools, or safe assets. It may not silently change doctrine, expand agent permissions, weaken safety rules, or introduce private/local context into the public repository.

## Before contributing

A contributor should first identify the type of change:

- doctrine change;
- protocol change;
- Scroll change;
- Clan change;
- UI or telemetry change;
- asset change;
- documentation change;
- tool or adapter change;
- example or template change.

If the category is unclear, open a discussion before opening a pull request.

## What belongs in the public repository

The public repository may contain:

- Academy laws and conduct rules;
- general protocols;
- generic Scrolls;
- safe Clan templates;
- generic telemetry schemas;
- generic UI assets;
- documentation;
- examples without sensitive data;
- templates for local Villages.

The public repository must not contain:

- credentials;
- `.env` files;
- private project context;
- corporate or client data;
- personal data;
- raw emails;
- copyrighted character assets;
- private sound effects;
- local Village memory;
- user-specific style guides;
- local model outputs that include sensitive content.

## Doctrine changes

Doctrine includes Markdown files that define behavior, responsibilities, policies, or permissions.

Examples:

- `core/laws/KONOHA_LAWS.md`;
- `core/conduct/AGENT_CONDUCT.md`;
- `protocols/**`;
- role policies under `hokage/`, `kagebunshin/`, `jounin/`, and `shikamaru/`;
- memory, review, safety, approval, context, and learning policies.

Doctrine changes require:

1. a clear problem statement;
2. evidence or a concrete scenario;
3. the exact proposed change;
4. impact on related policies;
5. review by Shikamaru or an authorized maintainer;
6. human approval before merge.

No doctrine change should be accepted only because it sounds useful.

## Scroll contributions

A Scroll is a reusable workflow or skill.

A Scroll contribution must include:

- purpose;
- activation criteria;
- when not to use it;
- required inputs;
- expected outputs;
- stop-and-ask triggers;
- safety notes;
- examples;
- review or testing notes.

External Scrolls are untrusted by default. Imported Scrolls must include source, version, license, and review status.

A Scroll may guide execution, but it may not add permissions beyond the approved Mission Charter.

## Clan contributions

A Clan is a specialization area inside the Academy.

A new Clan should only be added when the specialization is broad, repeated, and distinct enough to need its own rules, Scrolls, reviewers, or examples.

A new Clan requires:

- reason for existence;
- scope;
- non-scope;
- related Scrolls;
- expected reviewers;
- risk level;
- examples of missions it supports.

Do not create a Clan for a one-off task.

## Local Village content

Local Village content stays local by default.

Contributors may add templates or examples for Allied Villages, but must not add real local project memory, private context, raw communications, or company-specific rules to the public repository.

If a local learning should become general, it must be converted into a sanitized Learning Proposal before it can be considered for Academy doctrine.

## Assets

Public assets must be original, generic, or license-safe.

Allowed:

- generic terminal layouts;
- generic shinobi-inspired ASCII art;
- original icons;
- original sounds;
- safe placeholders;
- neutral palettes.

Not allowed in the public repository:

- copyrighted character art;
- recognizable franchise designs;
- copied voice lines;
- music or sound effects from protected works;
- logos or protected brand marks.

Local Villages may override assets locally, but those assets must remain ignored by Git if they are private, user-provided, or franchise-inspired.

## Security and privacy

A contribution must not include secrets or private data.

If a contributor accidentally includes sensitive content:

1. stop;
2. remove it from the working tree;
3. notify maintainers;
4. rotate any exposed secret if needed;
5. do not quote the secret in issues, comments, logs, or pull requests.

Safety rules override contribution convenience.

## Pull request expectations

A pull request should include:

- what changed;
- why it changed;
- which files are affected;
- whether doctrine changed;
- whether safety, approval, context, memory, or review rules are affected;
- how it was reviewed or tested;
- whether any local/private content was involved;
- screenshots or examples if UI/assets changed.

Large pull requests should be split unless the changes are tightly coupled.

## Review expectations

Reviewers should check:

- scope control;
- consistency with Konoha Laws;
- safety and privacy;
- no hidden permission expansion;
- no local/private leakage;
- clarity of language;
- whether the change belongs in doctrine, protocol, Scroll, Clan, tool, UI, or documentation;
- whether examples are safe and reproducible.

A review may return:

- approved;
- approved with notes;
- changes requested;
- blocked;
- escalate to Kage Summit.

## Agent-generated contributions

Agent-generated contributions are allowed, but they must be disclosed.

A contribution generated or edited by an agent must state:

- agent or tool used;
- human reviewer;
- whether the full diff was reviewed;
- whether any local context was used;
- whether outputs were checked for fabricated claims.

Agents may propose improvements, but they may not merge, promote doctrine, or declare their own work accepted.

## Completion checklist

Before a contribution is merged:

- no secrets are present;
- no private local context is present;
- no unsafe assets are present;
- doctrine changes were explicitly reviewed;
- Scrolls have activation and stop conditions;
- examples are safe;
- related policies are still consistent;
- the contribution has a clear reason to exist.
