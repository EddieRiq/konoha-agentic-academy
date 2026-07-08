# Project Config and Policy Contract

Status: pre-release / configuration-policy alpha.

## Purpose

The Project Config and Policy Contract defines a single public configuration file for Konoha Agentic Academy.

The config centralizes local-first safety policy, sandbox locations, allowed public paths, blocked private paths, approval tokens, and tool locations.

Configuration supports validation and routing. It does not authorize actions by itself.

## Files

- `konoha.config.example.json`: public example config.
- `schemas/runtime/konoha_project_config.schema.json`: schema contract for the config shape.
- `tools/config_validator/validate_konoha_config.py`: read-only config validator.
- `examples/config/konoha_config_validation_report.example.json`: example validation report.
- `tests/config_validator/`: validator tests.

## Boundary

The config validator may:

- read a JSON config file;
- validate required fields;
- validate safety flags;
- validate allowed and blocked paths;
- validate explicit approval tokens;
- print text or JSON validation reports;
- fail with a non-zero exit code when blockers exist.

The config validator may not:

- execute missions;
- execute shell commands;
- perform Git operations;
- modify files;
- invoke adapters;
- access private Village context;
- use the network;
- authorize runtime actions.

## Required policy

A valid project config must keep these defaults:

- execution blocked;
- filesystem mutation blocked by default;
- sandbox writes allowed only by policy;
- repository apply requires approval;
- Git staging requires approval;
- Git commit blocked;
- Git push blocked;
- adapter execution blocked;
- private context access blocked;
- network access blocked.

## Usage

```powershell
python .\tools\config_validator\validate_konoha_config.py .\konoha.config.example.json
python .\tools\config_validator\validate_konoha_config.py .\konoha.config.example.json --json
```

## Review requirements

Before accepting a project config change, reviewers must confirm:

- safety flags remain conservative;
- private paths remain blocked;
- allowlists are narrow;
- approval tokens remain exact;
- tool paths are public and repo-relative;
- validator tests pass.
