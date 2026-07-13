# v3.2.1 Supervised Task Evidence Bundle Scope

## Context

v3.2.0 introduced a normalized policy contract for supervised tasks.

Existing evidence artifacts already include:

- a declared-only evidence collection stub;
- task execution results;
- controlled tool reports;
- read-only repository inspection reports;
- mission-local evidence folders.

They do not provide one deterministic mapping from every contract evidence requirement to verified source bytes, claims, findings and unresolved items.

## Objective

Add a read-only evidence composition and validation layer linked directly to a v3.2.0 supervised task contract.

## Included

- supervised task evidence bundle schema;
- evidence validation report schema;
- deterministic validator;
- contract-reference SHA-256 verification;
- source-file SHA-256 verification;
- exact evidence-requirement coverage;
- acceptance-criterion and operation links;
- evidence states: complete, incomplete, contradicted;
- claims separated from findings;
- unresolved-item explanations;
- private-path blocks;
- sandbox-only validation output;
- example bundle and source report;
- focused tests, guide and review Scroll.

## Excluded

- automatic evidence collection;
- command execution;
- model invocation;
- patch application;
- Git operations;
- network access;
- private-memory reads or writes;
- approval consumption;
- acceptance decision;
- mission closure;
- Hokage Shell integration;
- migration of existing evidence artifacts.

## Compatibility

The bundle composes existing evidence by source path and hash. It does not replace:

```text
evidence_collection_stub
task_execution_result
controlled_tool_execution_report
repo_inspection_report
mission_closure_report
```

Future versions may add adapters that produce bundle entries from those reports. v3.2.1 performs no automatic conversion.

## Acceptance criteria

1. A complete example validates as `ready_for_human_review`.
2. Every contract evidence requirement maps exactly once.
3. Contract ID and mission ID match the referenced contract.
4. Contract and source SHA-256 values match actual bytes.
5. Traversal, absolute and private-context paths are blocked.
6. Supported claims reference only satisfied evidence.
7. Contradicted evidence yields `contradicted`.
8. Missing or unresolved evidence yields `incomplete`.
9. Incomplete evidence includes an unresolved explanation.
10. Validation output stays under sandbox.
11. Production validator executes no subprocess.
12. Focused and canonical tests pass.
13. Complete evidence still grants no execution authority.
