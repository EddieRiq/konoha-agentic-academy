# Release readiness scroll

## Status

Draft.

## Purpose

This Scroll defines a safe workflow for checking whether a repository, package, documentation set, Scroll, Clan, adapter, template, or public asset collection is ready for a public release.

The goal is not to make the release look complete. The goal is to decide whether it is safe, understandable, traceable, and honest enough to publish.

## Core rule

Release readiness is review, not promotion.

This Scroll may identify gaps, risks, blockers, and recommended changes. It may not publish, tag, push, merge, change versions, create releases, update doctrine, or declare a release ready unless those actions are explicitly allowed by an approved Mission Charter.

## When to use this Scroll

Use this Scroll when a mission involves:

- preparing a public repository release;
- checking whether a repo is safe to publish;
- reviewing documentation before announcement;
- validating that templates, Scrolls, adapters, or Clans are usable;
- checking license, attribution, or asset safety;
- preparing an initial `v0.x` release;
- preparing a GitHub release note;
- deciding whether a repo needs more work before being shared.

## Inputs required

Before starting, the Hokage or Local Kage must provide:

- repository path or target release path;
- intended audience;
- release type;
- expected scope;
- allowed paths;
- forbidden paths;
- current branch;
- whether Git operations are allowed;
- whether network access is allowed;
- whether local/private context may be inspected;
- required review level;
- approval owner.

If any of these are missing and they matter for the review, stop and ask.

## Release types

Classify the release as one of:

```text
internal-draft
public-draft
public-alpha
public-beta
stable
template-release
scroll-release
adapter-release
asset-release
documentation-release
```

The release type affects the standard of completeness.

A public draft can have known gaps.

A stable release must not depend on unstated assumptions.

## Default permissions

Unless the Mission Charter says otherwise, this Scroll allows only read-only actions.

Allowed by default:

- inspect file tree;
- read repository files;
- review README, docs, policies, templates, and metadata;
- run `git status`;
- run `git log --oneline`;
- run `git diff`;
- run `git remote -v`;
- list files;
- identify missing files;
- produce a release readiness report.

Not allowed by default:

- edit files;
- create files;
- delete files;
- stage files;
- commit;
- amend;
- tag;
- push;
- publish a release;
- upload packages;
- change repository visibility;
- modify licenses;
- modify doctrine;
- inspect private folders;
- copy local context into public docs.

## Minimum public repository checks

For a public repository, review:

```text
README.md
LICENSE
AGENTS.md
.gitignore
.gitattributes
docs/
core/
protocols/
scrolls/
templates/
```

Check whether:

- the project purpose is clear;
- the current maturity level is honest;
- the README links to the right documents;
- the license is present and consistent;
- contribution rules exist if contributions are expected;
- agent instructions exist if agents may use the repo;
- sensitive/private paths are ignored;
- line endings are controlled;
- local-only paths are not committed;
- generated files are not accidentally committed;
- the repo can be understood from the root.

## Safety checks

Search for signs of accidental exposure.

Look for:

```text
.env
.env.*
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
password
passwd
secret
token
apikey
api_key
client_secret
connection_string
jdbc:
odbc:
postgres://
mysql://
mongodb://
ssh-rsa
BEGIN PRIVATE KEY
```

Also check for:

- personal data;
- customer data;
- internal hostnames;
- internal emails where not intended;
- private project names;
- local absolute paths;
- screenshots with sensitive content;
- notebook outputs;
- logs;
- model artifacts;
- data extracts;
- copyrighted assets;
- franchise-specific images or sounds;
- private Allied Village context.

Do not reproduce sensitive values in the report. Report the file, line, category, and recommended action without copying secrets.

## Documentation checks

Review whether docs answer:

- what the project is;
- who it is for;
- what it does not do yet;
- how the repo is organized;
- how a new contributor should start;
- how an agent should start;
- what is safe by default;
- what requires approval;
- how local/private context is handled;
- how to report issues;
- how to propose changes.

Flag docs that are:

- inconsistent;
- too vague;
- too promotional;
- outdated;
- duplicated;
- contradicted by other docs;
- missing required safety notes;
- written as a changelog when they should describe current behavior.

## Doctrine consistency checks

For Konoha Agentic Academy, check consistency with:

```text
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
protocols/safety/safety_policy.md
protocols/context/context_policy.md
protocols/approval/approval_policy.md
protocols/review/review_policy.md
protocols/mission-charter/mission_charter.md
protocols/teachback/teachback_policy.md
protocols/learning/learning_policy.md
memory/yamanaka/yamanaka_memory_policy.md
```

No release is ready if a public document weakens the core laws.

Examples of blockers:

- a Scroll grants permissions not present in the Mission Charter;
- a tool claims it can approve actions;
- a UI claims it can complete missions;
- memory is treated as authorization;
- local context is treated as public by default;
- review is optional where risk requires it;
- agents are allowed to modify doctrine without approval.

