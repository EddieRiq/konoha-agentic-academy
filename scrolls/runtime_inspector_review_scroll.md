# Runtime Inspector Review Scroll

Status: review Scroll.

## Purpose

Review the Read-only Runtime Inspector before release or use.

The review verifies that the inspector improves package review without becoming an executor or auto-fixer.

## Required review inputs

- `tools/runtime_inspector/inspect_runtime_package.py`
- `tests/runtime_inspector/`
- a valid dry-run runtime package
- an invalid dry-run runtime package or modified fixture
- validator output when available

## Review checklist

### Non-execution boundary

Confirm that the inspector does not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- mutate package files;
- read private Village context;
- authorize runtime actions;
- execute missions.

### Read-only behavior

Confirm that the inspector:

- only reads the requested JSON package;
- prints findings to stdout;
- does not repair files;
- does not create reports unless a future explicit output feature is approved;
- exits with non-zero status when errors are found.

### Package coherence

Confirm that the inspector checks:

- root package fields;
- `mode = dry_run`;
- `execution_authorized = false`;
- blocked safety flags;
- required sections;
- mission ID consistency;
- trace events;
- manifest records;
- index records;
- validation report status;
- private/local reference fragments.

### Tests

Run:

```powershell
python -m unittest discover -s .\tests\runtime_inspector -p "test_*.py"
```

Expected:

```text
OK
```

### Smoke test

Run:

```powershell
python .\tools\runtime_inspector\inspect_runtime_package.py .\examples\dry_run_packages\builder_generated_docs_update.runtime_package.json
```

Expected:

```text
INSPECTION PASSED
```

Warnings are acceptable only when they point to review-readiness gaps and do not hide execution risk.

## Review outcomes

Use one of:

- `approved_for_release`;
- `revision_required`;
- `blocked`.

## Blocking findings

Block release if:

- the inspector executes shell commands;
- the inspector mutates files;
- the inspector performs Git operations;
- the inspector invokes adapters;
- the inspector reads private context;
- the inspector approves packages with execution flags enabled;
- the inspector hides private/local reference findings;
- tests fail.

## Closure

This Scroll does not authorize runtime execution. It only supports review of the read-only runtime inspector.
