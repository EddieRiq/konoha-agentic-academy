# Local Village bootstrap Scroll

## Status

Active.

## Purpose

This Scroll defines a safe workflow for creating a local Allied Village from the public Village templates.

It helps an operator create a local Village structure, copy the approved templates, rename them, validate Git ignore rules, and confirm that no private context is exposed.

## Core rule

Local Village bootstrap creates local context boundaries.

It does not approve private context for publication.

## Scope

This Scroll may be used to bootstrap a local Allied Village such as:

```text
alliance/kirigakure/
```

The workflow supports:

- creating a local Village folder;
- copying templates from `alliance/templates/village/`;
- renaming template files into local working files;
- creating basic local subfolders;
- applying a local `.gitignore`;
- validating that the local Village is ignored by Git;
- documenting what the Village is allowed to contain;
- preparing the Village for future local missions.

## Out of scope

This Scroll does not:

- create executable agents;
- configure Claude Code, Codex, Ollama, Obsidian, GitHub, or other adapters;
- import private books or converted literature;
- import credentials, `.env` files, tokens, or secrets;
- inspect the user's machine beyond approved paths;
- publish a local Village;
- weaken Academy doctrine;
- bypass the Mission Charter.

## Required reading

Before using this Scroll, read:

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
alliance/README.md
docs/guides/local_village_bootstrap.md
docs/guides/public_private_boundary.md
```

## Required templates

The public templates must exist at:

```text
alliance/templates/village/README.template.md
alliance/templates/village/AGENTS.local.template.md
alliance/templates/village/village_manifest.template.md
alliance/templates/village/local_context_pack.template.md
alliance/templates/village/private_boundary_checklist.md
alliance/templates/village/gitignore.template
```

If any template is missing, stop and report the missing file.

## Mission Charter requirements

A Mission Charter using this Scroll must explicitly define:

- Village name;
- target local path;
- allowed source template path;
- allowed destination path;
- whether folder creation is allowed;
- whether file moves or copies are allowed;
- whether Git ignore validation is allowed;
- whether local context may be added;
- whether private files may be created;
- review level;
- completion criteria.

The Mission Charter must not assume that a local Village may be created merely because templates exist.

## Recommended local structure

A local Village may use this baseline structure:

```text
alliance/<village-name>/
  README.md
  AGENTS.local.md
  village_manifest.md
  private_boundary_checklist.md
  .gitignore
  context/
    local_context_pack.md
  doctrine/
  memory/
    local/
    private/
  private-library/
    books/
    papers/
    articles/
  assets/
    private/
  outputs/
  tmp/
