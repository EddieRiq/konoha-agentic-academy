# Hokage Terminal Operator Baseline Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/hokage_shell \
  -p "test_*.py"
```

## Read-only smoke

```bash
WORKSPACE="./sandbox/hokage-shell-v3-1-6-smoke"
REPORT="./sandbox/reports/v3-1-6-operator-status.json"

rm -rf "$WORKSPACE"

python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "$WORKSPACE" \
  status \
  --json \
  > "$REPORT"

test ! -e "$WORKSPACE"
python -m json.tool "$REPORT" >/dev/null

jq '{
  status,
  operator_state,
  repo,
  mission,
  terminal,
  next_recommended_action,
  authority,
  boundaries
}' "$REPORT"
```

## Required assertions

```text
status = passed
workspace_exists = false
workspace path remains absent
private_memory_read = blocked
workspace_mutation = blocked
repository_source_mutation = blocked
network_access = blocked
model_invocation = blocked
status_report_is_evidence_only = true
status_does_not_authorize_execution = true
```

## Dirty-tree smoke

Run only after the release files are present. The status command should report:

```text
operator_state = attention_required
attention_reasons includes working_tree_dirty
```

It must not list changed filenames in JSON.

## Security grep

```bash
grep -RInE \
  'shell=True|git (add|commit|push|tag|fetch)|gh |requests\.|urllib|ollama|memory_root' \
  tools/hokage_shell/operator_status.py \
  tests/hokage_shell/test_operator_status.py \
  || true
```

Production findings must be reviewed. Expected production Git calls are read-only.

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py \
  --output "./sandbox/reports/v3-1-6-canonical-tests.json" \
  --force
```

## Stop conditions

Stop before Git delivery if:

- `status` creates workspace or memory directories;
- any command performs network or Git mutation;
- private memory is read;
- changed filenames are emitted;
- focused or canonical tests fail;
- the public scope differs from the release manifest.
