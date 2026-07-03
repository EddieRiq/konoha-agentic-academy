# Python clan

The Python clan defines reusable guidance for Python work inside Konoha Agentic Academy.

This clan does not replace project conventions. Local Villages may define stricter rules for their own projects, but they may not weaken Academy safety, approval, context, review, or teachback rules.

## Core rule

Python code must be clear, testable, safe to change, and honest about failure.

## Authority

This clan may guide Python work, review, and learning proposals.

It may not:

- authorize file edits;
- approve mission scope;
- override a Mission Charter;
- access private context;
- weaken local rules;
- bypass review;
- declare a mission complete.

## When to use this clan

Use this clan when a mission involves:

- Python scripts;
- Python packages;
- notebooks being converted into scripts;
- ETL code;
- model training code;
- scoring services;
- CLI tools;
- tests;
- refactors;
- dependency changes.

## Relationship with local Villages

The Academy defines reusable Python expectations.

A Local Village defines project specific details such as:

- Python version;
- package manager;
- folder structure;
- test command;
- lint command;
- logging standard;
- secrets handling;
- deployment target;
- data paths;
- model artifact paths;
- team conventions.

When both exist, use the stricter rule.

## Preferred structure

For reusable Python projects, prefer a clear separation between:

```text
src/
  package_name/
    __init__.py
    config.py
    io.py
    transform.py
    validate.py
    cli.py
tests/
scripts/
docs/
```

For small one off scripts, the structure may be simpler, but the code still needs:

- clear inputs;
- explicit outputs;
- safe paths;
- useful errors;
- no hardcoded secrets;
- basic validation.

## Coding expectations

Python code should prefer:

- clear names over clever names;
- functions with one main responsibility;
- explicit parameters over hidden globals;
- explicit errors over silent fallback;
- standard library solutions when enough;
- small modules over giant scripts;
- configuration separated from logic;
- paths handled with `pathlib`;
- CLI arguments for repeatable scripts;
- type hints when they improve readability;
- logging instead of uncontrolled printing;
- tests for critical logic.

## Data and ETL expectations

For data work, Python code should:

- validate input paths;
- validate expected columns;
- validate key uniqueness when relevant;
- validate row counts before and after joins;
- detect duplicate keys before saving;
- write final outputs safely using a temporary file first;
- avoid changing column names silently;
- avoid printing sensitive values;
- keep debug outputs in approved locations only.

## Error handling

Errors should help the next operator understand what happened.

Prefer:

```python
raise ValueError("Missing required columns: fecha, operacion")
```

Avoid:

```python
except Exception:
    pass
```

Do not hide failures to make a mission look successful.

## Logging

Logs should be useful and safe.

They may include:

- row counts;
- file paths when not sensitive;
- command stage;
- validation summaries;
- elapsed time.

They must not include:

- passwords;
- tokens;
- full connection strings;
- personal data;
- private customer identifiers;
- raw sensitive records.

## Tests

Tests should focus on behavior that can break the mission.

Useful test targets:

- parsing;
- validation;
- transformations;
- feature creation;
- scoring input schema;
- duplicate handling;
- path construction;
- error conditions.

Do not write meaningless tests only to claim coverage.

## Notebooks

Notebooks are valid for exploration, diagnosis, and analysis.

When a workflow becomes repeatable or operational, move the stable logic into scripts or modules and keep notebooks as explanation or exploration.

## Review

Python work should be reviewed with:

- `scrolls/code_review_scroll.md`;
- `scrolls/python_code_review_scroll.md`;
- local coding conventions when present;
- project tests or manual validation evidence.

## Learning

Lessons from Python missions may become learning proposals.

They may not become doctrine automatically.

A repeated pattern should be promoted only after:

1. evidence from missions;
2. distilled principle;
3. safety check;
4. user approval;
5. Shikamaru documentation update.
