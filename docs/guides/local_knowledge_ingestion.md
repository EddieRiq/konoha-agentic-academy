# Local knowledge ingestion

Status: public guide.

This guide defines how an Allied Village may ingest private knowledge sources locally without weakening the public/private boundary of Konoha Agentic Academy.

It is intentionally generic. It does not require any specific book, vendor, converter, model, or runtime.

## Purpose

Local knowledge ingestion helps a Village turn private sources into local navigation aids, notes, principle cards, rubrics, and learning proposals.

The goal is not to publish private material. The goal is to support local work while preserving safety, ownership, licensing, privacy, and traceability.

## Core rule

Private sources stay local.

A private source may include books, PDFs, converted Markdown, internal documentation, project notes, paid material, proprietary material, client material, or personal files.

None of those sources may be committed to the public repository.

## Recommended local structure

Use a Village-local structure like this:

```text
alliance/<village>/
  .venv/
  requirements.local.txt
  requirements.lock.local.txt
  private-library/
    sources/
      <source-id>/
        source_card.md
        source.pdf
        source.md
        source_index.md
        ingestion_report.md
        principle-cards/
          README.md
          item_001.md
          item_002.md
```

A Village may use a different internal layout, but it must preserve the same boundary rules.

## Local dependency convention

Public Konoha should not force private ingestion dependencies on every user.

Use local Village dependencies instead:

```text
alliance/<village>/.venv/
alliance/<village>/requirements.local.txt
alliance/<village>/requirements.lock.local.txt
```

Recommended virtual environment prompt:

```text
<short-village-name>env
```

Examples:

```text
<village-env>
sunaenv
iwaenv
```

These files and folders must remain local and ignored by Git unless they are explicitly designed as public templates.

## Optional converters

A Village may use optional local tools to convert files into easier-to-read formats, for example PDF to Markdown.

Converter choice is local. Konoha should document the pattern, not require a specific converter in the root project dependencies.

When using a converter, keep both the original and converted source local.

## Safe ingestion workflow

### 1. Open a Mission Charter

Before ingesting a source, define:

- the source type;
- the local Village path;
- the allowed tools;
- whether conversion is allowed;
- whether indexing is allowed;
- whether notes or principle cards may be created;
- the stop conditions;
- the expected local outputs.

### 2. Validate the private boundary

Before creating files, run a Git ignore check against the target path:

```powershell
git check-ignore -v alliance/<village>/private-library/sources/<source-id>/test.md
```

If Git does not ignore the path, stop.

### 3. Create a source card

Every private source needs a local `source_card.md`.

The card should record:

- source name;
- source type;
- ownership or access status;
- local path;
- allowed use;
- prohibited use;
- promotion rule;
- ingestion status.

The source card must not contain long copyrighted excerpts or sensitive content.

### 4. Convert or extract locally

If conversion is allowed, write converted files only inside the ignored Village path.

Examples of local outputs:

```text
source.pdf
source.md
source_index.md
```

Never write converted private sources to public folders.

### 5. Generate a local index

A local index may contain structural information such as:

- source metadata;
- line counts;
- hashes;
- headings;
- short labels;
- local references.

Avoid long excerpts. The index is for navigation, not publication.

### 6. Create principle cards

Principle cards must be written in the user's own words.

They may reference local lines or item numbers, but they must not copy long source passages.

Each card should answer:

- what principle was learned;
- why it matters;
- how it affects review;
- what risk it reduces;
- whether it should stay local or become a proposal.

### 7. Build local rubrics

A Village may consolidate cards into local rubrics.

Local rubrics help agents review work, but they do not authorize changes by themselves.

Editing, publishing, memory updates, and doctrine promotion still require explicit approval.

### 8. Promote only through proposals

A local learning may become public only if it is:

- generic;
- license-safe;
- written in original words;
- free of private context;
- reviewed;
- explicitly approved by the user.

Literature is evidence, not doctrine.

## Stop conditions

Stop immediately if:

- the target path is not ignored by Git;
- the source contains personal, client, internal, paid, copyrighted, or proprietary material and the Mission Charter does not explicitly allow local handling;
- the user asks to commit private source material;
- the task would copy long excerpts into public files;
- the converter writes outputs outside the Village;
- a generated note looks like a substitute copy of the source;
- promotion is requested without approval.

## Validation checklist

Before closing an ingestion mission:

```powershell
git status
git check-ignore -v alliance/<village>/.venv/pyvenv.cfg
git check-ignore -v alliance/<village>/requirements.local.txt
git check-ignore -v alliance/<village>/private-library/sources/<source-id>/source.md
```

Expected result:

```text
nothing to commit, working tree clean
```

and all private files must be ignored.

## Completion report

A local ingestion report should state:

- what source was ingested;
- what tools were used;
- what files were created;
- whether conversion succeeded;
- whether indexing succeeded;
- whether principle cards were created;
- whether the Git boundary was validated;
- what remains local;
- what, if anything, is proposed for later review.

## Teachback

The user should be able to explain:

- where the private source lives;
- why it is ignored by Git;
- which outputs are local;
- what can and cannot be promoted;
- how to validate the boundary again.
