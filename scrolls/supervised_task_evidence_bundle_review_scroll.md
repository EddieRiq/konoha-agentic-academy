# Supervised Task Evidence Bundle Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/task_evidence \
  -p "test_*.py"
```

## Complete bundle smoke

```bash
python tools/task_evidence/validate_supervised_task_evidence.py \
  --repo-root "." \
  --bundle "examples/task_evidence/supervised_task_evidence_bundle.example.json" \
  --output "./sandbox/reports/v3-2-1-complete-evidence.json" \
  --force \
  --json
```

Expected:

```text
exit code = 0
status = passed
readiness = ready_for_human_review
evidence_state = complete
requirements = 3/3
blockers = 0
```

## Incomplete bundle smoke

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path(
    "examples/task_evidence/"
    "supervised_task_evidence_bundle.example.json"
)
target = Path("sandbox/v3-2-1-incomplete-evidence.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["evidence_items"][1]["status"] = "missing"
payload["evidence_items"][1]["source_refs"] = []
payload["claims"] = []
payload["unresolved"] = [
    {
        "unresolved_id": "missing-check-results",
        "statement": "Deterministic check results are missing.",
        "reason": "No result source was recorded.",
        "requirement_indices": [1]
    }
]

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/task_evidence/validate_supervised_task_evidence.py \
  --repo-root "." \
  --bundle "./sandbox/v3-2-1-incomplete-evidence.json" \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

Expected:

```text
evidence_state = incomplete
readiness = blocked
```

## Hash mismatch smoke

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path(
    "examples/task_evidence/"
    "supervised_task_evidence_bundle.example.json"
)
target = Path("sandbox/v3-2-1-bad-hash-evidence.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["evidence_items"][0]["source_refs"][0]["sha256"] = "0" * 64

target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/task_evidence/validate_supervised_task_evidence.py \
  --repo-root "." \
  --bundle "./sandbox/v3-2-1-bad-hash-evidence.json" \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

Expected blocker:

```text
source_sha256_mismatch
```

## Security review

```bash
grep -nE \
  'subprocess|shell=True|os\.system|git (add|commit|push|tag|fetch)|gh |ollama|requests\.|urllib' \
  tools/task_evidence/validate_supervised_task_evidence.py \
  && exit 1 || true
```

The production validator must not execute subprocesses.

## Output-boundary review

```bash
set +e

python tools/task_evidence/validate_supervised_task_evidence.py \
  --repo-root "." \
  --bundle "examples/task_evidence/supervised_task_evidence_bundle.example.json" \
  --output "./v3-2-1-unsafe-report.json" \
  --force \
  --json

RC=$?

set -e

test "$RC" -eq 2
test ! -e "./v3-2-1-unsafe-report.json"
```

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py \
  --output "./sandbox/reports/v3-2-1-canonical-tests.json" \
  --force
```

Expected after adding the focused suite:

```text
47 suites
335 tests
0 failures
0 errors
0 timeouts
```

## Stop conditions

Stop before Git delivery if:

- source or contract hashes are not checked;
- a requirement can be omitted or duplicated;
- private paths can be read;
- a supported claim can rely on missing evidence;
- incomplete evidence lacks an unresolved explanation;
- output escapes sandbox;
- the validator invokes a subprocess;
- complete evidence is represented as execution permission;
- focused or canonical tests fail;
- public scope differs from the package manifest.