```

This structure is local-first and must remain ignored unless explicitly approved for publication.

## Template mapping

Use this mapping when bootstrapping a Village:

```text
README.template.md -> README.md
AGENTS.local.template.md -> AGENTS.local.md
village_manifest.template.md -> village_manifest.md
local_context_pack.template.md -> context/local_context_pack.md
private_boundary_checklist.md -> private_boundary_checklist.md
gitignore.template -> .gitignore
```

## Safe bootstrap flow

### 1. Confirm mission scope

The agent must restate:

- Village name;
- destination path;
- source templates;
- allowed actions;
- forbidden actions;
- expected output.

If anything is unclear, stop and ask.

### 2. Confirm public/private boundary

Before creating files, confirm that:

- the destination is local;
- the destination is ignored by Git or will be ignored before private content is added;
- no private context will be copied into public repo files;
- no secrets will be requested or stored;
- no copyrighted source material will be committed.

### 3. Create folders

Only create folders explicitly allowed by the Mission Charter.

If a folder already exists, do not overwrite it silently. Report it and ask whether to reuse it.

### 4. Copy templates

Copy public templates into the local Village and rename them using the approved mapping.

Do not copy content from another private Village unless explicitly allowed.

### 5. Apply local `.gitignore`

Create the local `.gitignore` from `gitignore.template`.

The local `.gitignore` is a defense-in-depth mechanism. It is not a substitute for human review.

### 6. Validate global Git ignore

Run a Git ignore check for the Village path.

Example:

```bash
git check-ignore -v alliance/kirigakure/test.md
```

Expected result: Git must show an ignore rule for the local Village path.

If the Village path is not ignored, stop before adding any private content.

### 7. Validate public repo status

Run:

```bash
git status
```

A correctly ignored local Village should not appear as untracked.

If it appears, stop and fix the ignore boundary before continuing.

### 8. Fill only safe placeholders

The agent may fill generic metadata such as:

- Village name;
- purpose;
- local owner placeholder;
- allowed public references;
- local folder map.

The agent must not invent:

- project secrets;
- private paths;
- credentials;
- business rules;
- model details;
- client data;
- proprietary context.

### 9. Report result

The final report must include:

- created folders;
- created files;
- templates used;
- Git ignore validation;
- any files intentionally left blank;
- any missing context;
- next recommended action.

## Commands

Commands are allowed only if the Mission Charter explicitly permits them.

Usually safe with approval:

```bash
mkdir -p alliance/<village-name>/context
mkdir -p alliance/<village-name>/doctrine
mkdir -p alliance/<village-name>/memory/local
mkdir -p alliance/<village-name>/memory/private
mkdir -p alliance/<village-name>/private-library/books
mkdir -p alliance/<village-name>/assets/private
mkdir -p alliance/<village-name>/outputs
mkdir -p alliance/<village-name>/tmp
cp alliance/templates/village/README.template.md alliance/<village-name>/README.md
cp alliance/templates/village/AGENTS.local.template.md alliance/<village-name>/AGENTS.local.md
cp alliance/templates/village/village_manifest.template.md alliance/<village-name>/village_manifest.md
cp alliance/templates/village/local_context_pack.template.md alliance/<village-name>/context/local_context_pack.md
cp alliance/templates/village/private_boundary_checklist.md alliance/<village-name>/private_boundary_checklist.md
cp alliance/templates/village/gitignore.template alliance/<village-name>/.gitignore
git check-ignore -v alliance/<village-name>/test.md
git status
```

Sensitive or forbidden unless explicitly approved:

```bash
git add alliance/<village-name>/
git commit
git push
rm -rf
cp -r /private/path alliance/<village-name>/
find / -name "*"
cat .env
```

## Stop conditions

Stop immediately if:

- the local Village path is not ignored;
- a private file would be added to Git;
- the Mission Charter does not allow folder or file creation;
- the destination path is ambiguous;
- the source templates are missing;
- the agent is asked to copy private literature into the public repo;
- credentials, secrets, personal data, or proprietary project files appear;
- the user asks to publish a local Village without review;
- the agent would need to inspect paths outside the approved scope.

## Review requirements

Minimum review level:

- Level 1 for creating an empty local Village from templates.
- Level 2 if local project context, private literature, local memory, or tool configuration is added.
- Level 3 if any local learning is proposed for promotion to public doctrine.

## Teachback

Before mission closure, the user must be able to explain:

- what a local Village is;
- why it must remain ignored;
- where local context goes;
- which files came from public templates;
- why `.gitignore` is not a security guarantee;
- what must never be committed.

## Mission Report checklist

The Mission Report must include:

```text
Village name:
Destination path:
Templates used:
Files created:
Folders created:
Git ignore validation:
Git status result:
Private content added: yes/no
Secrets encountered: yes/no
Publication risk:
Review required:
Next action:
```

## Violations

A violation occurs if an agent:

- creates a local Village without explicit approval;
- adds private context before ignore validation;
- commits a local Village;
- copies private literature into public documentation;
- invents local project facts;
- treats `.gitignore` as sufficient security;
- bypasses review;
- declares the Village ready without evidence.

Violations must be reported and may trigger Jounin review or Kage Summit escalation.

## Related documents

```text
alliance/README.md
alliance/templates/village/
docs/guides/local_village_bootstrap.md
docs/guides/public_private_boundary.md
scrolls/local_context_scroll.md
scrolls/sensitive_data_review_scroll.md
scrolls/publication_safety_scroll.md
scrolls/git_safety_scroll.md
```
