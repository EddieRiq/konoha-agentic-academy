# Hokage Shell Mission Continuity Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/hokage_shell \
  -p "test_*.py"
```

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py
```

## Mission continuity smoke

Use an isolated sandbox workspace:

```bash
WORKSPACE="./sandbox/hokage-shell-v3-1-5-smoke"

python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "$WORKSPACE" \
  --memory-root "./sandbox/hokage-shell-v3-1-5-private-memory" \
  --no-animation \
  smoke \
  --task "Validate v3.1.5 mission continuity." \
  --mission-id "v3-1-5-continuity-smoke" \
  --json \
  > "./sandbox/reports/v3-1-5-hokage-smoke.json"

python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "$WORKSPACE" \
  missions \
  --json \
  > "./sandbox/reports/v3-1-5-missions.json"

python tools/hokage_shell/run_hokage_shell.py \
  --repo-root "." \
  --workspace-root "$WORKSPACE" \
  resume \
  --latest \
  --json \
  > "./sandbox/reports/v3-1-5-resume.json"
```

Validate:

```bash
jq '{
  status,
  mode,
  latest_mission_id,
  mission_count,
  invalid_mission_count
}' ./sandbox/reports/v3-1-5-missions.json

jq '{
  status,
  mission_id,
  continuity,
  boundaries,
  authority
}' ./sandbox/reports/v3-1-5-resume.json
```

Expected:

```text
missions status: passed
mission_count: 1
invalid_mission_count: 0
resume status: passed
mission_id: v3-1-5-continuity-smoke
memory_is_not_read: true
resume_does_not_authorize_execution: true
```

## Security review

```bash
grep -RInE \
  'shell=True|git (add|commit|push|tag)|gh release|ollama|memory/obsidian' \
  tools/hokage_shell/mission_continuity.py \
  tests/hokage_shell/test_mission_continuity.py \
  || true
```

Review findings manually. Test fixtures may contain private-memory-like path strings, but production continuity code must not read those paths.

## Stop conditions

Stop before Git delivery if:

- a malformed session is selected as latest;
- mission ids can escape the workspace;
- resume invokes tools, models, network or Git;
- resume reads private memory;
- working tree changes after a read-only smoke;
- JSON reports fail syntax validation;
- focused or canonical tests fail.
