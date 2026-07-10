# v3.1.6 Terminal Operator Baseline Scope

## Objective

Provide a compact, deterministic, read-only operator snapshot for terminal and SSH use.

## Included

- `status` command in Hokage Shell;
- text and JSON output;
- local Git branch, HEAD, cleanliness, upstream and latest-tag summary;
- latest valid mission summary;
- evidence-artifact availability;
- terminal viewer and width detection;
- explicit authority and safety boundaries;
- no-workspace-creation test;
- schema, example, guide and review Scroll;
- shell header update to v3.1.6.

## Excluded

- interactive dashboard refresh;
- background polling;
- daemon;
- network fetch;
- Git writes;
- private-memory read;
- model invocation;
- patch application;
- mission execution or closure;
- Web UI.

## Acceptance criteria

1. `status --json` returns a valid operator report.
2. A missing workspace is not created.
3. A dirty tree is surfaced as `attention_required`.
4. Invalid missions are counted and surfaced.
5. Latest mission evidence paths are summarized.
6. No changed filenames are exposed in the report.
7. Viewer fallback follows `glow -> bat -> less -> plain`.
8. Existing Hokage Shell behavior remains green.
9. Canonical Release Test Gate passes.
