# Eval runner readiness template

Status: template.

Use this template before proposing or implementing any executable eval runner.

A completed readiness review does not grant execution permission by itself.

## Runner identity

Runner name:

Runner owner:

Runner status:

- [ ] proposal
- [ ] prototype
- [ ] local-only
- [ ] public candidate
- [ ] deprecated

Runner phase:

- [ ] Phase 0: manual only
- [ ] Phase 1: dry-run parser
- [ ] Phase 2: local non-mutating runner
- [ ] Phase 3: adapter-backed evals
- [ ] Phase 4: release-gated evals

## Mission Charter

Mission Charter reference:

Does the Mission Charter explicitly allow runner work?

- [ ] yes
- [ ] no

If yes, allowed scope:

Blocked scope:

## Inputs

Allowed input paths:

```text
<path>
```

Blocked input paths:

```text
alliance/<village>/
.env
private-library/
memory/local/
```

Input file types allowed:

- [ ] Markdown eval cases
- [ ] Markdown templates
- [ ] public docs
- [ ] public adapter manifests
- [ ] other: <describe>

Private context required?

- [ ] no
- [ ] yes, local-only and explicitly approved

## Execution behavior

Does the runner execute prompts?

- [ ] no
- [ ] yes

Does the runner invoke adapters?

- [ ] no
- [ ] yes

Does the runner run shell commands?

- [ ] no
- [ ] yes

Does the runner mutate files?

- [ ] no
- [ ] yes

Does the runner interact with Git?

- [ ] no
- [ ] yes

If any answer is yes, describe the approval gate:

## Output behavior

Allowed output paths:

```text
<path>
```

Output includes:

- [ ] eval case id
- [ ] runner mode
- [ ] input references
- [ ] expected behavior
- [ ] observed behavior
- [ ] verdict
- [ ] evidence summary
- [ ] stop conditions
- [ ] reviewer notes

Output must not include:

- [ ] secrets
- [ ] credentials
- [ ] private source content
- [ ] private literature excerpts
- [ ] personal data
- [ ] unapproved local memory

## Evidence

Required pre-run evidence:

Required post-run evidence:

Required logs:

Evidence retention rule:

## Safety checks

- [ ] Mission Charter exists.
- [ ] Scope is explicit.
- [ ] Input paths are approved.
- [ ] Output paths are approved.
- [ ] Private context is blocked by default.
- [ ] Adapter invocation is blocked by default.
- [ ] Git operations are blocked by default.
- [ ] Failure mode is fail-closed.
- [ ] Human review remains required.
- [ ] Eval results do not authorize execution by themselves.

## Stop conditions

The runner must stop if:

- Mission Charter is missing;
- path is ambiguous;
- private context may be exposed;
- adapter permission is unclear;
- expected behavior is undefined;
- output path is not approved;
- evidence cannot be produced safely;
- execution would exceed approved scope.

## Readiness verdict

- [ ] Ready for manual review only
- [ ] Ready for dry-run parser prototype
- [ ] Ready for local non-mutating prototype
- [ ] Blocked
- [ ] Rejected

Reason:

Reviewer:

Approval status:

- [ ] not approved
- [ ] approved for proposal only
- [ ] approved for prototype
- [ ] approved for implementation
