# Python project scroll

This Scroll guides the setup and review of Python project structure.

## Core rule

A Python project should make the safe path the easy path.

## Status

Draft.

## Activation

Use this Scroll when creating, reviewing, or reorganizing a Python project, package, script collection, or operational workflow.

## Default mode

Planning and review are read-only by default.

Creating files, moving files, installing dependencies, or changing configuration requires an approved Mission Charter.

## Project questions

Before proposing structure, identify:

- project purpose;
- runtime environment;
- Python version;
- package manager;
- deployment target;
- data sensitivity;
- CLI or service interface;
- tests available;
- expected users;
- local Village conventions.

## Recommended structure

For reusable projects:

```text
project/
  README.md
  pyproject.toml
  src/
    package_name/
      __init__.py
      config.py
      cli.py
  tests/
  scripts/
  docs/
```

For operational data projects:

```text
project/
  README.md
  pyproject.toml
  scripts/
  src/
  tests/
  data/
    raw/
    bronze/
    silver/
    gold/
    tmp/
  docs/
```

Data folders may be ignored depending on sensitivity and size.

## Configuration

Prefer:

- `.env` for local secrets;
- `.env.example` with placeholders;
- config objects or functions;
- environment variables for deployment;
- clear defaults for non-sensitive values.

Never commit real secrets.

## Dependencies

Prefer pinned or constrained dependencies when reproducibility matters.

Review dependency changes with `dependency_review_scroll.md`.

## CLI

Operational scripts should support:

- `--help`;
- explicit inputs;
- explicit outputs;
- safe overwrite behavior;
- `--dry-run` when useful;
- `--force` only when risk is understood;
- clear exit errors.

## Tests

A project should have a known validation command.

If tests are not present, document:

- why;
- what manual validation exists;
- what first tests should be added.

## Documentation

The README should explain:

- what the project does;
- how to install;
- how to run;
- what inputs are required;
- what outputs are generated;
- what validations exist;
- what should not be committed.

## Review

Use:

- `repo_review_scroll.md`;
- `dependency_review_scroll.md`;
- `python_code_review_scroll.md`;
- `sensitive_data_review_scroll.md`;
- local Village rules.

## Completion

A Python project structure mission is complete only when the user understands how to run, validate, and safely change the project.
