# Conversational Hokage Real Supervised Audit

## Release candidate

v3.5.0-RC1 connects the conversational Hokage to the existing deterministic
local-model audit and controlled documentation patch tools.

The user remains in:

```text
Mission>
```

## Mission flow

```text
natural-language request
→ Mission Charter approval
→ deterministic test action
→ scoped one-use Ollama grant
→ local repository audit
→ model_suggested_issues
→ validated_issues
→ suppressed_issues
→ exact patch preview and SHA-256
→ separate patch approval
→ controlled apply
→ post-patch tests
→ human review
→ human Teachback
→ closure
→ private memory
```

## Model grant

The model grant is bound to:

- mission ID;
- action ID;
- action argument hash;
- provider and model;
- localhost host;
- one repository-audit invocation.

It does not authorize model download, external network, patch application or
Git operations.

## Finding classification

`model_suggested_issues` contains untrusted model proposals.

`validated_issues` contains issues supported by deterministic evidence or exact
marker absence. Only validated issues may enter the patch plan.

`suppressed_issues` contains findings contradicted by deterministic repository
evidence and marked as possible false positives.

## Patch approval

The patch proposal includes:

- exact operations;
- exact unified diff preview;
- changed paths;
- SHA-256;
- approval and rejection phrases.

Any change to operations or preview invalidates approval.

## Private memory

Closure writes the normal mission memory plus:

```text
30-model-audits/<mission_id>_local_model_audit.md
```

The note records model identity, provider-reported token usage, issue counts,
patch status and post-patch test status. Memory remains evidence only.
