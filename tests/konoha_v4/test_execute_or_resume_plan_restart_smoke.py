from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import konoha_v4 as _konoha_pkg
from tools.konoha_v4.executor import expected_approval_command, plan_identity
from tools.konoha_v4.models import AgentAssignment, MissionPlan

_WORKER = Path(__file__).resolve().parent / "_restart_smoke_worker.py"
# Anchored to the already-imported tools.konoha_v4 package location (not to
# this test file's own directory depth), so it resolves correctly whether
# this file lives at its final tests/konoha_v4/ path or is being validated
# from a scratch directory before being copied there.
_REPO_ROOT = Path(_konoha_pkg.__file__).resolve().parent.parent.parent


def _assignment(task_id="t1", execution_gate="plan_approval", **overrides):
    fields = dict(
        task_id=task_id,
        family="repository-auditor",
        provider="codex",
        model="codex",
        objective="Inspeccionar sin mutar.",
        inputs=["tools/konoha_v4"],
        expected_output="Evidencia verificable.",
        estimated_input_tokens=10,
        estimated_output_tokens=5,
        estimated_total_tokens=15,
        execution_gate=execution_gate,
    )
    fields.update(overrides)
    return AgentAssignment(**fields)


def _plan(assignments, mission_id="mission-restart-smoke", approval_status="approved"):
    return MissionPlan(
        mission_id=mission_id,
        understanding="Validar el smoke multiproceso de restart.",
        explicit_facts=[],
        missing_context=[],
        assumptions_prohibited=[],
        complexity="low",
        assignments=assignments,
        acceptance_criteria=["done"],
        approval_boundaries=["read_only", "mutation", "network", "private_context"],
        estimated_tokens=15 * len(assignments),
        estimated_cost_class="low",
        rationale="test",
        approval={
            "status": approval_status,
            "approved_by": "human" if approval_status == "approved" else None,
            "approved_at": "2026-07-21T00:00:00Z" if approval_status == "approved" else None,
            "feedback": None,
        },
    ).seal()


def _write_plan(state_dir: Path, plan: MissionPlan) -> None:
    mission_dir = state_dir / "missions" / plan.mission_id
    mission_dir.mkdir(parents=True, exist_ok=True)
    (mission_dir / "plan.json").write_text(
        json.dumps(dataclasses.asdict(plan), ensure_ascii=False, indent=2), encoding="utf-8",
    )


def _execution_state_path(state_dir: Path, mission_id: str) -> Path:
    return state_dir / "missions" / mission_id / "execution_state.json"


