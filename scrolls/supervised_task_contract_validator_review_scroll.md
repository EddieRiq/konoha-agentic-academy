# Supervised Task Contract Validator Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/task_contract \
  -p "test_*.py"
```

## Ready-contract smoke

```bash
python tools/task_contract/validate_supervised_task_contract.py \
  --repo-root "." \
  --contract "examples/task_contract/supervised_task_contract.example.json" \
  --output "./sandbox/reports/v3-2-0-ready-contract.json" \
  --force \
  --json \
  > "./sandbox/reports/v3-2-0-ready-contract.stdout.json"
```

Expected:

```text
exit code = 0
status = passed
readiness = ready
blocker_count = 0
ready_does_not_authorize_execution = true
```

## Blocked-contract smoke

Create a sandbox copy and remove acceptance criteria:

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path("examples/task_contract/supervised_task_contract.example.json")
target = Path("sandbox/v3-2-0-blocked-contract.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["acceptance_criteria"] = []

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/task_contract/validate_supervised_task_contract.py \
  --repo-root "." \
  --contract "./sandbox/v3-2-0-blocked-contract.json" \
  --output "./sandbox/reports/v3-2-0-blocked-contract-report.json" \
  --force \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

Expected blocker:

```text
acceptance_criteria_invalid
```

## Security review

```bash
grep -RInE \
  'shell=True|subprocess|git (add|commit|push|tag|fetch)|gh |ollama|requests\.|urllib' \
  tools/task_contract/validate_supervised_task_contract.py \
  tests/task_contract/test_validate_supervised_task_contract.py \
  || true
```

Production validator must not invoke subprocesses.

## Output-boundary review

```bash
set +e

python tools/task_contract/validate_supervised_task_contract.py \
  --repo-root "." \
  --contract "examples/task_contract/supervised_task_contract.example.json" \
  --output "./v3-2-0-unsafe-report.json" \
  --force \
  --json

RC=$?

set -e

test "$RC" -eq 2
test ! -e "./v3-2-0-unsafe-report.json"
```

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py \
  --output "./sandbox/reports/v3-2-0-canonical-tests.json" \
  --force
```

## Stop conditions

Stop before Git delivery if:

- validator executes a command or subprocess;
- report output escapes sandbox;
- a protected path is accepted;
- a sensitive operation is ready without approval declaration;
- Teachback or review can be disabled;
- focused or canonical tests fail;
- public scope differs from the manifest.
