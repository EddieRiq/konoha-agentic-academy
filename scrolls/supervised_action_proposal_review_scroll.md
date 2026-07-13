# Supervised Action Proposal Review Scroll

## Focused tests

```bash
python -m unittest discover \
  -s tests/action_proposal \
  -p "test_*.py"
```

## Proposed smoke

```bash
python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "examples/action_proposal/supervised_action_proposal.example.json" \
  --output "./sandbox/reports/v3-2-2-proposed.json" \
  --force \
  --json
```

Expected:

```text
exit code = 0
proposal_state = proposed
readiness = ready_for_approval_review
blockers = 0
```

## Blocked operation smoke

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path(
    "examples/action_proposal/"
    "supervised_action_proposal.example.json"
)
target = Path("sandbox/v3-2-2-blocked-operation.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["proposed_actions"][0]["operation"] = "apply_patch"
payload["proposed_actions"][0]["command_argv"] = [
    "python",
    "patch.py"
]
payload["proposed_actions"][0]["requires_approval"] = True

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "./sandbox/v3-2-2-blocked-operation.json" \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

Expected blockers include:

```text
action_operation_not_allowed
action_operation_blocked
```

## Shell-composition smoke

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path(
    "examples/action_proposal/"
    "supervised_action_proposal.example.json"
)
target = Path("sandbox/v3-2-2-shell-composition.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["proposed_actions"][1]["command_argv"] = [
    "grep",
    "-n",
    "v3.2",
    "README.md",
    "&&",
    "git",
    "status"
]

target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "./sandbox/v3-2-2-shell-composition.json" \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

Expected blocker:

```text
shell_composition_blocked
```

## Private path smoke

```bash
python - <<'PY'
import json
from pathlib import Path

source = Path(
    "examples/action_proposal/"
    "supervised_action_proposal.example.json"
)
target = Path("sandbox/v3-2-2-private-path.json")

payload = json.loads(source.read_text(encoding="utf-8"))
payload["affected_paths"].append("vault/private.json")
payload["proposed_actions"][0]["affected_paths"].append(
    "vault/private.json"
)

target.write_text(
    json.dumps(payload, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

set +e

python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "./sandbox/v3-2-2-private-path.json" \
  --json

RC=$?

set -e

test "$RC" -eq 1
```

## Output boundary

```bash
set +e

python tools/action_proposal/validate_supervised_action_proposal.py \
  --repo-root "." \
  --proposal "examples/action_proposal/supervised_action_proposal.example.json" \
  --output "./v3-2-2-unsafe-report.json" \
  --force \
  --json

RC=$?

set -e

test "$RC" -eq 2
test ! -e "./v3-2-2-unsafe-report.json"
```

## Production capability check

```bash
python - <<'PY'
import ast
from pathlib import Path

path = Path(
    "tools/action_proposal/"
    "validate_supervised_action_proposal.py"
)
tree = ast.parse(path.read_text(encoding="utf-8"))

blocked = {
    "subprocess",
    "requests",
    "urllib",
    "socket"
}
found = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            if root in blocked:
                found.add(root)
    elif isinstance(node, ast.ImportFrom) and node.module:
        root = node.module.split(".", 1)[0]
        if root in blocked:
            found.add(root)

if found:
    raise SystemExit(
        "blocked imports: " + ", ".join(sorted(found))
    )
PY
```

## Canonical gate

```bash
python tools/release_testing/run_release_tests.py \
  --output "./sandbox/reports/v3-2-2-canonical-tests.json" \
  --force
```

Expected:

```text
48 suites
347 tests
0 failures
0 errors
0 timeouts
```

## Stop conditions

Stop before Git delivery if:

- contract or evidence hashes are not verified;
- evidence source hashes are not rechecked;
- actions can cite missing or unresolved evidence;
- blocked operations or paths validate;
- shell composition passes;
- sensitive actions lack contract-declared approval requirements;
- state-changing actions omit rollback;
- irreversible actions validate;
- the validator imports subprocess or network modules;
- output escapes sandbox;
- focused or canonical tests fail;
- public scope differs from the package manifest.
