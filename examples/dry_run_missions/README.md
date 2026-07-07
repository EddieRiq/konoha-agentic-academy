# Dry-run Mission Examples

Status: documentation-first examples.

This directory contains public-safe examples of dry-run runtime packages.

The examples are synthetic. They are intended to help reviewers understand the structure of a Konoha runtime package before executable runtime behavior exists.

## Included examples

| File | Purpose |
| --- | --- |
| `docs_update_dry_run_package.example.md` | Example package for a public documentation update plan. |
| `adapter_contract_review_dry_run.example.md` | Example package for reviewing adapter contract documentation. |
| `context_capsule_refresh_dry_run.example.md` | Example package for detecting and handling a stale context capsule. |

## Boundary

These files do not execute anything.

They do not authorize:

- shell commands;
- Git operations;
- filesystem mutation;
- adapter execution;
- private context access;
- automatic model routing;
- automatic token enforcement.

They are examples only.
