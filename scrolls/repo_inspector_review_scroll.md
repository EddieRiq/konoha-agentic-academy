# Repo Inspector Review Scroll

Status: v0.16.0 baseline.

This Scroll reviews the Read-only Repo Inspector before release or use in a runtime governance flow.

## Scope

Review:

- public scan allowlist;
- blocked private path rules;
- required artifact checks;
- private-boundary signal checks;
- Python risky-pattern checks;
- example non-execution checks;
- text and JSON report behavior;
- tests and fixtures;
- README, roadmap, changelog, guide, and examples references.

## Required evidence

A reviewer should see:

```powershell
python .\tools\repo_inspector\inspect_public_repo.py --repo-root "."
python .\tools\repo_inspector\inspect_public_repo.py --repo-root "." --json
python -m unittest discover -s .\tests\repo_inspector -p "test_*.py"
```

Expected result:

```text
REPO INSPECTION PASSED
Ran 6 tests
OK
```

Warnings are acceptable only if they are reviewed and explained.

## Safety checks

Confirm that the inspector does not use:

```text
subprocess
os.system
Popen
requests
socket
write_text
open(..., "w")
unlink
remove
```

Confirm that it does not:

- execute shell commands;
- call Git;
- modify files;
- repair files;
- invoke adapters;
- access private Village context;
- scan ignored local runtime outputs as public doctrine.

## Stop conditions

Stop and request revision if:

- the inspector writes files;
- the inspector executes commands;
- the inspector reads private or ignored folders;
- executable examples are accepted;
- missing required public artifacts are accepted;
- warnings are hidden from the user;
- JSON output omits safety boundaries;
- tests do not cover failure cases.

## Review outcome

Use one of:

```text
approved_for_release
revision_required
blocked
```

Approval means the inspector is safe as a read-only governance tool. It does not authorize runtime actions.
