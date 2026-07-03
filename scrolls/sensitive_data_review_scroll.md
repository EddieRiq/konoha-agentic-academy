# Sensitive data review scroll

## Status

Draft.

## Purpose

This Scroll defines a safe, read-only workflow for reviewing repository content before it is committed, pushed, published, shared, copied into public documentation, or promoted from a Local Village into the public Academy.

It helps detect accidental exposure of:

- secrets;
- credentials;
- private paths;
- personal data;
- internal business context;
- copyrighted or franchise-specific assets;
- confidential project notes;
- local Village memory;
- machine-specific configuration;
- generated outputs that should not be public.

## Core rule

Sensitive data review is read-only by default.

No agent may delete, rewrite, move, redact, commit, push, publish, or archive content unless those actions are explicitly allowed by an approved Mission Charter.

## Authority

This Scroll does not grant permission.

It is subordinate to:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/safety/safety_policy.md`
4. `protocols/context/context_policy.md`
5. `protocols/approval/approval_policy.md`
6. `protocols/review/review_policy.md`
7. `protocols/mission-charter/mission_charter.md`
8. `protocols/teachback/teachback_policy.md`
9. Local Village rules, when reviewing local or private repositories

If this Scroll conflicts with higher authority, the higher authority wins.

## When to use this Scroll

Use this Scroll before:

- first public push;
- release preparation;
- pull request or merge request;
- publishing documentation;
- importing local Village material into the public Academy;
- committing generated files;
- sharing examples, prompts, logs, screenshots, reports, or templates;
- uploading assets;
- accepting external Scrolls, adapters, tools, or templates;
- adding sample configuration;
- creating public issues or discussions from private work.

## Mission modes

### Conversation mode

Allowed by default.

The agent may explain what should be checked, list common risks, and suggest safe commands.

### Planning mode

Requires Mission Charter approval.

The agent may define the review scope, paths, file types, commands, risk level, and required review level.

### Review mode

Requires Mission Charter approval.

The agent may inspect explicitly allowed files and produce a findings report.

### Remediation mode

Requires explicit human approval.

The agent may propose exact redactions or file changes, but may not apply them unless the Mission Charter allows edits.

### Publication mode

Requires explicit human approval.

The agent may recommend whether content is safe to publish, but the human decides.

## Default allowed actions

Unless restricted by the Mission Charter, a reviewer may:

- read explicitly allowed files;
- list filenames in allowed paths;
- run read-only searches in allowed paths;
- inspect `git status`;
- inspect `git diff`;
- inspect `git log` metadata;
- inspect `.gitignore`;
- inspect `.gitattributes`;
- inspect repository settings documented in files;
- report possible sensitive content;
- propose remediation steps;
- recommend review level.

## Default forbidden actions

A reviewer may not:

- read files outside allowed paths;
- inspect private folders unless explicitly allowed;
- inspect local machine files outside the repository;
- open `.env`, credential stores, SSH keys, browser profiles, password managers, or token files unless explicitly allowed for a controlled secret-handling mission;
- print secrets into reports;
- copy secrets into memory;
- summarize secrets in a reusable way;
- commit or push changes;
- delete or rewrite files;
- upload files externally;
- publish findings that include sensitive values;
- treat absence of findings as proof of safety.

## Sensitive content categories

### Secrets and credentials

Look for:

- passwords;
- API keys;
- tokens;
- private keys;
- SSH keys;
- database credentials;
- full connection strings;
- service account files;
- cloud credentials;
- authentication cookies;
- session tokens;
- `.env` files;
- `.npmrc`, `.pypirc`, `.netrc`, or similar files containing secrets.

Do not reproduce secret values in the report.

Report only the file path, line number if allowed, type of issue, and recommended action.

Example:

```text
Potential secret found in config/example.env: DB password-like value.
Recommended action: replace with placeholder and rotate if this value was real.
```

### Personal data

Look for:

- names;
- personal IDs;
- phone numbers;
- email addresses;
- home addresses;
- customer IDs;
- account numbers;
- loan or operation numbers;
- free-text notes about people;
- screenshots showing identifiable users;
- filenames containing personal identifiers.

Do not reproduce personal data in the report.

Use placeholders.

### Internal business context

Look for:

- non-public company names;
- internal project names;
- internal model names when not meant for public release;
- private architecture diagrams;
- internal server paths;
- internal database names;
- internal IPs;
- Jira issue details;
- non-public strategy, risk, pricing, portfolio, customer, or policy details.

### Local Village context

Look for:

- `alliance/<village>/` content;
- local memory files;
- local context packs;
- Obsidian vault notes;
- local Mission Charters;
- local learning proposals;
- local agent reports;
- machine-specific setup notes;
- private project instructions.

Local context stays local by default.

### Assets and copyright

Look for:

- franchise-specific images, icons, music, voices, character art, screenshots, logos, fonts, or names used as assets;
- downloaded images without license metadata;
- generated assets based on copyrighted characters;
- third-party templates without license;
- font files;
- copied documentation from proprietary sources.

Public assets must be original, generic, or license-safe.

### Generated outputs

Look for:

- model outputs containing real records;
- logs with credentials or private paths;
- notebook outputs;
- debug files;
- temporary extracts;
- screenshots;
- cache folders;
- large data files;
- reports with identifiable rows;
- evaluation artifacts based on private data.

## Recommended checks

The Mission Charter must define which checks are allowed.

Typical read-only commands:

```bash
git status
git diff --cached
git diff
git log --oneline -5
find . -maxdepth 3 -type f | sort
```

Possible pattern searches, only inside approved paths:

```bash
grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv "password\|passwd\|secret\|token\|api_key\|apikey\|private_key\|BEGIN RSA\|BEGIN OPENSSH" .
grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv "@.*\." .
grep -RIn --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv "C:\\\|/home/\|/mnt/c/\|\\\\server\\" .
```

The reviewer must not run broad searches if the repository contains private data outside the approved scope.

## Review workflow

### 1. Confirm scope

Identify:

- repository name;
- branch;
- public or private target;
- paths to inspect;
- paths explicitly excluded;
- allowed commands;
- whether line-level reporting is allowed;
- whether suspected sensitive values may be shown or must be masked;
- required review level.

### 2. Inspect repository boundaries

Check:

- `.gitignore`;
- `.gitattributes`;
- ignored local folders;
- private Village paths;
- generated outputs;
- asset folders;
- templates;
- documentation paths;
- examples and sample configs.

### 3. Inspect staged and unstaged changes

Check:

```bash
git status
git diff
git diff --cached
```

Focus first on what is about to be published.

### 4. Search approved paths

Use only approved read-only search commands.

Do not search private or excluded paths.

### 5. Classify findings

Each finding should be classified as:

- blocker;
- high risk;
- medium risk;
- low risk;
- informational;
- false positive.

### 6. Recommend action

Recommendations may include:

- replace with placeholder;
- move to local ignored file;
- add ignore rule;
- remove generated output;
- add license metadata;
- rotate secret;
- split public and private context;
- request human review;
- escalate to Kage Summit.

### 7. Report safely

The report must not leak the content it is trying to protect.

Use masked examples.

## Required report format

```markdown
# Sensitive data review report

