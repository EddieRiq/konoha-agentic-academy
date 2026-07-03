# First mission walkthrough

This guide shows how to run a first safe mission in Konoha Agentic Academy.

The example is intentionally small and read-only. It helps a user, Hokage, and any assigned agent understand the mission flow before allowing edits, commits, tools, or local context access.

## Purpose

Use this walkthrough to learn how Konoha turns a vague request into a bounded mission.

The goal is not to finish a complex task. The goal is to practice:

- defining scope;
- asking for missing context;
- approving a Mission Charter;
- running a read-only review;
- reporting evidence;
- completing Teachback.

## Example mission

User request:

```text
Review this repository and tell me whether it is ready for a public release.
```

This request sounds simple, but it may involve security, documentation, license, Git history, assets, and repository structure. The agent must not assume permission to edit files, create commits, inspect private folders, or publish anything.

## Step 1: classify the mission

Hokage classifies the request before assigning work.

Suggested classification:

```yaml
mission_type: repo_review
mode: planning
risk_level: medium
default_access: read_only
requires_mission_charter: true
requires_review: true
```

Why medium risk?

A public release review may expose sensitive content if handled carelessly. It may also lead to recommendations involving Git, publication, or repository cleanup. Those actions are not automatically allowed.

## Step 2: identify required doctrine

Before acting, the agent reads the minimum doctrine needed for this mission:

```text
AGENTS.md
README.md
core/laws/KONOHA_LAWS.md
core/conduct/AGENT_CONDUCT.md
protocols/mission-charter/mission_charter.md
protocols/safety/safety_policy.md
protocols/context/context_policy.md
protocols/approval/approval_policy.md
protocols/review/review_policy.md
scrolls/repo_review_scroll.md
scrolls/release_readiness_scroll.md
scrolls/publication_safety_scroll.md
```

The agent may summarize what it read, but reading doctrine does not grant permission to execute.

## Step 3: draft the Mission Charter

Use:

```text
missions/templates/mission_charter_template.md
```

Example charter summary:

```yaml
mission_id: mission-YYYYMMDD-release-readiness-review
mission_title: Public release readiness review
mode: execution
scope:
  - review repository structure
  - review README and documentation navigation
  - review license presence
  - review obvious sensitive-data risks
  - review relevant Scrolls and templates
out_of_scope:
  - editing files
  - staging files
  - committing
  - pushing
  - changing remotes
  - accessing local Allied Villages
  - reading private folders
  - running destructive commands
allowed_paths:
  - .
forbidden_paths:
  - alliance/*/
  - local/
  - private/
  - .env
allowed_commands:
  - git status
  - git log --oneline -5
  - git remote -v
  - find . -maxdepth 3 -type f
  - grep searches that do not print secrets verbatim
required_scrolls:
  - scrolls/repo_review_scroll.md
  - scrolls/release_readiness_scroll.md
  - scrolls/publication_safety_scroll.md
required_review:
  - Jounin review for final recommendation
completion_requires_teachback: true
```

The user must explicitly approve the Mission Charter before execution starts.

## Step 4: execute read-only review

After approval, the assigned Kagebunshin performs only the actions allowed in the charter.

Example safe commands:

```bash
git status
git log --oneline -5
git remote -v
find . -maxdepth 3 -type f | sort
```

Optional read-only checks, if allowed by the charter:

```bash
grep -RIn "password\|secret\|token\|api_key\|private_key" . --exclude-dir=.git
grep -RIn "C:\\\|/home/\|/mnt/c/Users/" . --exclude-dir=.git
```

The agent must not paste secrets into the final report. If a possible secret is found, the report should identify the file and line pattern without reproducing the secret value.

## Step 5: produce the Mission Report

Use:

```text
missions/templates/mission_report_template.md
```

The report should include:

```text
- mission id;
- charter reference;
- commands executed;
- files reviewed;
- findings;
- evidence;
- risks;
- blocked items;
- recommended next steps;
- review requirement;
- teachback prompt.
```

Example finding:

```text
Finding:
README.md exists and gives a clear entry point into the project.

Evidence:
Reviewed README.md and confirmed it links to architecture, doctrine, Scrolls, Allied Villages, and contribution guidance.

Risk:
No issue found.
```

Example blocked finding:

```text
Finding:
Public release cannot be marked ready yet.

Evidence:
Release readiness requires a dedicated sensitive-data review and Jounin review.

Risk:
Publishing without those checks may expose private paths, secrets, or local Village context.

Recommended action:
Run sensitive_data_review_scroll.md before tagging a release.
```

## Step 6: Jounin review

A Jounin reviews the Mission Report when the charter or risk level requires it.

The Jounin verifies:

```text
- the agent stayed within scope;
- commands were allowed;
- evidence supports findings;
- sensitive content was not reproduced;
- recommendations do not imply unauthorized action;
- release status is not overstated.
```

The Jounin can approve, request changes, block, or escalate to Kage Summit.

## Step 7: Teachback

The user must be able to explain the result.

Teachback questions:

```text
1. What was reviewed?
2. What was not reviewed?
3. What evidence supports the conclusion?
4. What risks remain?
5. What action is allowed next?
6. What action is not allowed yet?
```

The mission is not complete until the user can answer these at a practical level.

## Step 8: capture learning, if needed

If the mission produced a reusable lesson, create a learning proposal.

Use:

```text
memory/yamanaka/templates/learning_proposal_template.md
```

Do not rewrite doctrine directly.

A learning proposal may recommend changes to doctrine, Scrolls, templates, or checklists. Shikamaru may draft the change only after approval.

## Example final status

```yaml
mission_status: completed
execution_mode: read_only
files_modified: false
commits_created: false
push_performed: false
review_completed: true
teachback_completed: true
release_status: ready_with_notes
```

## Common mistakes

Avoid these mistakes:

```text
- treating a user idea as approval to execute;
- editing files during a read-only review;
- assuming access to local Allied Villages;
- printing secret values in reports;
- declaring release readiness without evidence;
- skipping Jounin review;
- skipping Teachback;
- turning a lesson into doctrine without approval.
```

## Minimal first mission checklist

Before execution:

```text
[ ] User request restated.
[ ] Mission type classified.
[ ] Missing context identified.
[ ] Mission Charter drafted.
[ ] Allowed paths listed.
[ ] Forbidden paths listed.
[ ] Allowed commands listed.
[ ] Stop conditions listed.
[ ] Review level defined.
[ ] User approval received.
```

Before completion:

```text
[ ] Commands executed are listed.
[ ] Evidence is included.
[ ] No sensitive values are reproduced.
[ ] Findings separate facts from recommendations.
[ ] Required review is complete.
[ ] Teachback is complete.
[ ] Learning proposal created only if needed.
```

## Core rule

```text
A small mission done within scope is better than a large mission completed by assumption.
```
