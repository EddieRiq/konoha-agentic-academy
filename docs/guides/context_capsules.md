# Context Capsules

Status: documentation-first baseline.

A Context Capsule is a compact, validated summary of one or more Konoha source documents.

Capsules reduce repeated token intake, but they do not replace source authority.

## Purpose

Context Capsules help agents start missions with the smallest safe context needed.

They are useful when Konoha has many Markdown files and repeated workflows would otherwise require loading large amounts of doctrine every time.

## Core rule

```text
Capsules may reduce context intake, but they may not reduce safety controls.
```

## What a capsule can do

A capsule may:

- summarize source documents;
- list mandatory rules;
- list stop conditions;
- identify when full source is required;
- provide a source map;
- reduce repeated reading;
- support lower-tier models with reinforced context.

## What a capsule cannot do

A capsule must not:

- authorize actions;
- replace Konoha laws;
- override the Mission Charter;
- weaken private-context boundaries;
- change doctrine;
- hide uncertainty;
- claim full coverage when it is partial;
- remain valid after source hashes change.

## Capsule metadata

Every capsule should include:

```text
capsule_id:
status:
scope:
generated_at:
generated_by:
model_or_process:
source_files:
source_hashes:
coverage:
known_omissions:
requires_full_source_when:
review_status:
expiration_or_refresh_rule:
```

## Required sections

A capsule should include:

- purpose;
- covered sources;
- mandatory rules;
- stop conditions;
- non-authorizations;
- source-on-demand triggers;
- private-context warnings;
- stale-capsule rule;
- reviewer notes.

## Source hashes

A capsule should record a hash for each source file.

If any source hash changes, the capsule becomes stale until refreshed or reviewed.

Minimum hash metadata:

```text
source_path:
sha256:
captured_at:
```

## Capsule types

### Role capsule

Summarizes role-specific doctrine.

Examples:

- Hokage capsule;
- Jounin capsule;
- Kagebunshin capsule;
- Shikamaru capsule.

### Workflow capsule

Summarizes a repeated workflow.

Examples:

- release readiness;
- adapter invocation;
- local knowledge ingestion;
- runtime lifecycle;
- eval review.

### Safety capsule

Summarizes high-priority safety rules.

Examples:

- private context;
- Git operations;
- command runner boundaries;
- filesystem mutation.

Safety capsules require stricter review and should trigger full-source reads for conflicts.

### Local capsule

Summarizes approved local context inside an Allied Village.

Local capsules must stay ignored by Git unless explicitly approved for public release.

## Capsule-first mode

Capsule-first mode is allowed when:

- capsule is current;
- source hashes match;
- mission is low or standard risk;
- action is propose-only or documentation-only;
- no doctrine conflict is present;
- no private context is requested.

## Full-source triggers

Agents must read the full source when:

- changing doctrine;
- resolving conflicts;
- making permission decisions;
- handling private context;
- preparing release readiness;
- implementing runtime behavior;
- approving command, filesystem, Git, or release operations;
- capsule is stale;
- source hashes are missing;
- mission risk is high.

## Local model compression

A local model such as an Ollama-backed model may help produce capsule drafts.

Allowed uses:

- summarizing public doctrine locally;
- classifying source documents;
- drafting capsule text;
- detecting repeated rules;
- generating source maps.

Not allowed:

- deciding authority;
- granting permissions;
- promoting doctrine;
- approving private-context access;
- replacing reviewer approval;
- claiming source truth without hashes.

## Capsule review

A capsule should be reviewed for:

- source coverage;
- missing stop conditions;
- stale hashes;
- over-compression;
- unsupported claims;
- hidden policy changes;
- private-content leakage;
- unclear full-source triggers.

## Capsule lifecycle

```text
create draft
→ attach source hashes
→ review
→ approve for limited use
→ use in capsule-first missions
→ refresh when source changes
→ retire if unsafe or obsolete
```

## Safe capsule language

Use language like:

```text
This capsule summarizes selected rules for <scope>. It does not replace the source documents.
```

Avoid language like:

```text
This capsule is the complete doctrine.
```

## Recommended storage

Public capsules may live under a future public context area only after review.

Local capsules should live inside an ignored Village, for example:

```text
alliance/<village>/context/capsules/
```

Do not commit local capsules unless explicitly reviewed and approved for public release.
