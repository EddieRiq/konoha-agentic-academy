# Runtime Audit Review Scroll

Status: public review Scroll.

This Scroll reviews runtime planning materials before release or before any proposal to implement executable runtime behavior.

## Purpose

Ensure runtime-related documentation remains safe, explicit, non-autonomous, and aligned with Konoha doctrine.

## Inputs

Required inputs:

- Mission Charter or review request;
- runtime planning files;
- runtime templates;
- runtime-related Scrolls;
- repository status;
- release notes draft when applicable.

Optional inputs:

- runtime audit checklist result;
- eval results;
- adapter evidence packs;
- rollback readiness notes.

## Allowed actions

The reviewer may:

- read public runtime documentation;
- inspect public templates;
- inspect public Scrolls;
- run read-only Git checks;
- identify missing boundaries;
- recommend documentation changes;
- block release or runtime promotion when safety is unclear.

## Not allowed

The reviewer must not:

- execute runtime behavior;
- run commands outside explicit review scope;
- modify files unless editing authority is granted;
- access private Village content unless explicitly authorized;
- approve execution merely because documentation exists;
- treat technical feasibility as permission.

## Review procedure

### 1. Confirm scope

Verify:

- what release or change is being reviewed;
- whether the change is documentation-only;
- whether any executable behavior is introduced;
- which files are in scope;
- which files are out of scope.

### 2. Check runtime claims

Look for statements that imply:

- autonomous runtime exists;
- adapters can execute commands automatically;
- file mutation can happen without approval;
- Git operations can happen without approval;
- release operations can happen automatically.

Any such claim is a stop condition unless explicitly implemented, tested, bounded, and approved.

### 3. Check boundaries

Verify alignment with:

- Mission Charter requirements;
- approval policy;
- adapter invocation contract;
- adapter execution gate;
- adapter evidence pack;
- adapter dry-run protocol;
- rollback boundary;
- teachback policy.

### 4. Check privacy

Confirm that public files do not include:

- private Village content;
- private knowledge sources;
- converted source content;
- private local paths except generic placeholders;
- credentials;
- secrets;
- local memory;
- local virtual environments;
- local dependency locks.

### 5. Check evidence

For release or runtime promotion, verify:

- `git status` evidence exists;
- tracked-file checks were run;
- private leakage checks were run;
- local Village ignore checks were run when relevant;
- findings are recorded.

### 6. Decide verdict

Use one of:

- Pass;
- Pass with notes;
- Needs changes;
- Blocked.

## Stop conditions

Stop and request clarification if:

- runtime scope is ambiguous;
- a document appears to authorize execution;
- a document weakens Mission Charter requirements;
- private context appears in public files;
- Git operations are implied without approval;
- rollback is missing for risky behavior;
- release notes overstate the actual implementation.

## Output

The review output must include:

- files reviewed;
- checks performed;
- findings;
- verdict;
- required changes;
- whether release or promotion may proceed.
