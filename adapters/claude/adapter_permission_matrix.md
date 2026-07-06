# Claude adapter permission matrix

Status: public declarative profile.

This file defines the default permission posture for a Claude-style coding assistant adapter.

It does not implement an adapter. It does not grant runtime authority by itself.

## Adapter identity

- Adapter family: Claude-style coding assistant
- Primary use: repository analysis, documentation review, code review, patch proposal, planning support
- Default authority: propose-only
- Execution status: not implemented

## Permission posture

| Permission area | Default level | Notes |
|---|---|---|
| Read public repository files | Allowed with Mission Charter | Reads must stay within approved scope. |
| Read ignored or private files | Blocked by default | Requires explicit Mission Charter and public/private boundary review. |
| Analyze code | Allowed with Mission Charter | Analysis is advisory, not approval. |
| Propose patches | Allowed with Mission Charter | Patches must be shown for review before use. |
| Modify files directly | Blocked by default | Requires explicit patch-authorized mission. |
| Run shell commands | Blocked by default | Commands require command-authorized mission and user approval. |
| Install dependencies | Blocked by default | Requires explicit local or sandbox authorization. |
| Access network | Blocked by default | Requires explicit approval and purpose. |
| Git add/commit/push/tag | Blocked by default | Requires release-authorized or git-authorized mission. |
| Access local Village context | Blocked by default | Requires local-private authorization. |
| Create or update memory | Blocked by default | Requires approved learning or memory capture flow. |
| Publish outputs | Blocked by default | Requires publication safety review. |

## Allowed modes

### Read-only review

Claude-style adapters may inspect approved public files and produce:

- findings;
- questions;
- risk notes;
- review comments;
- documentation improvement proposals.

They must not modify files in this mode.

### Propose-only patch planning

Claude-style adapters may propose diffs or file contents when the Mission Charter authorizes patch planning.

The proposed patch is not approved until the user or authorized reviewer accepts it.

### Patch-authorized editing

Direct file modification is allowed only when the Mission Charter explicitly says:

- which files may be changed;
- what goal the change serves;
- which stop conditions apply;
- how changes will be reviewed.

### Command-authorized support

Shell commands are blocked unless the Mission Charter explicitly grants command authority.

When granted, commands must be:

- shown before execution when practical;
- scoped to the mission;
- reversible when possible;
- followed by evidence.

## Private context rules

Claude-style adapters must not read ignored paths, local Villages, private libraries, `.env` files, credentials, generated outputs, or local memory unless the Mission Charter explicitly allows it.

Local private authorization must name the path or category being accessed.

General curiosity is not authorization.

## Git and release rules

Claude-style adapters must not perform Git operations unless explicitly authorized.

Blocked by default:

- `git add`;
- `git commit`;
- `git push`;
- `git tag`;
- release publication;
- branch deletion;
- force push.

Release work requires release readiness review and publication safety review.

## Stop conditions

Stop and ask if:

- the task implies access to private or ignored files;
- a command could modify the working tree;
- a command could delete, move, overwrite, or publish content;
- user approval is unclear;
- the requested change conflicts with Konoha laws;
- the adapter detects secrets, credentials, private data, or copyrighted source material;
- the mission scope expands beyond the Charter.

## Evidence requirements

A Claude-style adapter report should include:

- files reviewed;
- files changed, if any;
- commands proposed or executed, if authorized;
- risks found;
- validation performed;
- remaining unknowns.

## Default verdict

Claude-style adapters are strong reviewers and patch planners.

They are not autonomous executors.
