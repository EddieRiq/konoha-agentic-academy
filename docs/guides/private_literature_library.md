# Private literature library guide

## Purpose

This guide explains how an Allied Village may use private literature, books, notes, articles, internal documents, or converted source material to improve agent behavior without publishing protected content.

The public Academy may recommend the pattern. The actual literature stays local.

## Core rule

```text
Private literature stays local.
Only distilled, license-safe, user-approved learning may be promoted.
```

## What belongs here

An Allied Village may keep local references such as:

- books converted to Markdown;
- personal notes;
- internal engineering manuals;
- course notes;
- paid articles;
- papers;
- project-specific architecture documents;
- coding guidelines from a private organization;
- local Obsidian notes;
- extracted principles;
- review rubrics.

## What must not be committed

Do not commit, push, publish, or copy into public doctrine:

- copyrighted books converted to Markdown;
- paid course material;
- proprietary company documents;
- internal architecture details;
- private prompts;
- credentials, tokens, or connection strings;
- customer or employee data;
- local paths that reveal sensitive structure;
- long excerpts from protected sources.

## Recommended local structure

Inside a local Allied Village:

```text
alliance/<village-name>/
  private-library/
    books/
      effective-python/
        source.md
        source_card.md
        notes.md
        extracted_principles.md
    papers/
    articles/
    internal-docs/

  doctrine/
    coding_conventions.md
    python_conventions.md

  review-rubrics/
    python_code_review_rubric.md

  agents/
    code_jounin.md
    python_kagebunshin.md

  learning-proposals/
```

Example for Kirigakure:

```text
alliance/<village>/private-library/books/<source-id>/
```

## Git ignore recommendation

The local library should be ignored by Git.

Recommended root `.gitignore` entries:

```gitignore
# Local Allied Villages
alliance/*/private-library/
alliance/*/internal-docs/
alliance/*/local-memory/
alliance/*/obsidian/
alliance/*/.env*
alliance/*/secrets/
alliance/*/models/
alliance/*/outputs/
```

If one Village is fully private, ignore the whole Village:

```gitignore
alliance/kirigakure/
```

Use `git check-ignore` before trusting the setup:

```bash
git check-ignore -v alliance/<village>/private-library/books/<source-id>/source.md
```

## Source card

Each source should have a source card.

Template:

```yaml
---
title:
author:
edition:
publisher:
year:
source_type: book
license_status: private-reference
publicly_shareable: false
allowed_use: local-reference-only
added_by:
added_date:
---
```

Suggested sections:

```text
# Source card

## Why this source is here

## Allowed local use

## Not allowed

## Relevant topics

## Extraction status

## Review status
```

## Conversion workflow

A safe conversion workflow:

```text
1. Place original source locally.
2. Convert to Markdown locally.
3. Store converted Markdown under private-library/.
4. Add a source_card.md.
5. Extract principles into extracted_principles.md.
6. Convert principles into a review rubric.
7. Use the rubric in review missions.
8. Propose doctrine only from distilled, license-safe principles.
```

The converted source is not doctrine. It is local reference material.

## Extracted principles

`extracted_principles.md` should contain short, actionable, paraphrased ideas.

Good:

```text
Prefer explicit errors over silent fallbacks when missing configuration would produce invalid output.
```

Avoid:

```text
Long passages copied from the source.
Chapter summaries that reproduce the book structure in detail.
Page-by-page paraphrases that replace the book.
```

## Review rubrics

Rubrics convert learning into operational checks.

Example:

```text
Python code review rubric

- Does the function have one clear responsibility?
- Are inputs validated close to the boundary?
- Are secrets excluded from logs?
- Is filesystem access isolated from business logic?
- Are errors explicit enough for debugging?
- Are tests or manual validation steps provided?
```

A rubric may guide a Code Jounin review, but it does not authorize edits.

## Promotion workflow

Learning may move from local literature into general Academy doctrine only through approval.

```text
Private source
  -> extracted principle
  -> local rubric
  -> local learning proposal
  -> user approval
  -> public doctrine or public Scroll update
```

Promotion rules:

- never copy protected text;
- cite the source as inspiration only when allowed;
- keep public rules generic;
- remove private paths and project names;
- review for copyright, privacy, and operational safety;
- require user approval.

## Local vs general learning

Not all learning should become general.

Keep local when:

- it depends on a specific project;
- it mentions private architecture;
- it uses internal naming;
- it relies on company policy;
- it contains operational secrets;
- it only applies to one toolchain.

Promote to general when:

- it is broadly useful;
- it can be stated without protected content;
- it does not reveal private context;
- it strengthens existing Academy doctrine;
- it can be reviewed and tested.

## Agent responsibilities

### Clerk

May summarize, tag, cluster, and extract candidate principles from local sources.

May not approve rules.

### Code Jounin

May review code against approved local rubrics.

May not rewrite source code unless assigned editing authority.

### Shikamaru

May draft rubrics, learning proposals, and doctrine updates.

May not create doctrine alone.

### Hokage or Local Kage

May route the work and request review.

May not bypass user approval for sensitive or doctrine-changing actions.

## Sensitive data handling

Agents must not copy sensitive source content into:

- Mission Reports;
- public docs;
- Git commits;
- issue descriptions;
- pull requests;
- prompts sent to external tools;
- release notes;
- telemetry.

When evidence is needed, cite the local source path and paraphrase the principle.

## Minimum local library checklist

Before using a private source:

```text
- The source is stored in an ignored local path.
- A source_card.md exists.
- License status is marked.
- Public sharing is explicitly false unless proven otherwise.
- Extracted principles are paraphrased.
- Review rubric is separate from source content.
- The Mission Charter allows the agent to use this source.
- Sensitive content will not be copied into reports.
```

## Stop conditions

Stop and ask when:

- the source license is unclear;
- the source contains sensitive data;
- the target output may become public;
- an agent tries to copy long source excerpts;
- a learning proposal contains protected content;
- a local rule conflicts with Academy safety;
- the Mission Charter does not allow use of private context.
