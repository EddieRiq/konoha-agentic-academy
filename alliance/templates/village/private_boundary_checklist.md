# Private boundary checklist

Use this checklist before moving, copying, summarizing, publishing, committing, or promoting any local Village content.

## Rule

When in doubt, keep it local.

## Content classification

Classify the content before acting:

```text
[ ] Public-safe doctrine.
[ ] Public-safe template.
[ ] Public-safe distilled principle.
[ ] Local private context.
[ ] Sensitive project context.
[ ] Private literature.
[ ] Converted copyrighted source.
[ ] Secrets or credentials.
[ ] Personal or customer-identifying data.
[ ] Private asset.
[ ] Generated output.
[ ] Unsure.
```

If `Unsure` is selected, stop and ask.

## Public-safe checks

Content may be considered public-safe only if:

```text
[ ] It contains no secrets.
[ ] It contains no credentials.
[ ] It contains no personal identifiers.
[ ] It contains no customer data.
[ ] It contains no private project identifiers.
[ ] It contains no private paths that expose internal structure.
[ ] It contains no copyrighted source text beyond safe, minimal reference.
[ ] It contains no proprietary business details.
[ ] It does not reveal local security posture.
[ ] It does not weaken Academy doctrine.
[ ] It was reviewed by the user or approved reviewer.
```

## Private literature checks

For private books, articles, papers, paid material, or converted sources:

```text
[ ] Source stays local.
[ ] Metadata stays local unless public-safe.
[ ] Notes are local unless explicitly sanitized.
[ ] Extracted principles are short and transformed.
[ ] No long quotes are copied.
[ ] No chapter-level summaries are published.
[ ] No protected structure is replicated.
[ ] Public output contains only distilled, license-safe principles.
```

## Git checks

Before committing:

```bash
git status
git diff --stat
git diff
git check-ignore -v alliance/{{VILLAGE_SLUG}}/private-library/example/source.md
git check-ignore -v alliance/{{VILLAGE_SLUG}}/.env
git check-ignore -v alliance/{{VILLAGE_SLUG}}/memory/local/example.md
```

Expected result:

```text
Private files must be ignored.
Public templates may be tracked.
```

## Promotion checks

Before promoting local learning to public Academy doctrine:

```text
[ ] The learning came from mission evidence.
[ ] The learning is not copied from private source material.
[ ] The learning is generalized beyond the local project.
[ ] The learning does not expose private paths, clients, data, or business logic.
[ ] The learning was reviewed.
[ ] The user explicitly approved promotion.
[ ] Shikamaru drafted the doctrine update.
[ ] The change passed review.
```

## Stop conditions

Stop immediately if:

```text
- content may contain secrets;
- content may identify a person or customer;
- content may reveal private business logic;
- content may include protected copyrighted text;
- content is from a local Village and publication was not explicitly approved;
- an agent is relying on inference instead of permission;
- git check-ignore does not ignore a private file;
- the reviewer cannot determine classification.
```

## Final decision

```text
decision: "keep_local | safe_to_publish | needs_redaction | blocked | ask_user"
reviewer: "TODO"
date: "TODO"
evidence: "TODO"
notes: "TODO"
```
