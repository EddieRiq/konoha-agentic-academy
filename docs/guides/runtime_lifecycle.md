# Runtime Lifecycle

Status: public planning baseline.

This guide defines the future runtime lifecycle for Konoha Agentic Academy.

It is not an executable runtime specification. It does not grant permission to run commands, mutate files, perform Git operations, access private context, or publish releases.

## Purpose

Runtime behavior must be governed before runtime exists.

The runtime lifecycle defines the sequence a future implementation must follow when moving from intent to action.

The default mode is non-execution.

## Core rule

A runtime lifecycle does not authorize execution by itself.

Execution requires:

- an approved Mission Charter;
- an explicit scope;
- an adapter or runner contract;
- permission level validation;
- dry-run evidence where applicable;
- execution gate approval;
- evidence capture;
- rollback readiness for risky operations;
- user approval when required.

## Lifecycle stages

### 1. Mission Charter

Every runtime activity starts with a Mission Charter.

The Mission Charter must define:

- goal;
- allowed scope;
- disallowed scope;
- affected files or systems;
- permitted tools;
- required approvals;
- stop conditions;
- expected evidence;
- completion criteria.

If the Mission Charter is missing or ambiguous, the runtime must stop.

### 2. Runtime plan

A runtime plan translates the Mission Charter into proposed operational steps.

The plan must identify:

- adapter or runner involved;
- expected permissions;
- commands or mutations proposed;
- Git operations, if any;
- private context access, if any;
- expected outputs;
- rollback expectations;
- validation method.

The runtime plan is a proposal, not permission.

### 3. Boundary checks

Before any dry-run or execution, the runtime must check the applicable boundaries:

- command runner boundary;
- filesystem mutation boundary;
- Git operation boundary;
- adapter permission matrix;
- adapter invocation contract;
- adapter execution gate;
- rollback boundary;
- private context boundary;
- eval runner boundary, if evaluation is involved.

If any boundary fails, the lifecycle stops.

### 4. Dry-run

A dry-run simulates the proposed action without mutating files, running risky commands, changing Git state, publishing releases, or accessing private context beyond the approved scope.

A dry-run must report:

- intended actions;
- affected files or systems;
- commands that would be run;
- expected changes;
- risks;
- missing approvals;
- required evidence;
- whether execution can proceed.

Dry-run success is not execution approval.

### 5. Approval gate

The execution gate decides whether a dry-run or proposal can move to execution.

Approval must be explicit, scoped, and current.

Approval must not be inferred from:

- the user's general intent;
- previous approvals;
- adapter capability;
- successful dry-run;
- existing templates;
- model confidence.

If approval is missing, the runtime remains in propose-only mode.

### 6. Execution

Execution may occur only within approved scope.

Execution must:

- run only approved commands;
- mutate only approved files;
- avoid private context unless explicitly allowed;
- capture evidence;
- stop on unexpected output;
- stop on scope drift;
- avoid hidden follow-up actions;
- avoid autonomous Git or release operations unless specifically approved.

### 7. Evidence capture

Every execution must produce evidence.

Evidence should include:

- pre-execution state;
- commands or actions performed;
- files touched;
- outputs or summaries;
- errors;
- validation results;
- Git status;
- privacy checks;
- residual risk.

Evidence must not leak secrets, private data, private literature, credentials, or local-only context.

### 8. Validation

Validation confirms whether the action achieved the Mission Charter goal.

Validation may include:

- tests;
- linting;
- manual checks;
- diff review;
- file existence checks;
- Git status checks;
- privacy scans;
- user teachback.

Passing validation does not authorize extra work.

### 9. Rollback readiness

For risky changes, rollback readiness must exist before execution.

Rollback readiness includes:

- known pre-change state;
- changed files;
- restore method;
- Git recovery approach, if applicable;
- expected residual risk;
- owner approval.

If rollback is not possible, that must be stated before execution.

### 10. Closure

A runtime lifecycle closes only when:

- evidence is complete;
- validation is complete;
- Git state is known;
- private boundaries are preserved;
- user-facing summary is provided;
- unresolved risks are documented;
- the user can explain what was done and why.

## Stop conditions

Stop immediately if:

- Mission Charter is missing;
- scope is unclear;
- requested action exceeds approved permissions;
- private context may be exposed;
- command output is unexpected;
- file mutations differ from plan;
- Git status is unexpected;
- rollback readiness is insufficient;
- evidence is incomplete;
- user approval is required but absent.

## Runtime lifecycle summary

```text
Mission Charter
→ Runtime Plan
→ Boundary Checks
→ Dry-Run
→ Approval Gate
→ Execution
→ Evidence Capture
→ Validation
→ Rollback Readiness
→ Closure
```

## Non-goals

This guide does not define:

- executable runtime implementation;
- shell runner code;
- adapter SDK;
- automatic Git automation;
- autonomous release publishing;
- background agents;
- private Village runtime behavior;
- CI integration.

## Safety principle

Runtime exists to execute approved plans, not to discover permission.

Technical ability is not authorization.
