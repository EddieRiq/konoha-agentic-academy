# Filesystem Mutation Readiness

Status: template.

Use this template to assess whether a future filesystem mutation component is ready to be implemented.

## Component

- Name:
- Owner:
- Proposed location:
- Related runtime plan:
- Related adapter or command runner:

## Capability description

What filesystem operations would the component be technically able to perform?

```text
<capabilities>
```

## Boundary

The component must not mutate files without:

- [ ] Mission Charter authorization;
- [ ] explicit path scope;
- [ ] operation scope;
- [ ] dry-run or preview;
- [ ] execution gate;
- [ ] evidence pack;
- [ ] rollback or recovery notes;
- [ ] post-mutation result report.

## Supported modes

- [ ] read-only
- [ ] propose-only
- [ ] patch-prepared
- [ ] mutation-authorized
- [ ] local-private mutation-authorized
- [ ] destructive mutation-authorized

## Blocked by default

- [ ] destructive actions;
- [ ] bulk recursive edits;
- [ ] private-context access;
- [ ] credential or secret handling;
- [ ] Git staging;
- [ ] Git commit;
- [ ] Git push;
- [ ] tag creation;
- [ ] release creation;
- [ ] cleanup of untracked files.

## Safety controls

- [ ] path allowlist;
- [ ] path denylist;
- [ ] operation allowlist;
- [ ] command preview;
- [ ] diff preview;
- [ ] max file count;
- [ ] max file size;
- [ ] rollback note required;
- [ ] private-context detection;
- [ ] evidence logging.

## Evaluation requirements

Before implementation, define evals for:

- [ ] missing Mission Charter;
- [ ] vague path scope;
- [ ] destructive action without approval;
- [ ] private-context exposure attempt;
- [ ] Git operation bundled into file mutation;
- [ ] dry-run skipped without reason;
- [ ] rollback missing;
- [ ] out-of-scope file mutation.

## Readiness verdict

- [ ] not ready
- [ ] ready for design review
- [ ] ready for prototype proposal
- [ ] ready for implementation proposal
- [ ] blocked

## Approval

Approver:

Date:

Notes:
