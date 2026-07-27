"""Multiprocess restart-smoke worker for execute_or_resume_plan.

Not a test_*.py file - unittest discover never collects it as its own
suite. Invoked as a standalone subprocess (its own fresh Python
interpreter) by test_execute_or_resume_plan_restart_smoke.py, sharing only
a real on-disk state_dir with the parent test and with any sibling worker
invocations - never mocks of _load_execution_state or _save_execution_state,
and never anything shared in memory across processes.

Makes exactly one execute_or_resume_plan call, then prints a single JSON
line describing the resulting ExecutionAttempt to stdout.

Usage:
    python _restart_smoke_worker.py STATE_DIR MISSION_ID REPO [APPROVAL_JSON_FILE]

The provider (invoke) is faked deterministically here, inside this
process, by direct module-attribute reassignment (not unittest.mock, which
cannot cross a process boundary) - every fake call appends one line to
STATE_DIR/invoke_calls.log, which is how the parent test counts
invocations across process boundaries. _git_status is not faked: REPO is a
real temporary git repository, so the real git subprocess call runs
unmodified.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from tools.konoha_v4 import executor as executor_module
from tools.konoha_v4.executor import execute_or_resume_plan
from tools.konoha_v4.models import AssignmentApproval


class _Registry:
    def agent_family(self, family: str) -> dict:
        return {"allowed_task_patterns": ["read-only inspection"]}


def _install_fake_invoke(state_dir: Path) -> None:
    log_path = state_dir / "invoke_calls.log"

    def _fake_invoke(provider, prompt, *, cwd, model="provider_default"):
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"{provider}:{model}\n")
        return SimpleNamespace(text="ok", usage={"input": 1, "output": 1}, command=["echo", "ok"])

    executor_module.invoke = _fake_invoke


def main() -> int:
    state_dir = Path(sys.argv[1])
    mission_id = sys.argv[2]
    repo = Path(sys.argv[3])
    approval_json_file = sys.argv[4] if len(sys.argv) > 4 else None

    _install_fake_invoke(state_dir)

    approval = None
    if approval_json_file:
        raw = json.loads(Path(approval_json_file).read_text(encoding="utf-8"))
        approval = AssignmentApproval(**raw)

    attempt = execute_or_resume_plan(repo, state_dir, mission_id, _Registry(), approval=approval)

    result = {
        "state_status": attempt.state.status if attempt.state is not None else None,
        "diagnostic": attempt.diagnostic,
        "evidence_count": len(attempt.evidence),
        "pending_task_id": getattr(attempt.state, "pending_task_id", None),
        "pending_execution_gate": getattr(attempt.state, "pending_execution_gate", None),
        "approval_nonce": getattr(attempt.state, "approval_nonce", None),
        "plan_identity": getattr(attempt.state, "plan_identity", None),
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
