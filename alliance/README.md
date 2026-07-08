# Alliance

The `alliance/` directory defines how Konoha Agentic Academy cooperates with local, private, or sensitive repositories.

Konoha is the founding academy and central command. Local repositories may act as allied Villages with their own private context, local memory, local assets, lightweight workers, and project-specific rules.

Public Konoha doctrine lives in the main repository. Local Village context stays local by default.

## Core idea

A Local Village is a project-specific environment that can use Konoha doctrine without exposing private information to the public repository.

A Village may contain:

- private project context;
- local rules;
- local Kage configuration;
- Obsidian-compatible memory;
- private assets;
- local model recommendations;
- local communication style;
- project-specific mission history;
- local learning proposals.

A Local Village may cooperate with Konoha, but it does not automatically publish its memory, assets, rules, or context.

## Example

The first planned Local Village is:

```text
kirigakure
```

`kirigakure` is a local-only Village used for experimentation, private configuration, local memory, custom assets, and project-specific setup.

It must not be committed to the public repository unless explicitly sanitized and approved.

## Recommended local structure

A Local Village may use this structure:

```text
alliance/<village-name>/
  village.md
  config.yml

  kage/
    local_kage.md

  memory/
    vault/
      00-inbox/
      10-requests/
      20-decisions/
      30-missions/
      40-communications/
      50-context-packs/
      90-archive/

  style/
    corporate_language.md
    writing_preferences.md

  assets/
    ascii/
    sounds/
    palettes/

  private/
    context/
    references/
    raw-inputs/

  learning/
    learning-proposals/
    approved-tactics/
    failures/
```

This structure is only a recommendation. A Village may use a smaller setup if the mission does not require all components.

## Local-first rule

Local context stays local by default.

A Local Village must not promote private context, private memory, private assets, sensitive project details, credentials, personal data, internal communications, or proprietary information to Konoha Central unless the user explicitly approves a sanitized version.

## Git ignore rule

Local Villages should be ignored by Git unless they are sanitized examples.

Recommended `.gitignore` entries:

```gitignore
# Local allied villages
alliance/*

# Keep public alliance documentation and templates
!alliance/README.md
!alliance/templates/
!alliance/examples/
```

If a specific local Village is created inside this repository, it should be ignored explicitly:

```gitignore
alliance/kirigakure/
kirigakure/
```

## Village naming

Village names should be short, memorable, lowercase, and filesystem-safe.

Examples:

```text
kirigakure
sunagakure
kumogakure
iwagakure
otogakure
```

A Village name is a local project identity. It does not need to describe the company, client, user, or sensitive project.

## Local Kage

A Local Village may define a Local Kage.

The Local Kage manages the local mission context, local rules, local workers, local memory, and local approvals.

The Konoha Hokage remains the central orchestrator for Academy doctrine, high-impact decisions, cross-village patterns, and escalations.

## Dual approval

Some missions require approval from both the Local Kage and the Konoha Hokage.

Dual approval is required when a mission:

- modifies local rules or local memory structure;
- changes project configuration;
- touches sensitive data;
- promotes a local learning into Academy doctrine;
- creates a new Clan, Scroll, or protocol;
- changes security boundaries;
- affects architecture or long-term workflow;
- requires Kage Summit escalation.

Low-risk local tasks may be handled by the Local Kage when allowed by the Mission Charter.

## Local workers

Local Villages should prefer lightweight workers and Clerks for low-risk tasks.

Examples:

- summarize local notes;
- tag memory entries;
- prepare draft Context Packs;
- classify requests;
- format Markdown;
- detect missing fields;
- prepare first-pass summaries.

Heavy reasoning, doctrine changes, security-sensitive reviews, architecture decisions, and ambiguous trade-offs should escalate to Konoha Central.

## Hardware inspection

A Local Village may ask the user for permission to inspect the machine before recommending local workers or local models.

The inspection must be read-only and must not access private files, credentials, emails, `.env` files, project data, or local memory contents.

Example request:

```text
Can I inspect this machine to recommend a safe local agent configuration?

I will run read-only commands to detect OS, CPU, RAM, GPU, VRAM, disk availability, Python, Node, Git, Ollama, and LM Studio availability.

I will not read project files, credentials, emails, `.env` files, or private data.
```

If the user approves, the Hokage may recommend local settings such as:

```yaml
village: kirigakure
max_workers: 2
prefer_local_models: true
local_models:
  clerk: qwen-small
  summarizer: llama-small
  classifier: gemma-small
remote_escalation:
  enabled: true
```

Shikamaru writes the final configuration only after user approval.

## Local memory

Each Local Village may maintain an Obsidian-compatible Markdown vault.

Local memory may store:

- copied requests;
- email summaries;
- decision records;
- mission summaries;
- local tactics;
- user-approved explanations;
- context packs;
- communication history;
- archived references.

Local memory must not be treated as permission. Memory supports action, but does not authorize action.

## Communications

A Local Village may help process emails, messages, or work requests.

Allowed actions:

- summarize communications;
- extract tasks, dates, senders, and pending items;
- prepare draft responses;
- store sanitized summaries in local memory;
- adapt style using local writing preferences.

Forbidden without explicit human approval:

- sending emails;
- replying to messages;
- uploading attachments;
- contacting external services;
- exposing private communications to Konoha Central;
- storing raw sensitive communication in public memory.

## Local assets

The public Konoha repository may only include generic, original, or license-safe assets.

Local Villages may define private themed assets, including avatars, ASCII animations, sounds, or palettes.

Local assets override generic assets when the UI runs inside that Village.

Asset resolution order:

```text
1. alliance/<village>/assets/
2. user-level assets
3. shinobi/assets/generic/
4. text-only fallback
```

Local assets may contain private or user-provided material and should not be committed to the public repository.

## Promotion to Konoha Central

A local learning may be promoted to Konoha Central only when:

1. it is sanitized;
2. it is useful beyond the Local Village;
3. it contains no private information;
4. the Local Kage approves escalation;
5. the Konoha Hokage reviews the proposal;
6. Shikamaru drafts the doctrine or Scroll update;
7. the user approves the final diff.

Local learning is local by default.

## Completion

A Local Village setup is considered ready when:

- it is ignored by Git if private;
- it has a local config or setup note;
- it defines whether it uses local memory;
- it defines whether it uses local assets;
- it defines whether it has a Local Kage;
- it defines approval boundaries;
- it defines what must escalate to Konoha Central.

## Village templates

Public templates for local Allied Villages live in:

```text
alliance/templates/village/
```

They include:

```text
README.template.md
AGENTS.local.template.md
village_manifest.template.md
local_context_pack.template.md
private_boundary_checklist.md
gitignore.template
```

Use these templates to create local Villages with clear boundaries, local instructions, context packs, and private-content checks.

Do not commit a real local Village unless it has been explicitly reviewed and approved for public release.

## Knowledge ingestion templates

- `knowledge_source_card.template.md`: local template for documenting private sources without exposing source content.
- `principle_card.template.md`: local template for distilling source-backed principles in user-written language.

## Local Village templates

- `templates/local_village/`: public-safe template documentation for private Local Village structure.
