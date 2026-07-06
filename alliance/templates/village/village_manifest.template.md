# Village manifest

This file records the local identity, boundaries, and operating assumptions for an Allied Village.

It is local doctrine.

It may specialize Konoha Academy behavior, but it may not weaken Academy rules.

## Village identity

```yaml
village_name: "{{VILLAGE_NAME}}"
village_slug: "{{VILLAGE_SLUG}}"
owner: "{{OWNER}}"
local_kage: "{{LOCAL_KAGE}}"
created_at: "{{YYYY-MM-DD}}"
status: "local"
public_safe: false
```

## Purpose

Describe why this Village exists.

```text
TODO: Explain the project, team, domain, or local use case.
```

## Scope

This Village may contain:

```text
- project-specific context;
- local coding conventions;
- local memory;
- private literature;
- private assets;
- local tools;
- local adapter configuration;
- local eval notes;
- local learning proposals.
```

This Village may not contain:

```text
- secrets committed to Git;
- unredacted personal data;
- customer-identifying data;
- copyrighted material intended for publication;
- public Academy doctrine unless safely promoted through review;
- content that weakens Konoha Laws.
```

## Public/private boundary

Default classification:

```text
local_private
```

Before any content leaves this Village, run the private boundary checklist.

Required reference:

```text
docs/guides/public_private_boundary.md
```

## Local stack

```yaml
languages:
  - "TODO"
frameworks:
  - "TODO"
package_manager: "TODO"
test_command: "TODO"
lint_command: "TODO"
format_command: "TODO"
runtime_notes: "TODO"
```

## Local paths

Approved read paths:

```text
TODO
```

Approved write paths:

```text
TODO
```

Forbidden paths:

```text
TODO
```

Ignored paths:

```text
private-library/
memory/local/
assets/private/
outputs/
tmp/
.env
.env.*
```

## Local Git rules

```text
- Do not commit this Village to the public Academy repo.
- Do not stage ignored private context.
- Do not force add ignored files without explicit human approval.
- Run git check-ignore before adding new private folders.
```

## Local context packs

Approved context packs:

```text
TODO
```

Each context pack must define:

```text
- purpose;
- source;
- sensitivity;
- freshness;
- allowed use;
- expiration or review date.
```

## Local doctrine files

```text
doctrine/coding_conventions.md
doctrine/data_conventions.md
doctrine/review_rubrics.md
```

If a doctrine file does not exist, agents may propose a draft but may not treat it as approved.

## Local reviewers

```text
TODO: human reviewer, local Jounin, or review rules.
```

## Local learning path

```text
mission evidence
memory note
learning proposal
local review
user approval
local doctrine update
optional public-safe Academy proposal
```

## Open questions

```text
TODO
```
