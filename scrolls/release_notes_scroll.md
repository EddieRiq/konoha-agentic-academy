# Release notes Scroll

## Status

Draft Scroll.

## Purpose

This Scroll guides the creation or review of release notes for Konoha Agentic Academy.

Release notes explain what changed, why it matters, and what users or contributors should check before using the new version. They must be clear, traceable, and safe to publish.

## Core rule

Release notes describe approved changes.

They do not approve releases, modify doctrine, publish artifacts, hide risk, or replace release readiness review.

## When to use this Scroll

Use this Scroll when a mission asks an agent to:

- draft release notes;
- review existing release notes;
- summarize changes since the previous tag or commit;
- prepare a changelog entry;
- explain compatibility or migration notes;
- collect known issues for a public release;
- turn merged work into a human-readable release summary.

## When not to use this Scroll

Do not use this Scroll to:

- decide that a release is ready;
- tag a release;
- push to a remote repository;
- publish a package;
- modify code;
- modify doctrine;
- inspect private or local Village context unless explicitly allowed;
- invent impact, adoption, stability, or compatibility claims.

Release approval belongs to the Mission Charter, release readiness review, required reviewers, and the human maintainer.

## Required inputs

Before drafting release notes, the agent must identify:

- release name or version;
- release date or planned date;
- commit range, tag range, or merged work to summarize;
- target audience;
- files or changes in scope;
- known limitations;
- review status;
- publication target.

If these inputs are missing, the agent must ask before drafting final release notes.

## Allowed actions by default

Unless the Mission Charter says otherwise, this Scroll only allows read-only actions:

- read repository documentation;
- read `git log`, `git diff`, and release-related files;
- summarize committed changes;
- group changes by category;
- draft release notes in the response;
- propose a release notes file path;
- identify missing evidence;
- flag unclear or risky claims.

## Actions that require explicit approval

The following actions require explicit approval in the Mission Charter:

- creating or editing release note files;
- creating or editing `CHANGELOG.md`;
- creating tags;
- pushing tags;
- publishing GitHub releases;
- publishing packages;
- changing version numbers;
- amending commits;
- modifying release workflows;
- marking a release as final;
- storing release notes in memory.

## Forbidden actions

The agent must not:

- fabricate a change that is not supported by evidence;
- claim that a release is stable without validation evidence;
- claim security fixes without confirmed details;
- expose sensitive paths, secrets, private context, internal customer data, local Village details, or private artifacts;
- copy private release notes from local Villages into the public Academy without approval;
- include copyrighted or franchise-specific assets;
- hide breaking changes;
- hide known risks;
- convert planned work into completed work.

## Release notes structure

Use this structure unless the Mission Charter specifies another format:

```markdown
# Release notes: <version or date>

## Summary

Short summary of the release.

## Added

New features, documents, Scrolls, templates, adapters, tools, or assets.

## Changed

Changes to existing behavior, wording, structure, docs, templates, policies, or workflows.

## Fixed

Corrections to errors, broken links, inconsistent docs, or behavior.

## Removed

Deleted files, deprecated paths, removed behavior, or removed examples.

## Security and privacy

Relevant safety changes, secret-handling changes, publication checks, or privacy notes.

Do not include sensitive values.

## Compatibility

Required migrations, changed paths, renamed files, or expected user action.

## Known issues

Known limitations, incomplete areas, or pending review items.

## Evidence

Commit range, tags, PRs, issue IDs, or file paths used to prepare the notes.
```

If a section has no content, omit it or write `None known` only when this has been checked.

## Evidence requirements

Release notes must be based on evidence, such as:

- `git log --oneline`;
- `git diff`;
- merge commits;
- pull requests;
- reviewed Mission Reports;
- approved Mission Charters;
- release readiness reports;
- file paths changed in the release;
- issue tracker entries.

The agent must distinguish between:

- completed changes;
- planned changes;
- proposed changes;
- known issues;
- inferred impact.

Inferred impact must be clearly marked as inference.

## Wording rules

Use plain language.

Prefer:

```text
Added mission templates for Mission Charters and Mission Reports.
```

Avoid:

```text
This release marks a major milestone in the evolution of agentic workflows.
```

Prefer:

```text
Known issue: adapters are documented but not implemented yet.
```

Avoid:

```text
The adapter layer is production-ready.
```

Do not overstate maturity. If the project is still doctrine-first, say so.

## Public release safety

Before finalizing release notes for a public repository, check that the notes do not contain:

- secrets;
- credentials;
- tokens;
- real customer or employee data;
- private paths;
- internal hostnames;
- local Village names unless approved for public mention;
- proprietary business details;
- copyrighted assets;
- private model details;
- unsupported claims about security, stability, or performance.

If sensitive content is found, stop and report the category without repeating the sensitive value.

## Handling breaking changes

A breaking change is any change that may affect users, contributors, agents, local Villages, templates, paths, commands, or expected behavior.

Breaking changes must be called out clearly:

```markdown
## Breaking changes

- Renamed `<old path>` to `<new path>`.
- Existing local references must be updated manually.
```

Do not hide breaking changes inside a generic "Changed" section when the release is public or shared.

## Versioning notes

This Scroll does not define the repository versioning policy.

If versioning is not defined, the agent may ask whether the release should use:

- date-based versioning;
- semantic versioning;
- milestone names;
- commit-only release notes.

The agent must not create a versioning policy alone.

## Agent report

A release notes mission should end with:

```markdown
# Release notes report

## Scope reviewed

What range, files, PRs, tags, or commits were reviewed.

## Draft location

Where the draft was written, or whether it was only provided in the response.

## Evidence used

Commands, commits, files, or reports used.

## Risks

Unverified claims, missing review, unclear compatibility, or missing release readiness.

## Suggested next step

Review, edit, approve, publish, or run release readiness.

## Completion status

Draft only, reviewed, blocked, or ready for human approval.
```

## Stop conditions

Stop and ask if:

- there is no commit range or change source;
- the release target is unclear;
- the Mission Charter does not allow file edits but a file edit is requested;
- sensitive content appears in the change history;
- release notes would require private context;
- breaking changes are suspected but not confirmed;
- the user asks to publish without release readiness;
- evidence conflicts with the requested summary.

## Relationship with other Scrolls

Use this Scroll with:

- `release_readiness_scroll.md` before public release approval;
- `publication_safety_scroll.md` before publishing externally;
- `sensitive_data_review_scroll.md` when release notes mention paths, data, logs, or examples;
- `git_safety_scroll.md` when tags, commits, or push operations are involved;
- `documentation_review_scroll.md` when release notes are part of repository docs;
- `learning_capture_scroll.md` after release issues produce lessons.

## Violations

A violation occurs if an agent:

- publishes release notes without approval;
- edits release files outside the Mission Charter;
- fabricates completed work;
- omits known breaking changes;
- exposes sensitive content;
- claims validation without evidence;
- converts a draft into an official release without human approval.

Violations must be reported to the Hokage or Local Kage and may require Jounin review.

## Checklist

Before closing a release notes mission, confirm:

- the scope is explicit;
- the change source is identified;
- the notes are evidence-based;
- completed work is separated from planned work;
- known issues are not hidden;
- sensitive content is not exposed;
- breaking changes are clear;
- the release is not marked approved unless approval exists;
- the user receives the next safe action.
