# Sandbox Evidence Hygiene Review Scroll

## Deterministic checks

```bash
git diff --check
git check-ignore -v sandbox/hokage-shell
git check-ignore -v sandbox/v3-1-1-hokage-shell-review-panels.json
git ls-files sandbox
git status --short
```

## Expected public allowlist

```text
sandbox/README.md
sandbox/tmp/.gitkeep
sandbox/worktrees/.gitkeep
```

## Focused tests

```bash
python -m unittest discover -s tests/hokage_shell -p "test_*.py"
python -m unittest discover -s tests/local_model_audit -p "test_*.py"
python -m unittest discover -s tests/beta_runtime -p "test_*.py"
```

## Safety review

- No runtime evidence is added to Git.
- No existing evidence is deleted.
- No private memory is read or published.
- No model invocation is required.
- Git operations remain behind explicit gates.