## Template checks

For templates, check whether they include:

- purpose;
- status;
- scope;
- explicit approvals;
- allowed paths;
- forbidden paths;
- allowed commands;
- forbidden commands;
- evidence requirements;
- review level;
- teachback requirements;
- stop conditions;
- memory and learning handling;
- completion criteria.

Templates should guide action without granting authority.

## Scroll checks

For each Scroll, check:

- it declares its purpose;
- it declares default mode;
- it defines inputs;
- it defines allowed actions;
- it defines forbidden actions;
- it lists stop conditions;
- it explains evidence requirements;
- it references review;
- it does not override policy;
- it does not grant implicit permission;
- it can be used without private context.

## Adapter checks

For adapters, check:

- external systems are not trusted by default;
- capabilities are declared explicitly;
- local configuration is separated from public repo;
- secrets are not committed;
- failures are visible;
- adapter outputs are treated as evidence only when verified;
- the adapter cannot bypass approval, safety, or review.

## Asset checks

For public assets, verify:

- assets are original, generic, or license-safe;
- attribution exists when required;
- license compatibility is clear;
- no franchise-specific assets are committed;
- local overrides are ignored;
- text-only fallback exists where relevant;
- asset metadata does not expose private paths.

## Git checks

Run or request:

```bash
git status
git log --oneline -5
git remote -v
git diff --stat
git diff --check
```

If release involves publishing, also check:

```bash
git ls-files
git tag
```

Do not create tags or push unless explicitly authorized.

## Optional command checks

Only run these if allowed by the Mission Charter:

```bash
grep -RIn "TODO\|FIXME\|password\|secret\|token\|api_key\|client_secret" .
find . -maxdepth 3 -type f | sort
```

For larger repositories, prefer targeted searches to avoid reading private or generated folders.

## Risk levels

Assign one risk level.

```text
low
medium
high
blocked
```

Low means no obvious blockers and only minor polish remains.

Medium means release is possible, but known gaps should be documented.

High means release should wait until specific issues are fixed.

Blocked means publication would expose sensitive information, violate policy, create misleading expectations, or publish unsafe behavior.

## Release decision categories

Use one of:

```text
ready
ready-with-notes
not-ready
blocked
```

Definitions:

- `ready`: safe to release within the reviewed scope;
- `ready-with-notes`: safe, but with known limitations that must be stated;
- `not-ready`: fix listed issues before release;
- `blocked`: do not release until blockers are resolved and reviewed again.

## Report format

Use this structure:

```md
# Release readiness report

## Target

- Repository:
- Branch:
- Commit:
- Release type:
- Reviewed scope:
- Review date:

## Decision

- Status:
- Risk level:
- Required approval before release:

## Summary

Short summary of the review.

## Checks performed

- [ ] Git status
- [ ] README
- [ ] License
- [ ] Agent entrypoint
- [ ] Safety
- [ ] Sensitive data
- [ ] Documentation consistency
- [ ] Doctrine consistency
- [ ] Templates
- [ ] Scrolls
- [ ] Assets
- [ ] Local/private exclusions

## Blockers

List blockers, or write `None found`.

## Required fixes

List fixes required before release.

## Recommended improvements

List improvements that are useful but not blocking.

## Evidence

List commands, files, and observations. Do not copy sensitive values.

## Final recommendation

State whether to release, wait, or escalate.
```

## Stop conditions

Stop and ask if:

- repository visibility is unclear;
- target release type is unclear;
- sensitive data is found;
- secrets are suspected;
- local/private context appears in public files;
- license is missing or inconsistent;
- copyrighted assets are present;
- doctrine conflict is found;
- Git state is dirty and release requires clean state;
- release would require a tag, push, or external upload not explicitly approved;
- the review would require inspecting forbidden paths.

## Escalation

Escalate to Kage Summit if:

- release changes public behavior of the Academy;
- release creates or changes doctrine;
- release includes external contributions with unclear provenance;
- release includes adapters that touch external systems;
- release includes assets with licensing uncertainty;
- release would expose local Village patterns or private context;
- reviewers disagree on safety or readiness.

## Completion criteria

The Scroll is complete only when:

- reviewed scope is clear;
- checks performed are listed;
- blockers are documented;
- risk level is assigned;
- release decision category is assigned;
- evidence is provided;
- sensitive values are not reproduced;
- required review is identified;
- user receives a clear recommendation.

## Non-goals

This Scroll does not:

- publish releases;
- create tags;
- push code;
- change repository visibility;
- approve doctrine;
- rewrite documentation;
- sanitize secrets;
- replace security review;
- replace legal review for licensing.

## Final reminder

A release is not ready because the repo looks complete.

A release is ready when the reviewed scope is safe, understandable, traceable, and honest.
