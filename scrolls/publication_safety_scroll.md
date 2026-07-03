# Publication safety scroll

## Status

```yaml
scroll_id: publication_safety_scroll
name: Publication safety scroll
type: safety-review
default_mode: read-only
risk_level: high
owner: Konoha Agentic Academy
```

## Core rule

Publication is external exposure.

No agent may publish, push, release, share, upload, announce, or make repository content public unless the action is explicitly allowed by an approved Mission Charter and the required review is complete.

## Purpose

This Scroll defines a safe review workflow before content leaves a local workspace.

It applies before:

- `git push` to a public or shared remote;
- creating a GitHub release;
- publishing packages, assets, templates, Scrolls, tools, or adapters;
- sharing documentation outside the local workspace;
- promoting local Village material into the public Academy repo;
- exporting reports, screenshots, logs, or generated files.

## Non-purpose

This Scroll does not approve publication.

It only helps identify whether publication appears safe enough to request approval.

Publication approval still comes from the Mission Charter, Approval Policy, Safety Policy, Review Policy, and the human user.

## Required inputs

Before starting, collect only the minimum needed:

```text
- Target destination:
- Publication type:
- Files or paths proposed for publication:
- Current branch:
- Remote name and URL:
- Intended audience:
- Sensitive context involved:
- Required review level:
- Mission Charter reference:
```

If any required input is missing, stop and ask.

## Default mode

Publication safety review is read-only by default.

Allowed by default:

```text
git status
git diff --stat
git diff --cached --stat
git log --oneline -5
git remote -v
git branch --show-current
find . -maxdepth 3 -type f
```

Sensitive actions require explicit approval:

```text
git add
git commit
git commit --amend
git push
git push --force
git push --force-with-lease
gh release create
npm publish
pip upload
docker push
changing repository visibility
uploading files to external systems
posting release notes publicly
```

Forbidden by default:

```text
publishing secrets
publishing private Village context
publishing raw logs with credentials
publishing private screenshots
publishing copyrighted or franchise-specific assets
publishing private customer, employee, or operational data
publishing generated outputs that contain sensitive context
```

## Review checklist

### 1. Repository state

Check:

```text
- working tree status;
- current branch;
- upstream branch;
- latest commits;
- staged vs unstaged changes;
- untracked files;
- remote destination.
```

Flag if:

```text
- branch is not the expected branch;
- remote points to an unexpected destination;
- working tree contains unrelated changes;
- staged content differs from intended publication scope;
- repository has local-only files staged.
```

### 2. Secret scan

Look for secrets without reproducing values in the report.

Risk patterns:

```text
.env
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
token
password
passwd
secret
credential
api_key
client_secret
connection string
database URL
private key
```

If a possible secret is found:

1. do not print the value;
2. identify only file path and line number if safe;
3. recommend removal;
4. recommend rotation if it may have been committed or exposed;
5. block publication until resolved.

### 3. Sensitive data scan

Look for private or regulated content.

Examples:

```text
names
emails
phone numbers
addresses
customer IDs
employee IDs
operation numbers
account numbers
document numbers
internal URLs
internal server names
production paths
screenshots with private UI
logs with operational data
```

For public repositories, private business context must be removed or generalized.

### 4. Local Village boundary

Check that no local Allied Village content is being published unless explicitly approved.

Examples:

```text
alliance/kirigakure/
local/
private/
vault/
obsidian/
context-packs/
personal-notes/
client-work/
```

Local Village learnings may be promoted only after sanitization, Shikamaru drafting, required review, and user approval.

### 5. Asset and copyright review

Public assets must be original, generic, or license-safe.

Block publication if content includes:

```text
franchise images;
unlicensed icons;
screenshots from copyrighted media;
private company logos without permission;
brand-specific themes copied from protected material;
audio or voice assets without clear rights;
fonts that should not be redistributed.
```

Use logical asset names and text fallback when needed.

### 6. Documentation safety

Review public documentation for:

```text
private project names;
internal roadmaps;
company-specific process details;
private folder paths;
machine usernames or hostnames;
unapproved model details;
security assumptions;
credentials or connection examples with real values;
private operational decisions.
```

Public docs may describe patterns, not private implementation details.

### 7. Dependency and supply chain exposure

If publication includes dependencies, review:

```text
package manifests;
lockfiles;
GitHub Actions;
Dockerfiles;
install scripts;
curl/bash patterns;
external adapters;
external Scrolls;
generated code;
vendored files.
```

Flag:

```text
unpinned dependencies;
unknown external scripts;
unexpected binary files;
license conflicts;
network access not documented;
tools that can modify files without clear approval.
```

### 8. Generated output review

Generated artifacts must be treated as untrusted until reviewed.

Check:

```text
AI-generated Markdown;
logs;
reports;
CSV files;
Parquet files;
screenshots;
images;
audio;
model outputs;
diff summaries;
release notes.
```

Do not publish generated content if it contains private context, hallucinated claims, unsupported facts, or unsafe instructions.

### 9. Release note review

Release notes must be factual and scoped.

They must not:

```text
overstate readiness;
claim security guarantees without evidence;
claim production stability without tests;
hide known limitations;
mention private context;
include unsupported attribution;
include confidential roadmap items.
```

Preferred format:

```text
- Added:
- Changed:
- Fixed:
- Safety notes:
- Known limitations:
```

### 10. Final gate

Before recommending publication, confirm:

```text
- Mission Charter allows publication.
- Scope matches the approved publication target.
- Sensitive data review passed.
- Asset review passed.
- Dependency review passed if applicable.
- Required review level is complete.
- User understands what will become public.
- User gives explicit final approval.
```

## Output format

Use this report:

```md
# Publication safety report

## Publication target

- Destination:
- Branch or release:
- Audience:
- Files or paths reviewed:

## Current state

- Branch:
- Remote:
- Working tree:
- Latest commit:

## Checks performed

- Repository state:
- Secrets:
- Sensitive data:
- Local Village boundary:
- Assets and copyright:
- Documentation:
- Dependencies:
- Generated outputs:
- Release notes:

## Findings

| Severity | File/path | Finding | Required action |
|---|---|---|---|

## Blockers

- [ ] None found
- [ ] Blockers listed below

## Recommendation

Choose one:

```text
safe_to_request_publication
safe_with_notes
not_ready
blocked
```

## Required approvals

- Mission Charter:
- Human approval:
- Jounin review:
- Kage Summit if needed:

## Final note

Publication must not proceed until the user explicitly approves the final target and scope.
```

## Severity levels

```text
critical = secret, private data, destructive exposure, illegal or clearly unsafe content
high = internal context, private paths, unlicensed assets, risky dependency behavior
medium = unsupported claims, unclear scope, missing review evidence
low = formatting, naming, minor doc inconsistency
```

Critical and high findings block publication by default.

## Stop conditions

Stop and ask if:

```text
- publication target is unclear;
- branch or remote is unexpected;
- sensitive content may be present;
- a secret may be staged or committed;
- local Village content appears in the publication set;
- license or asset rights are unclear;
- user has not explicitly approved publication;
- review evidence is incomplete.
```

## Violations

A violation occurs if an agent:

```text
- publishes without explicit approval;
- hides sensitive findings;
- reproduces secrets in a report;
- publishes local Village context by default;
- treats this Scroll as publication approval;
- bypasses required review;
- marks publication safe without evidence.
```

## Completion

This Scroll is complete only when:

```text
- the reviewed scope is clear;
- findings are reported without leaking sensitive values;
- blockers are stated plainly;
- required approvals are listed;
- the final recommendation is evidence-based;
- no publication action has been taken unless separately approved.
```
