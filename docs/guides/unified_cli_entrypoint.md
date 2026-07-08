# Unified CLI Entrypoint

Status: v0.21.0 baseline.

The Unified CLI Entrypoint provides one command surface for the existing Konoha safe local-first tools.

It does not replace the underlying gates. It delegates to them.

## Purpose

Before this baseline, Konoha had several independent tools:

- dry-run runtime runner;
- runtime run registry;
- runtime package validator;
- runtime package inspector;
- sandbox preparation;
- sandbox artifact writer;
- human-approved apply plan;
- Git read-only gate;
- Git staging gate;
- read-only repo inspector.

The unified CLI makes those tools easier to use without weakening their boundaries.

## Non-goals

This CLI does not:

- execute missions;
- run arbitrary shell commands;
- invoke adapters;
- access private Village context;
- bypass approval tokens;
- bypass allowlists;
- create commits;
- push changes;
- clean or reset the repository;
- authorize runtime actions.

## Entrypoint

The initial command is:

```bash
python tools/konoha_cli.py --help
```

A future packaging release may expose it as:

```bash
python -m konoha
```

## Command groups

### Runtime

```bash
python tools/konoha_cli.py runtime dry-run --title "Demo" --scope "Demo scope" --run-id "demo" --sandbox-root sandbox --force
```

Delegates to the dry-run runtime runner.

### Runs

```bash
python tools/konoha_cli.py runs list --sandbox-root sandbox
```

Delegates to the runtime run registry.

### Package

```bash
python tools/konoha_cli.py package validate sandbox/runs/demo/runtime_package.json
python tools/konoha_cli.py package inspect sandbox/runs/demo/runtime_package.json
```

Delegates to the runtime validator and inspector.

### Sandbox

```bash
python tools/konoha_cli.py sandbox prepare --run-id demo --mission-title "Demo mission"
```

Delegates to the sandbox boundary.

### Artifact

```bash
python tools/konoha_cli.py artifact write --run-id demo --artifact-path docs/proposal.md --content "# Proposal" --artifact-kind markdown
```

Delegates to the controlled sandbox artifact writer.

### Apply

```bash
python tools/konoha_cli.py apply preview --run-id demo
python tools/konoha_cli.py apply confirm --run-id demo --approval-token APPLY_SANDBOX_PLAN
```

Delegates to the human-approved apply plan prototype.

### Git

```bash
python tools/konoha_cli.py git readiness
python tools/konoha_cli.py git stage --path README.md
```

Delegates to Git gates.

The staging command still requires the underlying staging gate's explicit confirmation and approval token for confirmed staging.

### Repo

```bash
python tools/konoha_cli.py repo inspect
```

Delegates to the read-only repo inspector.

## Dispatch boundary

The CLI dispatches only to allowlisted internal Python scripts.

It must not accept arbitrary script names, shell fragments, commands, URLs, adapter names, or private context paths as executable targets.

## Safety rules

The CLI must preserve the strongest boundary of the delegated tool.

If a delegated tool requires approval, the CLI must not hide or synthesize that approval.

If a delegated tool blocks an operation, the CLI must propagate the non-zero exit code.

If a delegated tool writes only inside sandbox, the CLI must not redirect it outside sandbox.

If a delegated tool is read-only, the CLI must not add mutation behavior.

## Exit behavior

The CLI returns the exit code from the delegated tool.

Common outcomes:

- `0`: delegated command passed;
- `1`: delegated command failed due to validation, inspection, readiness, or gate blockers;
- `2`: CLI dispatch failed, tool missing, or command invalid.

## Version boundary

v0.21.0 is a unified entrypoint baseline. It does not add new runtime authority.

The CLI improves usability, not autonomy.
