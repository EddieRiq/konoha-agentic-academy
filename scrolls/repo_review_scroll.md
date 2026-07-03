# Repo Review Scroll

```yaml
name: repo_review_scroll
version: 0.1.0
status: draft
type: scroll
risk_level: low_to_medium
default_mode: read_only
owner: Konoha Agentic Academy
```

## Purpose

This Scroll defines a safe workflow for inspecting a software repository without modifying it.

It is used when an agent needs to understand a repo, summarize its architecture, identify risks, and propose a plan before any implementation work begins.

## Core rule

Repo review is read-only by default.

The agent may inspect, summarize, map, and report. It may not edit files, create files, delete files, install dependencies, run migrations, start services with side effects, commit changes, or push changes unless a Mission Charter explicitly allows those actions.

## Authority

This Scroll does not grant permission by itself.

It must operate under:

1. `core/laws/KONOHA_LAWS.md`
2. `core/conduct/AGENT_CONDUCT.md`
3. `protocols/mission-charter/mission_charter.md`
4. `protocols/context/context_policy.md`
5. `protocols/safety/safety_policy.md`
6. `protocols/approval/approval_policy.md`
7. `protocols/review/review_policy.md`
8. `sandbox/README.md`
9. `AGENTS.md`

If this Scroll conflicts with any higher authority document, the higher authority document wins.

## When to use this Scroll

Use this Scroll when the mission asks to:

- inspect a new or existing repository;
- understand project architecture;
- find where a feature should be implemented;
- prepare a change plan;
- review technical risks before editing;
- understand tests, CI, dependencies, routes, controllers, services, models, or data flows;
- brief a human before allowing an implementation agent to modify files.

## When not to use this Scroll

Do not use this Scroll as the execution workflow for:

- editing source code;
- creating files;
- refactoring;
- running database migrations;
- changing configuration;
- installing dependencies;
- modifying CI/CD;
- committing or pushing changes;
- writing production artifacts.

Those require a separate Mission Charter and a Scroll specific to the execution task.

## Required inputs

A Repo Review mission should define:

```yaml
repo_path: ""
mission_goal: ""
review_scope:
  include_paths: []
  exclude_paths: []
  focus_areas: []
allowed_commands: []
forbidden_commands: []
sensitive_paths: []
expected_output: ""
review_required: true
```

If `repo_path`, scope, or allowed commands are missing, the agent must stop and ask.

## Default allowed actions

Unless the Mission Charter says otherwise, the agent may:

- read file and folder names;
- inspect text files;
- run read-only discovery commands;
- summarize architecture;
- identify likely entrypoints;
- identify tests and documentation;
- identify risks and missing context;
- propose files to modify later;
- propose commands to run later;
- produce a Repo Review Report.

## Default forbidden actions

Unless explicitly approved in the Mission Charter, the agent must not:

- edit files;
- create files;
- delete files;
- rename files;
- format files;
- install packages;
- update lockfiles;
- run migrations;
- start services that write state;
- call external APIs;
- read secrets;
- print secrets;
- open private local context;
- inspect ignored private villages;
- commit changes;
- push changes;
- open pull requests;
- declare implementation complete.

## Read-only command guidance

The Mission Charter must explicitly allow commands. If allowed, these are normally low-risk read-only commands:

```bash
pwd
ls
find . -maxdepth 3 -type f
git status
git log --oneline -5
git branch --show-current
git remote -v
git diff --stat
rg "pattern" .
cat path/to/file
sed -n '1,160p' path/to/file
head -n 80 path/to/file
```

The agent should prefer targeted inspection over dumping entire large files.

## Commands requiring explicit approval

These commands may be valid in some missions, but require explicit approval because they can be slow, noisy, external, or state-changing depending on the project:

```bash
npm test
pytest
make test
docker compose up
npm install
pip install
poetry install
uv sync
npm run build
python manage.py migrate
alembic upgrade
git checkout
git switch
git clean
git reset
```

If unsure whether a command is safe, stop and ask.

## Review process

### 1. Confirm mission scope

Before inspecting the repo, confirm:

- the repo path;
- the goal of the review;
- included and excluded paths;
- allowed commands;
- sensitive paths;
- expected output;
- whether the review is for planning only or for a later implementation mission.

If scope is unclear, ask the smallest useful question.

### 2. Establish repository baseline

Collect only the baseline needed for the mission:

```bash
pwd
git status
git branch --show-current
git log --oneline -5
```

Report whether the working tree is clean.

If the working tree is dirty, do not assume the changes belong to the mission. Report them and ask before proceeding if they affect the review.

### 3. Map the top-level structure

Inspect the root and key folders.

The report should identify:

