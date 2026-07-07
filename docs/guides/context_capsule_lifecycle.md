# Context Capsule Lifecycle

Status: documentation-first baseline.

This guide defines how Konoha creates, validates, refreshes, invalidates, and uses context capsules.

A context capsule is a compact, source-backed summary intended to reduce repeated context intake. It is not doctrine, not permission, and not a replacement for source files when full-source review is required.

## Purpose

Context capsules help Konoha:

- reduce repeated reading of long instruction files;
- keep routine missions within a reasonable context budget;
- route tasks to the cheapest sufficiently capable model;
- preserve traceability to source documents;
- detect stale summaries when source files change;
- avoid treating summaries as authority.

## Core rule

A capsule may compress context, but it may not compress authority.

If a task is sensitive, high-risk, ambiguous, or permission-bearing, the relevant source files must be checked directly.

## Capsule lifecycle

```text
source selection
→ source hashing
→ capsule generation
→ capsule review
→ approval status
→ use in mission intake
→ usage reporting
→ refresh or invalidation
```

## Source selection

A capsule must list every source file it summarizes.

Each source entry should include:

```text
source_path:
source_role:
source_sha256:
source_last_checked:
coverage:
```

Allowed source roles:

```text
law
conduct
policy
scroll
guide
template
local_private_source
reference
```

Local private sources must remain local and ignored by Git.

## Capsule generation

A capsule may be generated manually or by a local tool/model.

Allowed generation helpers:

- local summarizer;
- local LLM such as an Ollama model;
- manual extraction;
- script-based heading extractor;
- checklist compiler.

Generation helpers are not authorities. They produce drafts only.

## Required capsule sections

A valid capsule should include:

```text
# <capsule name>

Status:
Scope:
Intended use:
Not authorized for:
Sources:
Source hashes:
Required rules:
Stop conditions:
When to read full source:
Known omissions:
Review status:
Last refreshed:
```

## Review status

Capsules should use one of these statuses:

```text
draft
reviewed
approved-for-routine-use
stale
deprecated
blocked
```

Only `approved-for-routine-use` capsules may be used as primary intake for routine missions.

Even approved capsules cannot authorize sensitive actions.

## Hash invalidation

A capsule becomes stale when:

- any source hash changes;
- a source file is removed;
- a new source becomes relevant;
- doctrine changes in the capsule scope;
- an incident reveals missing or misleading guidance;
- a reviewer marks it stale.

A stale capsule may not be used as primary intake.

## Full-source required triggers

Agents must read source files directly when:

- Mission Charter authorization is unclear;
- private context is involved;
- Git operations are requested;
- filesystem mutation is requested;
- command execution is requested;
- release or tag work is requested;
- doctrine changes are proposed;
- safety, approval, or stop conditions are involved;
- a capsule conflicts with a source file;
- the user asks for audit-quality evidence.

## Capsule usage modes

### Capsule-first

Use an approved capsule as the first intake layer for routine, low-risk missions.

### Source-on-demand

Start with the capsule, then open source files only when the capsule points to needed details.

### Source-required

Skip capsule-only intake and read source files directly.

### Stop-and-ask

Stop when the capsule is stale, missing, ambiguous, or out of scope.

## Token governance

Capsule use should be reported in token usage reports.

A mission report should state:

```text
capsules used:
source files opened:
estimated intake reduction:
full-source triggers encountered:
over-budget reason:
```

The goal is not minimal context at all costs. The goal is sufficient context at reasonable cost.

## Local capsules

Local Allied Villages may maintain private capsules under their ignored local paths.

Suggested local path:

```text
alliance/<village>/context/capsules/
```

Local capsules must not be committed unless explicitly reviewed and approved for public release.

## Public capsules

Public capsules may exist only when they summarize public Konoha doctrine and avoid private or copyrighted content.

Public capsules must include source hashes and review status.

## Non-goals

This guide does not implement:

- automatic capsule generation;
- automatic source hashing;
- automatic context routing;
- automatic model selection;
- permission grants;
- replacement of doctrine sources.

## Acceptance checklist

A capsule lifecycle is acceptable when:

- sources are listed;
- source hashes are recorded;
- intended use is narrow;
- non-authority is explicit;
- full-source triggers are clear;
- stale conditions are defined;
- review status is visible;
- token governance reporting is supported.
