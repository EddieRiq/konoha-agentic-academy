# Unified Supervised Release Gate Review Scroll

## 1. Base state

```bash
git status --short
git log --oneline --decorate -5
git tag -l --sort=-v:refname | head -5
git branch --show-current
```

Confirm:

```text
main
expected base commit
previous tag targets base
origin/main aligned
no existing target tag
clean tracked base before extraction
```

## 2. Package integrity

```bash
sha256sum -c \
  sandbox/tmp/v3-2-3-package/SHA256SUMS
```

## 3. Focused tests

```bash
python -m unittest discover \
  -s tests/release_workflow \
  -p "test_*.py"
```

Expected:

```text
14 tests
0 failures
0 errors
```

## 4. Static capability review

```bash
python - <<'PY'
import ast
from pathlib import Path

path = Path(
    "tools/release_workflow/run_supervised_release.py"
)
tree = ast.parse(path.read_text(encoding="utf-8"))

blocked = {
    "eval",
    "exec",
}

found = set()

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in blocked:
                found.add(node.func.id)

if found:
    raise SystemExit(
        "blocked calls: " + ", ".join(sorted(found))
    )
PY
```

The orchestrator may import `subprocess` because bounded command execution is its explicit purpose. Review every command construction and confirm:

```text
shell=False
argv arrays
known tool paths
no plan-provided arbitrary command
no force flags
no tag delete
no release delete
```

## 5. Plan review

Inspect:

```bash
python -m json.tool \
  examples/release_workflow/supervised_release_workflow_plan.example.json
```

Confirm:

- expected base is v3.2.2;
- target is v3.2.3;
- public scope contains exactly 16 paths;
- release notes hash matches;
- expected tests are 49 suites / 361 tests;
- all authority flags are true.

## 6. Unified run

Run the single supervised block supplied with the package.

Expected minimal output:

```text
KONOHA UNIFIED SUPERVISED RELEASE GATE
version: v3.2.3
status_code: RELEASE_CLOSED
head: <commit>
tag_target: <same commit>
release: <GitHub URL>
tests: 49/49 suites, 361 tests
tracking: 0 behind / 0 ahead
working_tree: clean
UNIFIED SUPERVISED RELEASE GATE PASSED
```

## 7. Expected transition evidence

The final report should include some or all of:

```text
BLOCKED_BRANCH_NOT_SYNCED → push_main
NEEDS_TAG_CREATION → create_tag
NEEDS_TAG_PUBLICATION → push_tag
NEEDS_RELEASE_PUBLICATION → publish_release
NEEDS_LATEST_PROMOTION → promote_latest
RELEASE_CLOSED → complete
```

`NEEDS_LATEST_PROMOTION` may be absent when release creation already marks the release Latest.

## 8. Stop conditions

Stop immediately if:

- base, branch or previous tag differ;
- scope differs from 16 paths;
- release notes hash differs;
- focused tests fail;
- canonical counts differ;
- an unexpected closure state appears;
- the branch is behind remote;
- the branch is ahead by more than the expected release commit;
- a local or remote tag points elsewhere;
- an existing release has a different title or tag;
- GitHub authentication fails;
- any force, delete or rewrite operation appears;
- final direct verification differs from the guard.

## 9. Evidence doctrine

```text
Expected RC alone is not permission.
Expected status alone is not permission.
Both must match the state machine.
Tests are evidence only.
Guard reports are evidence only.
Explicit tokens authorize only the named operation.
RELEASE_CLOSED requires direct verification.
```
