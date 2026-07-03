# Public/private boundary guide

Konoha Agentic Academy is public by default. Allied Villages are local by default.

This guide explains what belongs in the public repository, what must stay local, and how agents should treat private context, converted literature, local memory, assets, outputs, and project-specific rules.

## Core rule

Private context stays private unless the user explicitly approves a safe, distilled, license-safe promotion.

Local material may inform learning proposals, review rubrics, and project-specific conventions, but it does not become Academy doctrine automatically.

## Public repository

The public repository may contain:

- general doctrine;
- policies;
- Scrolls;
- Clans;
- templates;
- examples with synthetic or generic content;
- public guides;
- generic assets;
- eval templates;
- license-safe distilled principles.

The public repository must not contain:

- private business context;
- customer data;
- employee data;
- internal project names that should not be public;
- credentials;
- `.env` files;
- tokens;
- private logs;
- local machine paths;
- proprietary source code;
- copyrighted books or converted copyrighted material;
- private Obsidian vaults;
- local model artifacts;
- generated outputs from private projects;
- franchise-specific or copyrighted assets.

## Allied Villages

Allied Villages hold local context and project-specific execution rules.

A local Village may contain:

- private project context;
- local `AGENTS.local.md`;
- local Mission records;
- local memory;
- local learning proposals;
- private literature;
- project-specific coding conventions;
- local review rubrics;
- private tools or adapters;
- ignored assets;
- generated outputs;
- local models.

A local Village may specialize Academy behavior, but it may not weaken Academy rules.

If a local rule conflicts with Safety Policy, Context Policy, Approval Policy, Review Policy, or Mission Charter, the stricter rule wins.

## Private literature

Private literature includes books, paid material, proprietary documentation, internal guides, converted PDFs, converted EPUBs, MarkItDown outputs, personal notes, and any source that should not be published.

Private literature may be used locally to produce:

- short notes;
- source cards;
- extracted principles;
- local review rubrics;
- learning proposals;
- approved coding conventions.

Private literature must not be copied into the public repository.

Do not commit full chapters, long excerpts, converted books, screenshots, tables, or derived text that closely tracks copyrighted source material.

Use distilled principles instead.

Example:

```text
Allowed public form:
Prefer clear error handling over silent failure.

Not allowed public form:
A copied or lightly rewritten passage from a copyrighted book explaining the same idea.
```

## Promotion path

Local learning may become public only through an explicit promotion path.

Recommended flow:

```text
Private source
  -> Local notes
  -> Extracted principles
  -> Local review rubric
  -> Learning Proposal
  -> Shikamaru draft
  -> Jounin review
  -> User approval
  -> Public doctrine or public Scroll update
```

No agent may skip this path.

## Git boundary

The `.gitignore` file protects common private paths, but `.gitignore` is not a security system.

Before every public commit or push, run a publication safety review.

Minimum checks:

```bash
git status
git diff --stat
git diff
git check-ignore -v alliance/kirigakure/test.md
git check-ignore -v .env
```

For suspicious files, inspect the staged diff before committing.

```bash
git diff --cached --stat
git diff --cached
```

## Local paths

Do not publish local machine paths unless they are generic examples.

Avoid committing paths such as:

```text
C:\Users\...
/home/user/private-projects/...
/mnt/c/Users/...
/srv/internal/...
```

Use placeholders instead:

```text
/path/to/local-village/
<LOCAL_PROJECT_ROOT>
<PRIVATE_VAULT_PATH>
```

## Secrets and credentials

Secrets must stay out of the repository.

This includes:

- `.env`;
- passwords;
- tokens;
- private keys;
- API keys;
- database URLs;
- signed URLs;
- SSH keys;
- service account files;
- exported credentials;
- logs that reveal secrets.

If a secret is committed or pasted into an agent conversation, treat it as exposed and rotate it.

## Sensitive data

Do not commit personal data or private business data.

Examples:

- names;
- IDs;
- phone numbers;
- email addresses;
- addresses;
- account numbers;
- operation numbers;
- customer records;
- raw credit data;
- internal portfolio data;
- business-sensitive metrics;
- screenshots with private details.

Use synthetic examples, schema-only examples, or aggregated descriptions.

## Assets

Public assets must be original, generic, or clearly license-safe.

Local assets may be used inside a local Village if they are ignored by Git.

Do not commit:

- franchise-specific images;
- copyrighted characters;
- private screenshots;
- purchased assets without redistribution rights;
- generated images that imitate protected characters too closely;
- internal UI screenshots with private content.

The public repository should always have text-only fallback behavior.

## Memory

Academy memory may hold public, general, approved knowledge.

Local memory may hold private, project-specific knowledge.

Memory supports action, but it does not authorize action.

A memory note is not permission to edit files, publish content, access private paths, or change doctrine.

## Agent behavior

When an agent encounters local or private material, it must:

1. confirm whether the Mission Charter allows access;
2. minimize the context it reads;
3. avoid copying sensitive content into public outputs;
4. summarize only when allowed;
5. cite or reference local sources without reproducing protected content;
6. stop if the boundary is unclear.

If the agent is unsure whether something is public or private, it must treat it as private.

## Public examples

Examples in the public repository should be:

- synthetic;
- generic;
- small;
- license-safe;
- free of private business details;
- free of local paths;
- free of credentials;
- easy to replace.

## Review checklist

Before publishing, answer:

```text
Does this commit contain private context?
Does it contain credentials?
Does it contain customer or employee data?
Does it contain copyrighted source material?
Does it contain local paths?
Does it contain private assets?
Does it expose internal project structure that should remain private?
Does it promote local learning without approval?
Does it bypass the learning proposal process?
```

If any answer is uncertain, stop and run a sensitive data review.

## Related files

Read these with this guide:

```text
AGENTS.md
protocols/safety/safety_policy.md
protocols/context/context_policy.md
protocols/approval/approval_policy.md
protocols/learning/learning_policy.md
scrolls/sensitive_data_review_scroll.md
scrolls/publication_safety_scroll.md
scrolls/private_literature_extraction_scroll.md
docs/guides/private_literature_library.md
```

## Final rule

When in doubt, keep it local.