def _write_execution_state_raw(state_dir: Path, mission_id: str, **fields) -> None:
    from tools.konoha_v4.models import EXECUTION_STATE_SCHEMA_VERSION

    base = dict(
        schema_version=EXECUTION_STATE_SCHEMA_VERSION,
        mission_id=mission_id,
        plan_identity="0" * 64,
        status="in_progress",
        next_assignment_index=0,
        completed_task_ids=[],
        pending_task_id=None,
        pending_execution_gate=None,
        approval_nonce=None,
        active_approval_id=None,
        consumed_approval_ids=[],
        evidence_ids_by_task={},
        executing_task_id=None,
        pause_reason=None,
        diagnostic=None,
        updated_at="2026-07-21T00:00:00Z",
    )
    base.update(fields)
    path = _execution_state_path(state_dir, mission_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")


def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def _run_worker(state_dir: Path, mission_id: str, repo: Path, approval_json_file: str | None = None) -> dict:
    args = [sys.executable, str(_WORKER), str(state_dir), mission_id, str(repo)]
    if approval_json_file:
        args.append(approval_json_file)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_REPO_ROOT)
    env["TMPDIR"] = "/tmp"
    env["PYTHONPYCACHEPREFIX"] = "/tmp/konoha-pycache"
    completed = subprocess.run(
        args, cwd=str(_REPO_ROOT), env=env, capture_output=True, text=True, timeout=60,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"worker exited {completed.returncode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _invoke_call_count(state_dir: Path) -> int:
    log_path = state_dir / "invoke_calls.log"
    if not log_path.is_file():
        return 0
    return len([line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()])


class RestartSmokeTests(unittest.TestCase):
    def test_plan_approval_completes_and_restart_does_not_reinvoke(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], mission_id="mission-restart-smoke-a")
        with tempfile.TemporaryDirectory() as state_tmp, tempfile.TemporaryDirectory() as repo_tmp:
            state_dir = Path(state_tmp)
            repo = Path(repo_tmp)
            _init_git_repo(repo)
            _write_plan(state_dir, plan)

            process_a = _run_worker(state_dir, plan.mission_id, repo)
            self.assertEqual(process_a["state_status"], "completed")
            self.assertEqual(process_a["diagnostic"], "completed")
            self.assertEqual(_invoke_call_count(state_dir), 1)

            # Process B: a genuinely separate Python process, same on-disk
            # state_dir, simulating a restart after the mission finished.
            process_b = _run_worker(state_dir, plan.mission_id, repo)
            self.assertTrue(process_b["diagnostic"].startswith("non_resumable_status:"))
            self.assertEqual(_invoke_call_count(state_dir), 1)

    def test_separate_human_approval_waiting_is_idempotent_then_executes_once(self):
        task = _assignment(task_id="t1", execution_gate="separate_human_approval")
        plan = _plan([task], mission_id="mission-restart-smoke-b")
        with tempfile.TemporaryDirectory() as state_tmp, tempfile.TemporaryDirectory() as repo_tmp:
            state_dir = Path(state_tmp)
            repo = Path(repo_tmp)
            _init_git_repo(repo)
            _write_plan(state_dir, plan)

            process_a = _run_worker(state_dir, plan.mission_id, repo)
            self.assertEqual(process_a["state_status"], "waiting_for_approval")
            self.assertEqual(_invoke_call_count(state_dir), 0)
            nonce = process_a["approval_nonce"]
            identity = process_a["plan_identity"]
            self.assertIsNotNone(nonce)

            # Process B: separate process, no approval supplied - idempotent
            # re-poll, no mutation, no invocation.
            process_b = _run_worker(state_dir, plan.mission_id, repo)
            self.assertEqual(process_b["state_status"], "waiting_for_approval")
            self.assertEqual(process_b["approval_nonce"], nonce)
            self.assertEqual(_invoke_call_count(state_dir), 0)

            approval_text = expected_approval_command(plan.mission_id, "t1", identity, nonce)
            approval_payload = {
                "mission_id": plan.mission_id,
                "task_id": "t1",
                "execution_gate": "separate_human_approval",
                "plan_identity": identity,
                "approval_nonce": nonce,
                "approval_text": approval_text,
                "approval_source": "interactive_terminal",
                "approved_at": "2026-07-21T00:05:00Z",
            }
            approval_file = state_dir / "approval.json"
            approval_file.write_text(json.dumps(approval_payload), encoding="utf-8")

            # Process C: separate process, valid approval - executes exactly
            # once.
            process_c = _run_worker(state_dir, plan.mission_id, repo, str(approval_file))
            self.assertEqual(process_c["state_status"], "completed")
            self.assertEqual(_invoke_call_count(state_dir), 1)

    def test_inherited_executing_produces_recovery_required_without_invoke(self):
        task = _assignment(task_id="t1", execution_gate="plan_approval")
        plan = _plan([task], mission_id="mission-restart-smoke-c")
        with tempfile.TemporaryDirectory() as state_tmp, tempfile.TemporaryDirectory() as repo_tmp:
            state_dir = Path(state_tmp)
            repo = Path(repo_tmp)
            _init_git_repo(repo)
            _write_plan(state_dir, plan)

            # Simulate the exact crash window: "executing" was durably
            # persisted by a prior (now-dead) process, but invoke never ran
            # (or never finished) - no evidence file exists for t1.
            _write_execution_state_raw(
                state_dir, plan.mission_id,
                plan_identity=plan_identity(plan),
                status="executing",
                pending_task_id="t1", pending_execution_gate="plan_approval",
                executing_task_id="t1",
            )

            process_b = _run_worker(state_dir, plan.mission_id, repo)
            self.assertEqual(process_b["state_status"], "recovery_required")
            self.assertEqual(process_b["diagnostic"], "interrupted_while_executing")
            self.assertEqual(_invoke_call_count(state_dir), 0)


if __name__ == "__main__":
    unittest.main()
