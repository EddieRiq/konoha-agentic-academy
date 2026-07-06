# Local Knowledge Ingestion Scroll

Status: public Scroll.

This Scroll defines the safe workflow for ingesting private knowledge sources inside a local Allied Village.

It applies to books, PDFs, converted Markdown, internal documents, research notes, project references, private documentation, and other local materials.

## Doctrine alignment

This Scroll follows these rules:

- private context stays local by default;
- evidence does not become authority automatically;
- memory supports action but does not authorize action;
- Mission Charter before execution;
- explicit approval before publication;
- user approval before doctrine changes.

## Purpose

Use this Scroll when a Village needs to transform a private source into local support material such as:

- source cards;
- local indexes;
- personal notes;
- principle cards;
- review rubrics;
- learning proposals.

This Scroll does not authorize publishing the source or copying it into public doctrine.

## Required inputs

A Mission Charter must define:

- Village name;
- local target path;
- source type;
- source access status;
- allowed tools;
- allowed outputs;
- whether conversion is allowed;
- whether indexing is allowed;
- whether principle cards are allowed;
- whether local rubrics are allowed;
- stop conditions.

## Allowed outputs

Allowed local outputs may include:

```text
source_card.md
source.pdf
source.md
source_index.md
ingestion_report.md
principle-cards/
review_rubric.md
learning_proposal.md
```

All outputs must remain inside the ignored local Village path unless explicitly designed as public templates.

## Forbidden outputs

Do not create public files containing:

- copied private source text;
- long copyrighted excerpts;
- proprietary context;
- client data;
- credentials;
- personal information;
- paid material;
- internal documentation;
- converted source files;
- local memory dumps.

## Dependency rule

Do not add ingestion dependencies to root project requirements merely because one Village needs them.

Use local Village dependencies:

```text
alliance/<village>/.venv/
alliance/<village>/requirements.local.txt
alliance/<village>/requirements.lock.local.txt
```

Root dependencies are allowed only when the public project has an approved public runtime or tool that needs them.

## Procedure

### 1. Confirm authority

Read the Mission Charter.

If the Mission Charter does not explicitly allow local source handling, stop.

### 2. Confirm target path

Identify the target path:

```text
alliance/<village>/private-library/sources/<source-id>/
```

or another approved local private path.

### 3. Validate Git boundary

Run:

```powershell
git check-ignore -v alliance/<village>/private-library/sources/<source-id>/test.md
git status
```

If the target path is not ignored, stop.

### 4. Create source card

Create `source_card.md` with:

- source identity;
- local path;
- access status;
- allowed use;
- prohibited use;
- promotion rule;
- ingestion status.

Do not paste long excerpts into the source card.

### 5. Prepare local environment

If tools are needed, use a local Village virtual environment.

Recommended pattern:

```powershell
python -m venv --prompt <village-env> alliance/<village>/.venv
alliance/<village>/.venv/Scripts/python.exe -m pip install -r alliance/<village>/requirements.local.txt
```

On Unix-like systems, use the equivalent local environment path.

### 6. Convert source locally

If conversion is allowed, write outputs only inside the local private source folder.

A conversion may produce:

```text
source.md
source.txt
source_index.md
```

Do not write converted files outside the Village.

### 7. Generate navigation index

A local index may contain short structural labels and references.

It should avoid paragraphs, examples, long quotations, and substitute copies of the source.

### 8. Create principle cards

For each useful concept, create a card in the user's own words.

Each card should include:

- source reference;
- personal summary;
- why it matters;
- review signal;
- example risk;
- possible local rule;
- promotion decision;
- approval status.

### 9. Consolidate local rubric

A rubric may be created from approved local cards.

The rubric may guide review, but it does not grant permission to edit, publish, or rewrite doctrine.

### 10. Report completion

The final report must include:

- files created;
- tools used;
- Git boundary evidence;
- unresolved risks;
- what remains local;
- whether any learning proposal is recommended.

## Review criteria

A Jounin review should check:

- Mission Charter allowed the work;
- all paths are local and ignored;
- no private source content was copied into public files;
- notes are in original words;
- long excerpts are absent;
- dependencies stayed local;
- promotion decisions are explicit.

## Stop conditions

Stop if:

- Git does not ignore the target path;
- the Mission Charter is missing or vague;
- the source access status is unclear;
- the user asks to publish private source material;
- a generated output includes long copied passages;
- a tool writes outside the approved path;
- a dependency change touches the public root without approval;
- the task starts becoming doctrine work without a learning proposal.

## Completion standard

A Local Knowledge Ingestion mission is complete only when:

- the user can identify the local source path;
- the user can rerun the Git boundary checks;
- the local outputs are listed;
- the public/private boundary is preserved;
- `git status` remains clean;
- no promotion is implied without approval.
