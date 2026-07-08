# Local Village Bootstrap and Hardware Profile

v2.5.0 adds the Local Village Bootstrap and Hardware Profile layer.

This release turns the original Local Village idea into a safe, explicit, local-first operation.

## Purpose

A Local Village is a private project workspace for local context, local memory, local assets, local style guides, local missions, and local configuration.

The first intended Local Village name remains:

```text
Kirigakure
```

The public repository must not receive private Village content.

## Core rule

```text
Private context stays local.
Hardware profile is evidence only.
Local config is not permission.
```

## What the tool may do

The Local Village Bootstrap tool may:

- build a read-only hardware profile with Python stdlib;
- detect OS, CPU count, Python version, disk summary, and tool presence;
- record that GPU/VRAM are not inspected by the safe stdlib profile;
- create a private Local Village skeleton under an explicit `--village-root`;
- create local memory vault directories;
- create a local style guide template;
- create a local village config;
- write a bootstrap report.

## What the tool may not do

The tool may not:

- read project files;
- read `.env`;
- read credentials;
- read emails;
- read user documents;
- scan arbitrary directories;
- use network access;
- invoke models;
- invoke adapters;
- execute shell commands;
- apply repository changes;
- stage files;
- commit files;
- push files;
- authorize private context access;
- authorize background agents.

## Approval tokens

Hardware profile confirmation requires:

```text
INSPECT_LOCAL_HARDWARE
```

Local Village bootstrap confirmation requires:

```text
BOOTSTRAP_LOCAL_VILLAGE
```

These tokens authorize only the specific profile or bootstrap operation.

They do not authorize execution, private context access, model invocation, adapter invocation, repository apply, Git operations, doctrine rewrite, or mission closure.

## Commands

Preview profile:

```powershell
python .\tools\local_village\bootstrap_local_village.py profile `
  --repo-root "." `
  --village-root ".\sandbox\kirigakure-v2-5-smoke" `
  --village-name "kirigakure"
```

Confirmed profile:

```powershell
python .\tools\local_village\bootstrap_local_village.py profile `
  --repo-root "." `
  --village-root ".\sandbox\kirigakure-v2-5-smoke" `
  --village-name "kirigakure" `
  --profile-id "kirigakure-v2-5-profile" `
  --confirm-profile `
  --approval-token "INSPECT_LOCAL_HARDWARE" `
  --output ".\sandbox\kirigakure-v2-5-profile.json" `
  --force
```

Preview bootstrap:

```powershell
python .\tools\local_village\bootstrap_local_village.py bootstrap `
  --repo-root "." `
  --village-root ".\sandbox\kirigakure-v2-5-smoke" `
  --village-name "kirigakure" `
  --bootstrap-id "kirigakure-v2-5-bootstrap"
```

Confirmed bootstrap:

```powershell
python .\tools\local_village\bootstrap_local_village.py bootstrap `
  --repo-root "." `
  --village-root ".\sandbox\kirigakure-v2-5-smoke" `
  --village-name "kirigakure" `
  --bootstrap-id "kirigakure-v2-5-bootstrap" `
  --hardware-profile ".\sandbox\kirigakure-v2-5-profile.json" `
  --confirm-bootstrap `
  --approval-token "BOOTSTRAP_LOCAL_VILLAGE" `
  --force
```

Doctor:

```powershell
python .\tools\local_village\bootstrap_local_village.py doctor `
  --village-root ".\sandbox\kirigakure-v2-5-smoke" `
  --json
```

## Canonical private structure

```text
config/
memory/vault/
assets/
style/
missions/
context/
local_kage/
reports/
.konoha.local/
```

Memory vault:

```text
memory/vault/00-inbox/
memory/vault/10-requests/
memory/vault/20-decisions/
memory/vault/30-missions/
memory/vault/40-communications/
memory/vault/50-context-packs/
memory/vault/90-archive/
```

## Public/private boundary

Public repository:

- generic templates only;
- generic examples only;
- original and license-safe assets only;
- no private Village content.

Local Village:

- private memory;
- private assets;
- private style guides;
- private mission context;
- private local configuration.

## Relationship with v2.0-v2.4

- v2.0 closes missions with teachback and memory.
- v2.1 records notification state.
- v2.2 resolves local/public visual assets.
- v2.3 strengthens Yamanaka memory and context packs.
- v2.4 records learning proposals without doctrine rewrite.
- v2.5 gives those systems a private Local Village home.

## Non-authority

A Local Village does not grant permission.

Its config can guide future plans, but every sensitive action still requires the relevant Konoha gate.
