# Changelog Maintenance Scroll

## Purpose

This Scroll defines how agents help maintain a project changelog.

It is used when a mission requires drafting, reviewing, updating, or preparing changelog entries for public or local repositories.

A changelog records approved changes. It does not approve changes.

## Core rule

Changelog maintenance documents what changed.

It may not approve releases, authorize publication, hide risk, modify doctrine without approval, invent changes, or replace release readiness review.

## Authority

This Scroll is subordinate to:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/safety/safety_policy.md`
4. `protocols/context/context_policy.md`
5. `protocols/approval/approval_policy.md`
6. `protocols/review/review_policy.md`
7. `protocols/mission-charter/mission_charter.md`
8. `protocols/teachback/teachback_policy.md`
9. `scrolls/publication_safety_scroll.md`
10. `scrolls/release_readiness_scroll.md`
11. `scrolls/release_notes_scroll.md`

If there is a conflict, the higher authority wins.

## Default mode

Changelog maintenance is read-only by default.

The agent may inspect repository history, existing changelog files, release notes, tags, commits, merge requests, issues, or mission reports only if the Mission Charter allows those sources.

The agent may not edit `CHANGELOG.md` or any release file unless the Mission Charter explicitly allows file modification.

## When to use this Scroll

Use this Scroll when the user asks to:

- create a changelog;
- update an existing changelog;
- summarize commits into changelog entries;
- prepare entries for a release;
- convert mission reports into changelog text;
- verify that release notes and changelog entries are consistent;
- classify changes into added, changed, fixed, deprecated, removed, security, or documentation sections.

## What this Scroll is not for

This Scroll is not for:

- approving a release;
- deciding project versioning alone;
- editing doctrine without approval;
- hiding breaking changes;
- summarizing sensitive local context into a public changelog;
- replacing release notes;
- replacing a Mission Report;
- replacing review.

## Required inputs

Before drafting or updating a changelog, the agent must know:

- repository or project name;
- target version or date range;
- source of truth for changes;
- whether the changelog is public or local;
- expected changelog format;
- allowed files to read;
- allowed files to edit, if any;
- whether unreleased changes should be included;
- whether sensitive or private changes must be excluded.

If these are missing, the agent must ask before drafting final text.

## Accepted sources of truth

The agent may use only explicit sources allowed by the Mission Charter, such as:

- existing `CHANGELOG.md`;
- Git commit history;
- Git tags;
- release notes;
- merge request descriptions;
- issue tracker summaries;
- Mission Reports;
- approved Kage Summit Verdicts;
- approved Learning Proposals;
- user-provided notes.

The agent must not infer changes from memory alone.

## Recommended changelog format

Use a simple format compatible with Keep a Changelog style.

```markdown
# Changelog

## [Unreleased]

### Added

### Changed

### Fixed

### Deprecated

### Removed

### Security

### Documentation
```

Use only the sections that have content.

Do not keep empty sections unless the project convention requires them.

## Entry style

Changelog entries should be:

- factual;
- short;
- specific;
- written from the user's point of view when possible;
- free of internal implementation noise unless relevant;
- free of hype;
- traceable to evidence.

Good:

```markdown
- Added `AGENTS.md` with entrypoint instructions for repository agents.
- Added Mission Charter and Mission Report templates.
- Normalized line endings with `.gitattributes`.
```

Bad:

```markdown
- Implemented a robust and comprehensive documentation ecosystem.
- Improved the whole project significantly.
- Added many important files.
```

## Sensitive content rules

Public changelog entries must not include:

- credentials;
- tokens;
- private URLs;
- internal hostnames;
- personal data;
- customer data;
- operation IDs;
- private project names unless approved;
- local Village memory;
- private file paths;
- copyrighted or franchise-specific asset references;
- unpublished business context.

If a sensitive change must be mentioned, generalize it:

```markdown
- Updated local context handling rules.
```

Do not write:

```markdown
- Added rules for `/home/user/private-client-project/secret-context.md`.
```

## Versioning

The agent may propose version labels, but may not decide them unless explicitly authorized.

Acceptable proposals:

```text
0.1.0 for first public doctrine baseline.
0.1.1 for documentation-only fixes.
0.2.0 for first operational Scroll set.
```

The agent must mark this as a proposal.

## Workflow

### 1. Confirm scope

Identify:

- target version or date range;
- public or local changelog;
- allowed sources;
- allowed edit mode;
- required review level.

### 2. Inspect existing changelog

If a changelog exists, preserve its style unless the Mission Charter authorizes migration.

Check:

- heading structure;
- version format;
- dates;
- section names;
- links;
- unreleased section;
- previous conventions.

### 3. Gather evidence

Use approved sources only.

For Git-based summaries, inspect:

```bash
git status
git log --oneline --decorate
git tag
git diff
```

Only run commands explicitly allowed by the Mission Charter.

### 4. Classify changes

Group changes into useful categories:

- Added;
- Changed;
- Fixed;
- Deprecated;
- Removed;
- Security;
- Documentation.

Avoid dumping commit messages directly if they are too noisy.

### 5. Draft entries

Each entry should describe the user-visible or maintainer-visible change.

Do not invent impact.

Do not claim something is ready, stable, released, secure, or production-grade unless evidence supports it.

### 6. Safety review

Before finalizing, check for:

- sensitive content;
- private paths;
- internal names;
- credentials;
- unsupported claims;
- release approval language;
- doctrine changes not approved;
- entries that summarize unmerged or unapproved work as completed.

### 7. Produce output

Depending on the Mission Charter, provide either:

- a draft changelog section;
- a patch proposal;
- an updated file;
- a review report;
- a list of questions before proceeding.

### 8. Request review

Changelog changes for public repositories require review before publication.

If the changelog mentions security, doctrine, sensitive workflows, permissions, dependencies, or external integrations, request Jounin review.

## Editing rules

When editing is explicitly allowed:

- keep changes minimal;
- preserve existing format;
- avoid rewriting old entries unless requested;
- do not change version history silently;
- do not delete entries without explanation;
- show diff before commit;
- do not commit unless the Mission Charter allows it.

## Stop conditions

Stop and ask if:

- the target version is unclear;
- sources conflict;
- Git history does not match user-provided notes;
- a change may expose sensitive information;
- a requested entry claims unsupported impact;
- the user asks to hide a relevant breaking change or security issue;
- the changelog requires doctrine interpretation;
- the changelog would imply release approval;
- the Mission Charter does not allow editing.

## Changelog review checklist

Before final output, verify:

- entries match evidence;
- no sensitive content is exposed;
- no private context leaked into public docs;
- no unsupported claims;
- no release approval implied;
- section names are consistent;
- dates and versions are correct or marked as proposed;
- breaking changes are visible;
- security changes are handled carefully;
- documentation-only changes are not overstated.

## Output format

A changelog maintenance report should include:

```markdown
# Changelog Maintenance Report

## Mission

## Sources reviewed

## Target version or date range

## Proposed changelog entries

## Sensitive content check

## Risks or uncertainties

## Review required

## Next action
```

## Violations

The following are violations:

- inventing changelog entries;
- converting private memory into public changelog content;
- hiding breaking changes;
- hiding security-relevant changes;
- changing version history without approval;
- editing changelog without an approved Mission Charter;
- using changelog maintenance to approve a release;
- declaring release readiness without release readiness review.

## Closing rule

If the agent cannot prove a changelog entry from approved evidence, it must not write it as fact.
