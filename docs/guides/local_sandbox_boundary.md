# Local Sandbox Boundary

Status: documentation and tool boundary baseline.

## Purpose

The Local Sandbox Boundary defines where Konoha tools may create controlled
dry-run outputs before any real runtime execution exists.

The boundary exists to prevent a safe CLI from gradually becoming a general
repository mutation tool.

## Core rule

Konoha may prepare sandbox artifacts only under the declared sandbox root.

```text
sandbox/
  tmp/
  runs/
  reports/
```

A sandbox run manifest records the boundary. It does not authorize execution.

## What this baseline adds

This baseline adds:

- a sandbox run manifest schema;
- a path guard for sandbox-only writes;
- a CLI that prepares a sandbox run directory;
- tests for traversal rejection and manifest creation;
- an example sandbox manifest;
- a review Scroll.

## Allowed behavior

The sandbox preparation CLI may:

- create the declared sandbox root if it does not exist;
- create `tmp/`, `runs/`, and `reports/` under that root;
- create one run directory under `runs/<run_id>`;
- write `sandbox_run_manifest.json` inside that run directory;
- print a preparation summary.

## Blocked behavior

The sandbox preparation CLI must not:

- execute shell commands;
- perform Git operations;
- invoke adapters;
- access private Village context;
- use network access;
- mutate repository source files;
- modify docs, runtime contracts, adapters, Scrolls, or examples automatically;
- clean or delete arbitrary paths.

## Run identifiers

Run identifiers must be single safe path segments.

Allowed examples:

```text
v0-13-smoke
docs-update-001
runtime_validator_demo
```

Blocked examples:

```text
../escape
runs/demo
C:\temp\demo
demo;rm-rf
```

## Manifest authority

A sandbox run manifest is evidence of preparation only.

It does not authorize:

- mission execution;
- shell commands;
- adapter execution;
- Git operations;
- filesystem mutation outside the sandbox;
- private context access;
- doctrine changes;
- release publication.

## Relationship to previous tools

The sandbox boundary is designed to support the existing safe toolchain:

```text
Builder -> Validator -> Inspector -> Sandbox Boundary
```

The builder may generate dry-run packages.
The validator may validate package JSON.
The inspector may inspect package coherence.
The sandbox boundary may prepare a controlled output area.

None of these tools execute missions.

## Review expectations

A reviewer should confirm:

- all writes remain under the declared sandbox root;
- path traversal is rejected;
- unsafe identifiers are rejected;
- no subprocess, network, Git, or adapter calls exist;
- the manifest records blocked execution boundaries;
- tests cover valid and invalid paths.
