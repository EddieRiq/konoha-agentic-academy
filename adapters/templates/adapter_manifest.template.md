# Adapter manifest template

Status: public template.

This template describes a proposed execution adapter without granting it authority to act.

Adapters connect Konoha doctrine to an external execution environment such as a coding assistant, shell runner, local model, hosted model, notebook, CI job, or tool wrapper.

A manifest is descriptive. It is not permission.

## Adapter identity

Adapter name: `<adapter-name>`

Adapter type:

- [ ] coding assistant
- [ ] shell runner
- [ ] local model
- [ ] hosted model
- [ ] notebook
- [ ] CI job
- [ ] tool wrapper
- [ ] other: `<describe>`

Adapter owner: `<owner>`

Adapter location: `<path-or-link>`

Public or local:

- [ ] public adapter
- [ ] local/private adapter

## Purpose

Describe what this adapter is intended to do.

Do not describe private projects, credentials, internal systems, client data, or unpublished operational details in a public manifest.

## Non-goals

This adapter must not be used for:

- actions outside the approved Mission Charter;
- bypassing Konoha laws;
- bypassing review;
- bypassing approval;
- accessing private context without explicit authorization;
- modifying memory without an approved learning flow;
- publishing local or private content.

## Execution boundary

Allowed execution environment:

```text
<environment>
```

Allowed working directories:

```text
<paths>
```

Forbidden working directories:

```text
<paths>
```

Allowed file operations:

- [ ] read only
- [ ] create files
- [ ] edit files
- [ ] move files
- [ ] delete files

Allowed commands or tool categories:

```text
<commands-or-tools>
```

Network access:

- [ ] no network access
- [ ] allowed only with explicit Mission Charter approval
- [ ] allowed for specific endpoints listed below

Approved endpoints, if any:

```text
<endpoints>
```

## Inputs

Allowed input types:

- [ ] public repository files
- [ ] local Village instructions
- [ ] local context packs
- [ ] user-provided prompt
- [ ] approved private files
- [ ] generated artifacts
- [ ] logs without secrets
- [ ] other: `<describe>`

Input restrictions:

- no secrets;
- no credentials;
- no personal identifiers;
- no private source material unless explicitly approved;
- no copyrighted source text for public output.

## Outputs

Allowed output types:

- [ ] analysis only
- [ ] Markdown
- [ ] code
- [ ] tests
- [ ] diffs
- [ ] logs
- [ ] reports
- [ ] generated artifacts
- [ ] other: `<describe>`

Output restrictions:

- no secrets;
- no unapproved private context;
- no unapproved memory updates;
- no copyrighted source excerpts beyond safe limits;
- no claim of mission completion without validation and teachback.

## Required controls

Before execution:

- [ ] Mission Charter exists.
- [ ] Scope is explicit.
- [ ] Inputs are listed.
- [ ] Outputs are listed.
- [ ] Allowed paths are listed.
- [ ] Stop conditions are listed.
- [ ] Approval requirements are clear.

During execution:

- [ ] stay within scope;
- [ ] report uncertainty;
- [ ] preserve public/private boundaries;
- [ ] stop on unexpected access, secrets, or ambiguous authority.

After execution:

- [ ] summarize actions;
- [ ] provide validation evidence;
- [ ] list changed files;
- [ ] state unresolved risks;
- [ ] complete teachback if required.

## Required reviewers

Reviewer role:

- [ ] Jounin
- [ ] Local Kage
- [ ] Hokage
- [ ] Security reviewer
- [ ] User approval

Reason:

```text
<why-review-is-needed>
```

## Approval status

- [ ] Draft
- [ ] Reviewed
- [ ] Approved for limited use
- [ ] Approved for public template use
- [ ] Rejected

Approver:

```text
<name-or-role>
```

Date:

```text
<YYYY-MM-DD>
```
