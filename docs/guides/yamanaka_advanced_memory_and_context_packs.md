# Yamanaka Advanced Memory and Context Packs

## Purpose

Yamanaka memory is Konoha's local, Markdown-based mission memory layer.

This release advances the minimal memory added in v2.0 by adding:

- vault initialization;
- mission evidence capture;
- Obsidian-compatible mission memory notes;
- context pack generation;
- memory indexing;
- explicit memory non-authority boundaries.

Memory supports action but does not authorize action.

Context packs are not permission.

Summaries are not truth.

## Scope

The Yamanaka advanced memory manager may:

- initialize a local memory vault;
- create canonical memory directories;
- read an explicit Mission Workspace;
- collect mission-local evidence references;
- write mission memory notes under an explicit memory root;
- write capture reports under the memory root;
- build context packs from memory notes;
- build a memory index;
- inspect the memory vault.

It may not:

- execute mission actions;
- invoke models;
- invoke adapters;
- use network access;
- access private Village context by default;
- apply files to the repository;
- stage files;
- commit files;
- push files;
- rewrite doctrine;
- close missions.

## Vault structure

The canonical local vault structure is:

```text
memory/vault/
  00-inbox/
  10-missions/
  20-decisions/
  30-tactics/
  40-failures/
  50-scroll-proposals/
  60-context-packs/
  90-archive/
  _reports/
  _index/
```

A local Village may use its own ignored memory root.

Example:

```text
alliance/kirigakure/memory/vault/
```

The public repository must not commit private Village memory.

## Approval tokens

Mission memory capture requires:

```text
RECORD_YAMANAKA_MEMORY
```

Context pack build requires:

```text
BUILD_CONTEXT_PACK
```

These tokens only authorize the memory operation. They do not authorize execution, model calls, adapter calls, repository apply, Git operations, private context access, doctrine rewrite, or mission closure.

## Commands

Initialize a vault:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py init `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --force
```

Preview mission capture:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py capture-mission `
  --workspace-root ".\sandbox\workspace" `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --mission-id "example-mission" `
  --capture-id "example-capture"
```

Confirmed mission capture:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py capture-mission `
  --workspace-root ".\sandbox\workspace" `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --mission-id "example-mission" `
  --capture-id "example-capture" `
  --human-actor "eduardo" `
  --confirm-capture `
  --approval-token "RECORD_YAMANAKA_MEMORY" `
  --force
```

Build a context pack:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py build-context-pack `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --mission-id "example-mission" `
  --context-pack-id "example-context-pack" `
  --purpose "Compact mission context for future review." `
  --confirm-build `
  --approval-token "BUILD_CONTEXT_PACK" `
  --force
```

Index the vault:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py index `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --json
```

Inspect the vault:

```powershell
python .\tools\yamanaka_memory\manage_yamanaka_memory.py inspect `
  --memory-root ".\sandbox\yamanaka-v2-3\vault" `
  --json
```

## Evidence policy

Yamanaka memory captures references to mission-local evidence.

It does not claim that summaries are ground truth.

When a future agent uses a context pack, it must still check current evidence before action.

## Private context policy

Private local memory belongs in an ignored local Village or another explicit private memory root.

Public examples must remain generic, original, license-safe, and free of private context.
