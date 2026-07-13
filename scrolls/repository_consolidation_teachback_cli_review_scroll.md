# Repository Consolidation, Teachback and CLI Review Scroll

## Acceptance Gate

Run focused suites:

```bash
python -m unittest discover -s tests/mission_closure -p "test_*.py"
python -m unittest discover -s tests/konoha_cli -p "test_*.py"
python -m unittest discover -s tests/mission_runtime -p "test_*.py"
python -m unittest discover -s tests/product_runtime -p "test_*.py"
python -m unittest discover -s tests/hokage_shell -p "test_*.py"
python -m unittest discover -s tests/beta_runtime -p "test_*.py"
python -m unittest discover -s tests/package_installation -p "test_*.py"
python -m unittest discover -s tests/release_workflow -p "test_*.py"
```

Review:

```text
Teachback passed requires human evidence.
Clarification and failure do not close.
Review must be human-approved.
Execution must be successful.
Source paths stay inside the mission.
Same evidence reentry is idempotent.
Different evidence conflicts.
```

Validate registry:

```bash
python tools/konoha_cli.py --validate-registry
python tools/konoha_cli.py --registry-json
```

Confirm the CLI command array never includes synthesized approval tokens or
`--allow-network`.

## Git Delivery Gate

Before delivery:

```bash
git diff --check
git status --short
git diff --name-only
git ls-files --others --exclude-standard
```

Confirm exact package manifest scope and no staged paths.

Run private/suspicious checks:

```bash
git grep -n "Effective-Python-Brett-Slatkin\|Brett Slatkin\|Praise for Effective Python\|alliance/kirigakure/private-library/books/effective-python\|kirienv" -- .
```

Expected: no private leak outside a deliberate sanitized audit pattern.

Use the existing supervised release workflow. Do not replace its tokens or
state transitions.

## Release Closure Gate

After publication:

```bash
python tools/release_workflow/run_supervised_release.py \
  --repo-root "." \
  --plan "examples/release_workflow/v3_2_6_repository_consolidation_release_plan.example.json" \
  --output "./sandbox/reports/v3-2-6-status-after-close.json" \
  --status \
  --allow-network \
  --force
```

Required:

```text
RELEASE_CLOSED
tracking 0/0
working tree clean
valid test evidence
tag target = tested HEAD
GitHub Release published and Latest
```

## Stop conditions

Stop on:

- hidden compatibility path that accepts phrase-only closure;
- non-human review accepted as approved;
- source path traversal;
- private path in public scope;
- CLI-injected approval or network permission;
- test count drift;
- package/release regression;
- unexpected branch, commit, tag or release state.
