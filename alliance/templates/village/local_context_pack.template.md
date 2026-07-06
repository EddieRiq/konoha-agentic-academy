# Local context pack

This file defines a scoped context pack for a local Allied Village.

A context pack gives agents enough context to work safely without loading unnecessary private material.

It does not authorize action.

## Metadata

```yaml
context_pack_id: "{{CONTEXT_PACK_ID}}"
village: "{{VILLAGE_SLUG}}"
title: "{{TITLE}}"
owner: "{{OWNER}}"
created_at: "{{YYYY-MM-DD}}"
updated_at: "{{YYYY-MM-DD}}"
sensitivity: "local_private"
freshness: "TODO"
status: "draft"
```

## Rule

Context supports action.

Context does not authorize action.

Agents may use this context only when it is explicitly attached to an approved Mission Charter or allowed by the user.

## Purpose

```text
TODO: What this context pack is for.
```

## Allowed use

```text
TODO: What agents may use this context for.
```

## Not allowed use

```text
TODO: What agents may not use this context for.
```

Examples:

```text
- do not publish this content;
- do not copy this content to public docs;
- do not use for unrelated missions;
- do not infer approval for file edits;
- do not use stale assumptions as truth.
```

## Sources

List sources without exposing secrets.

```text
TODO: file paths, local notes, internal docs, architecture summaries, safe references.
```

## Sensitivity check

```text
[ ] Contains no passwords.
[ ] Contains no tokens.
[ ] Contains no private keys.
[ ] Contains no customer-identifying data.
[ ] Contains no personal identifiers.
[ ] Contains no proprietary source text intended for publication.
[ ] Contains no confidential business details beyond the approved local scope.
```

If any checkbox cannot be checked, stop and reduce the context pack.

## Summary

```text
TODO: Short scoped summary.
```

## Project facts

Use facts that are sourced and stable enough for the mission.

```text
TODO
```

## Local conventions

```text
TODO
```

## Commands

Read-only commands allowed for missions using this pack:

```text
TODO
```

State-changing commands requiring explicit approval:

```text
TODO
```

Forbidden commands:

```text
TODO
```

## Paths

Allowed paths:

```text
TODO
```

Forbidden paths:

```text
TODO
```

## Known risks

```text
TODO
```

## Assumptions

Assumptions must be explicit.

```text
TODO
```

## Expiration

This context pack must be reviewed when:

```text
- project structure changes;
- local conventions change;
- dependencies change;
- sensitive context is added;
- the user marks it stale;
- the review date is reached.
```

Review date:

```text
TODO
```

## Approval

```text
prepared_by: "TODO"
reviewed_by: "TODO"
approved_by: "TODO"
approval_date: "TODO"
```