## Mission

- Mission ID:
- Repository:
- Branch:
- Reviewer:
- Date:
- Review mode:

## Scope reviewed

- Included paths:
- Excluded paths:
- Commands used:

## Summary

- Overall status:
- Highest risk level:
- Publication recommendation:

## Findings

### Finding 1

- Risk level:
- Category:
- Path:
- Line or area:
- Description:
- Evidence, masked:
- Recommended action:
- Requires human approval:
- Requires rotation:
- Requires Kage Summit:

## Files that should not be public

- Path:
- Reason:

## Assets review

- Public assets checked:
- License metadata present:
- Issues:

## Git safety notes

- Working tree status:
- Staged changes reviewed:
- `.gitignore` concerns:
- `.gitattributes` concerns:

## Decision

- Safe to publish:
- Safe only after changes:
- Not safe to publish:
- Human approval required:

## Teachback

The user should be able to explain:

- what was reviewed;
- what risks were found;
- what must be changed before publishing;
- what remains uncertain.
```

## Publication recommendation levels

### Safe to publish

Use only when:

- no blockers or high-risk findings remain;
- all files are within public scope;
- assets are license-safe;
- no private context is included;
- no secrets or personal data are present based on reviewed scope;
- required review is complete.

### Safe after remediation

Use when:

- issues are clear;
- remediation is small;
- publication should wait until changes are made and reviewed.

### Not safe to publish

Use when:

- secrets are present;
- personal data is present;
- private local context is present;
- copyrighted or unlicensed assets are present;
- scope is unclear;
- review was incomplete;
- the repository includes excluded paths that may be published accidentally.

## Stop conditions

Stop and ask when:

- the review scope is unclear;
- a path looks private but was not excluded;
- a file appears to contain secrets;
- personal data appears in examples, logs, screenshots, or outputs;
- local Village memory appears in public paths;
- assets lack license metadata;
- the agent needs to inspect a path not listed in the Mission Charter;
- the agent needs to modify files to continue;
- the user asks to publish despite unresolved blockers;
- the agent is uncertain whether content is sensitive.

## Handling discovered secrets

If a secret is found:

1. Do not reproduce it.
2. Stop if continued review may expose more secrets.
3. Report the file and masked type.
4. Recommend removing the secret.
5. Recommend rotating the secret if it may be real.
6. Do not commit remediation unless explicitly approved.
7. Do not store the secret in memory.

## Handling personal data

If personal data is found:

1. Do not reproduce it.
2. Replace examples with placeholders in the report.
3. Recommend anonymization, deletion, or moving to ignored local storage.
4. Escalate if the data appears to belong to real customers, employees, or private individuals.

## Handling private local context

If Local Village context appears in a public path:

1. Stop and report.
2. Recommend moving it under ignored local Village paths.
3. Check whether `.gitignore` protects the intended local path.
4. Do not summarize private content into public documentation.
5. Do not promote local learning to public doctrine without approval.

## Handling assets

For every public asset, verify:

- source;
- creator;
- license;
- allowed use;
- attribution requirements;
- whether it is generic or tied to copyrighted characters;
- whether the asset contains hidden metadata or private names.

If uncertain, mark the asset as not safe for public release.

## Memory and learning

The reviewer may create a learning proposal only if explicitly allowed.

The reviewer may not store:

- secrets;
- personal data;
- private local context;
- internal business details;
- copyrighted assets;
- raw findings that reveal sensitive content.

Allowed memory content should be limited to generic lessons, such as:

```text
Before public push, run a sensitive data review over staged changes and public documentation.
```

## Review level

Minimum review level:

- Level 1 for small documentation-only changes with no private context.
- Level 2 for public releases, repository initialization, templates, policies, assets, scripts, adapters, tools, and any change involving examples or generated outputs.
- Level 3 for doctrine changes, security policy changes, memory policy changes, cross-Village promotion, or unresolved sensitivity disputes.

## Violations

A violation occurs if an agent:

- exposes a secret;
- reproduces personal data;
- inspects private paths without approval;
- modifies files during a read-only review;
- commits or pushes without explicit permission;
- publishes local Village context;
- marks content safe without checking the approved scope;
- hides uncertainty;
- claims safety without evidence.

Violations must be reported to the Hokage and may require Jounin review or Kage Summit escalation.

## Completion checklist

Before closing the mission, confirm:

- scope was explicit;
- only approved paths were reviewed;
- only approved commands were used;
- findings were reported without leaking sensitive values;
- blockers were clearly marked;
- publication recommendation is clear;
- uncertainty is documented;
- required review level was met;
- teachback is complete.