- main language or framework;
- entrypoints;
- configuration files;
- dependency files;
- test folders;
- documentation folders;
- source folders;
- scripts;
- CI/CD files;
- deployment files;
- local or ignored paths if visible through safe metadata.

Do not inspect private or sensitive paths unless explicitly allowed.

### 4. Identify architecture

Depending on the repo, identify the relevant pattern:

- routes, controllers, services, repositories;
- CLI commands;
- notebooks and scripts;
- ETL pipeline stages;
- model loading logic;
- adapters and integrations;
- configuration management;
- database access;
- frontend/backend boundaries;
- package/module boundaries.

Use evidence from file paths and short code excerpts. Do not invent architecture.

### 5. Identify execution and validation paths

Find how the project is likely run or tested.

Examples:

- `README.md`;
- `pyproject.toml`;
- `requirements.txt`;
- `package.json`;
- `Makefile`;
- `docker-compose.yml`;
- `.github/workflows/`;
- `.gitlab-ci.yml`;
- test folders.

Do not run tests unless approved.

### 6. Identify risks

Report risks relevant to the mission, such as:

- secrets or credentials risk;
- missing tests;
- unclear environment setup;
- heavy files or generated outputs;
- ambiguous ownership of files;
- risky migrations;
- lockfile drift;
- fragile path handling;
- duplicated logic;
- untyped or unvalidated inputs;
- model feature mismatch;
- data leakage;
- many-to-many joins;
- hidden state;
- branch or working tree risk.

Only include risks supported by evidence.

### 7. Propose implementation plan

If the mission goal is to prepare future edits, propose:

- files likely to touch;
- files likely to create;
- files to avoid;
- commands to run only after approval;
- tests or checks to run;
- assumptions to confirm;
- review level required;
- rollback or safety notes.

The plan is a proposal, not permission.

### 8. Produce Repo Review Report

The final output must include:

```markdown
# Repo Review Report

## Mission goal

## Scope inspected

## Commands run

## Repository baseline

## Architecture summary

## Relevant files

## Execution and validation paths

## Risks and concerns

## Missing context

## Proposed next mission

## Files likely to touch later

## Commands requiring approval later

## Evidence

## Stop conditions triggered
```

## Evidence standard

The agent must distinguish between:

- observed facts;
- reasonable inferences;
- assumptions needing confirmation;
- unknowns.

Use wording like:

```text
Observed:
Inferred:
Assumption:
Unknown:
```

Do not write "the repo uses X" unless there is evidence.

## Stop-and-ask triggers

Stop and ask when:

- the repo path is missing;
- the working tree is dirty and may affect the review;
- a path appears sensitive or private;
- required files are missing;
- architecture cannot be determined from available evidence;
- a command may modify state;
- a command may access network;
- a command may expose secrets;
- the requested output requires edits;
- the review discovers a safety issue;
- the mission starts drifting into implementation.

## Handling secrets

If the agent sees a file name suggesting secrets, such as `.env`, credentials, keys, tokens, or certificates:

1. Do not open it.
2. Report the path as sensitive.
3. Continue only with non-sensitive metadata.
4. Ask for explicit approval if inspection is truly necessary.

If a secret is accidentally exposed, do not repeat it. Report that sensitive content appeared and recommend rotation.

## Local Village boundaries

If the repo contains local Village folders or ignored private context, the agent must not inspect them unless explicitly allowed by the Mission Charter.

Examples:

```text
alliance/kirigakure/
.local/
private/
secrets/
```

Local context remains local by default.

## Reviewer expectations

A Repo Review Report should normally receive at least Level 1 review.

Level 2 Jounin review is required when the report will guide:

- production code changes;
- security-sensitive changes;
- data pipeline changes;
- model deployment;
- CI/CD changes;
- dependency updates;
- database migrations;
- architecture decisions.

## Completion criteria

The Scroll is complete only when:

- the inspected scope is clear;
- commands run are listed;
- evidence is included;
- risks are stated;
- unknowns are separated from facts;
- next steps are proposed without granting permission;
- the user understands what was found and what decision is needed next.

## Minimal user-facing summary

When reporting to the user, keep the first summary short:

```text
I inspected the repo in read-only mode.
The project appears to use <framework> based on <evidence>.
The main flow seems to be <summary>.
I would not edit yet because <risk or missing context>.
Next safe step: <proposal>.
```

Then include the full Repo Review Report.

## Violations

The following are violations of this Scroll:

- editing files during read-only review;
- creating files during read-only review;
- installing dependencies without approval;
- running state-changing commands without approval;
- reading secrets without approval;
- hiding uncertainty;
- presenting assumptions as facts;
- proposing broad refactors without evidence;
- declaring implementation complete after review only;
- using this Scroll to bypass Mission Charter approval.
