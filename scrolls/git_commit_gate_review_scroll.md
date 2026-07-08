# Git Commit Gate Review Scroll

Status: review Scroll.

Use this Scroll to review Git Commit Gate behavior before accepting a commit gate run or release.

## Review scope

Review:

- staged paths;
- commit message;
- approval evidence;
- no-push boundary;
- no-stage boundary;
- private path blocking;
- report output;
- tests.

## Required checks

A valid commit gate run must show:

- explicit staged files;
- no private or local-only staged paths;
- a single-line commit message;
- preview mode unless confirmed commit is intentionally requested;
- exact approval token for confirmed commit;
- no Git push;
- no Git clean;
- no Git reset;
- no adapter execution;
- no private context access.

## Blockers

Block the run if:

- staged paths include private material;
- staged paths are broad, ambiguous, or not allowlisted;
- the gate attempted to stage files;
- the gate attempted to push;
- the gate attempted to clean or reset files;
- commit approval token is missing or wrong;
- the commit message is vague, unsafe, or multi-line;
- the report cannot identify what was committed.

## Approval boundary

The approval token authorizes only the commit of already staged allowlisted files.

It does not authorize:

- new staging;
- push;
- cleanup;
- reset;
- mission execution;
- adapter execution;
- private context access;
- future commits.

## Expected evidence

Reviewers should see:

- command used;
- staged file list;
- preview or confirmed mode;
- commit message;
- commit hash when confirmed;
- safety boundary output;
- test evidence.

## Reviewer outcome

Use one of:

- `approved_for_commit_gate_release`;
- `revision_required`;
- `blocked`.

Do not approve if any boundary is unclear.
