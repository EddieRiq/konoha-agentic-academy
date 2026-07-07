# Runtime Run Registry Review Scroll

Status: review Scroll.

Use this Scroll to review changes to the Runtime Run Registry.

## Review objective

Confirm that the registry provides read-only visibility into dry-run runtime runs without becoming a mission executor, file repair tool, Git tool, or private context reader.

## Required artifacts

A registry change should include:

- registry CLI;
- tests;
- registry report schema;
- example registry report;
- guide;
- index references.

## Safety review

Confirm that the registry does not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- access network;
- read private Village context;
- write files;
- delete files;
- repair packages automatically;
- authorize runtime actions.

The registry may read sandbox run files and print reports.

## Functional review

Confirm that the registry can:

- list runs under `sandbox/runs`;
- detect missing manifests;
- detect missing runtime packages;
- detect missing validation reports;
- detect missing inspection reports;
- detect missing run summaries;
- detect unsafe boundary fields;
- produce text output;
- produce JSON output;
- support passed-only filtering.

## Boundary review

A passed run must keep these boundaries:

```text
Execution: blocked
Filesystem mutation: sandbox only
Git operations: blocked
Private context access: blocked
Adapter execution: blocked
Network access: blocked
```

The registry itself must report:

```text
Filesystem mutation: read_only
```

## Stop conditions

Block the change if the registry:

- imports command execution utilities;
- shells out to Git;
- modifies sandbox files;
- cleans or deletes runs;
- writes reports without explicit future approval;
- reads ignored/private folders;
- treats a registry pass as mission authorization.

## Reviewer outcome

Use one of:

```text
approved
revision_required
blocked
```

Approval means the registry is safe as a read-only inventory tool. It does not authorize runtime execution.
