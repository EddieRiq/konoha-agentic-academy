# Mission Workspace Review Scroll

Use this Scroll when reviewing Mission Workspace changes.

## Review questions

- Is the mission ID explicit and path-safe?
- Is the workspace root explicit?
- Are all outputs contained under the workspace root?
- Does the workspace include charter, manifest, approvals, reports, and evidence areas?
- Does the manifest preserve non-authority boundaries?
- Does the tool avoid Git writes?
- Does the tool avoid adapter execution?
- Does the tool avoid private context access?
- Does the tool avoid network access?
- Is UI implementation still gated behind a draft and explicit approval?

## Required evidence

- Command used to create the workspace.
- Validation report.
- Manifest path.
- Charter path.
- Approval log path.
- Any blockers.
- Confirmation that no Git write operation occurred.

## Closure rule

A Mission Workspace is ready only when a human can explain its scope, boundaries, required approvals, and current status.
