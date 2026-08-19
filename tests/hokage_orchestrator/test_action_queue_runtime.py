import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator import authority
from tools.hokage_orchestrator import skill_runtime
from tools.hokage_orchestrator.skill_runtime import ActionQueue, RuntimeBridge

ROOT = Path(__file__).resolve().parents[2]


def _decision(mission_id: str) -> dict:
    return {
        "schema_version": authority.DECISION_SCHEMA_VERSION,
        "report_type": "hokage_mission_decision",
        "decision_id": f"decision-{mission_id}",
        "mission_id": mission_id,
        "selection": {
            "provider": "ollama",
            "model": "qwen2.5-coder:7b",
            "strategy": "local_only",
            "selection_source": "human_constraint_local_model_only",
        },
    }


def _charter(mission_id: str, decision: dict, *, proposed, followups=(), forbidden=()) -> dict:
    return {
        "schema_version": authority.CHARTER_SCHEMA_VERSION,
        "report_type": "conversational_mission_charter",
        "charter_id": f"charter-{mission_id}",
        "mission_id": mission_id,
        "state": "approved",
        "human_constraints": {
            "mutation_forbidden": False,
            "network_blocked": True,
            "local_model_only": True,
            "private_context_restricted": True,
        },
        "proposed_skills": list(proposed),
        "forbidden_skills": list(forbidden),
        "allowed_followup_skills": list(followups),
        "memory_write_allowed": False,
        "decision_id": decision["decision_id"],
        "decision_digest": authority.canonical_digest(decision),
        "approval_phrase": f"APROBAR CHARTER-{mission_id.upper()}",
    }


def _seed_authority(mission_dir: Path, mission_id: str, *, proposed, followups=(), forbidden=()):
    decision = _decision(mission_id)
    charter = _charter(mission_id, decision, proposed=proposed, followups=followups, forbidden=forbidden)
    authority.atomic_write_json(authority.mission_decision_path(mission_dir), decision)
    authority.atomic_write_json(authority.mission_charter_path(mission_dir), charter)
    authority.write_authority_receipt(
        mission_dir,
        mission_id=mission_id,
        charter=charter,
        decision=decision,
        approved_at=skill_runtime.utc_now(),
        approval_phrase=charter["approval_phrase"],
    )
    return charter, decision


class ActionQueueRuntimeTests(unittest.TestCase):
    def _mission_dir(self, root: Path, mission_id: str = "mission-1") -> Path:
        mission_dir = root / "missions" / mission_id
        mission_dir.mkdir(parents=True)
        return mission_dir

    def test_initialize_creates_only_proposed_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(
                mission_dir,
                "mission-1",
                proposed=["inspect_python_runtime", "inspect_git_status"],
            )
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            skills = [a["skill_id"] for a in payload["actions"]]
            self.assertEqual(skills, ["inspect_python_runtime", "inspect_git_status"])
            for action in payload["actions"]:
                self.assertEqual(action["tier"], "initial")
                self.assertEqual(action["status"], "proposed")

    def test_crash_between_claim_and_running_leaves_interrupted_claimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            skill_runtime._publish_execution_claim(
                mission_dir, action, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )

            candidates = queue.find_recovery_candidates()
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["action_id"], action["action_id"])
            self.assertEqual(candidates[0]["recovery_status"], "interrupted_claimed")

    def test_second_approval_of_claimed_action_fails_execution_already_claimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            skill_runtime._publish_execution_claim(
                mission_dir, action, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.approve_and_dispatch(
                    action["action_id"],
                    phrase=action["approval_phrase"],
                    approved_by="Eduardo",
                    dispatch=lambda a: {"ok": True},
                )
            self.assertEqual(ctx.exception.code, "execution_already_claimed")

            reloaded = queue.load()
            reloaded_action = next(
                a for a in reloaded["actions"] if a["action_id"] == action["action_id"]
            )
            self.assertEqual(reloaded_action["status"], "proposed")

    def test_corrupt_claim_fails_execution_claim_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            claim_path = skill_runtime._action_claim_path(mission_dir, action["action_id"])
            claim_path.parent.mkdir(parents=True, exist_ok=True)
            claim_path.write_text("not json", encoding="utf-8")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                skill_runtime.verify_execution_claim(mission_dir, action)
            self.assertEqual(ctx.exception.code, "execution_claim_invalid")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.approve_and_dispatch(
                    action["action_id"],
                    phrase=action["approval_phrase"],
                    approved_by="Eduardo",
                    dispatch=lambda a: {"ok": True},
                )
            self.assertEqual(ctx.exception.code, "execution_claim_invalid")

    def test_claim_with_wrong_binding_fails_execution_claim_binding_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(
                mission_dir,
                "mission-1",
                proposed=["inspect_python_runtime", "inspect_git_status"],
            )
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action_a, action_b = payload["actions"]

            claim_b = skill_runtime._publish_execution_claim(
                mission_dir, action_b, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )
            claim_a_path = skill_runtime._action_claim_path(mission_dir, action_a["action_id"])
            claim_a_path.parent.mkdir(parents=True, exist_ok=True)
            claim_a_path.write_text(
                json.dumps(claim_b, indent=2, sort_keys=True), encoding="utf-8"
            )

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                skill_runtime.verify_execution_claim(mission_dir, action_a)
            self.assertEqual(ctx.exception.code, "execution_claim_binding_mismatch")

    def test_running_without_claim_fails_execution_claim_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action_id = payload["actions"][0]["action_id"]

            raw = queue.load()
            for action in raw["actions"]:
                if action["action_id"] == action_id:
                    action["status"] = "running"
                    action["evidence"] = {
                        "approved_by": "Eduardo",
                        "approved_at": skill_runtime.utc_now(),
                        "arguments_hash": action["arguments_hash"],
                    }
            authority.atomic_write_json(queue.path, raw)

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.find_recovery_candidates()
            self.assertEqual(ctx.exception.code, "execution_claim_missing")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.restore()
            self.assertEqual(ctx.exception.code, "execution_claim_missing")

    def test_interrupted_claimed_action_only_closes_via_human_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            skill_runtime._publish_execution_claim(
                mission_dir, action, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.reject_action_checked(
                    action["action_id"],
                    phrase=action["rejection_phrase"],
                    expected_arguments_hash=action["arguments_hash"],
                )
            self.assertEqual(ctx.exception.code, "execution_already_claimed")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.approve_and_dispatch(
                    action["action_id"],
                    phrase=action["approval_phrase"],
                    approved_by="Eduardo",
                    dispatch=lambda a: {"ok": True},
                )
            self.assertEqual(ctx.exception.code, "execution_already_claimed")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.block_interrupted_action_checked(
                    action["action_id"],
                    phrase="WRONG PHRASE",
                    expected_arguments_hash=action["arguments_hash"],
                    reason="interrupted before dispatch",
                )
            self.assertEqual(ctx.exception.code, "approval_binding_mismatch")

            blocked = queue.block_interrupted_action_checked(
                action["action_id"],
                phrase=skill_runtime.interrupted_recovery_phrase(action["action_id"]),
                expected_arguments_hash=action["arguments_hash"],
                reason="interrupted before dispatch",
            )
            self.assertEqual(blocked["status"], "blocked")

            reloaded = queue.load()
            reloaded_action = next(
                a for a in reloaded["actions"] if a["action_id"] == action["action_id"]
            )
            self.assertEqual(reloaded_action["status"], "blocked")
            self.assertTrue(
                skill_runtime._action_claim_path(mission_dir, action["action_id"]).exists()
            )

    def test_duplicate_append_revalidates_exact_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(
                mission_dir,
                "mission-1",
                proposed=["inspect_python_runtime"],
                followups=["inspect_git_status"],
            )
            queue = ActionQueue(mission_dir)
            queue.initialize(mission_id="mission-1", plan_id="plan-1")

            first = queue.append_action_checked(
                mission_id="mission-1", plan_id="plan-1", skill_id="inspect_git_status"
            )
            second = queue.append_action_checked(
                mission_id="mission-1", plan_id="plan-1", skill_id="inspect_git_status"
            )
            self.assertEqual(first["action_id"], second["action_id"])
            self.assertEqual(first["arguments_hash"], second["arguments_hash"])

            payload = queue.load()
            matching = [a for a in payload["actions"] if a["action_id"] == first["action_id"]]
            self.assertEqual(len(matching), 1)

    def test_duplicate_append_with_tampered_content_fails_arguments_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(
                mission_dir,
                "mission-1",
                proposed=["inspect_python_runtime"],
                followups=["inspect_git_status"],
            )
            queue = ActionQueue(mission_dir)
            queue.initialize(mission_id="mission-1", plan_id="plan-1")

            first = queue.append_action_checked(
                mission_id="mission-1", plan_id="plan-1", skill_id="inspect_git_status"
            )

            raw = queue.load()
            for action in raw["actions"]:
                if action["action_id"] == first["action_id"]:
                    action["arguments"]["tampered"] = True
            authority.atomic_write_json(queue.path, raw)

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.append_action_checked(
                    mission_id="mission-1", plan_id="plan-1", skill_id="inspect_git_status"
                )
            self.assertEqual(ctx.exception.code, "arguments_hash_mismatch")

    def test_approve_and_dispatch_full_success_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            completed = queue.approve_and_dispatch(
                action["action_id"],
                phrase=action["approval_phrase"],
                approved_by="Eduardo",
                dispatch=lambda a: {"stdout": "3.11.0"},
            )
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(completed["evidence"]["result"], {"stdout": "3.11.0"})

            restored = queue.restore()
            restored_action = restored["actions"][0]
            self.assertEqual(restored_action["status"], "completed")

    def test_approve_and_dispatch_failure_marks_action_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            def boom(_action):
                raise RuntimeError("dispatch exploded")

            with self.assertRaises(RuntimeError):
                queue.approve_and_dispatch(
                    action["action_id"],
                    phrase=action["approval_phrase"],
                    approved_by="Eduardo",
                    dispatch=boom,
                )

            reloaded = queue.load()
            reloaded_action = next(
                a for a in reloaded["actions"] if a["action_id"] == action["action_id"]
            )
            self.assertEqual(reloaded_action["status"], "failed")

    def test_legacy_schema_queue_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = self._mission_dir(root)
            _seed_authority(mission_dir, "mission-1", proposed=["inspect_python_runtime"])
            queue = ActionQueue(mission_dir)

            legacy_payload = {
                "schema_version": "1.0.0",
                "report_type": "conversational_action_queue",
                "mission_id": "mission-1",
                "plan_id": "plan-1",
                "actions": [],
            }
            authority.atomic_write_json(queue.path, legacy_payload)

            self.assertEqual(queue.load()["schema_version"], "1.0.0")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.restore()
            self.assertEqual(ctx.exception.code, "charter_schema_migration_required")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.append_action_checked(
                    mission_id="mission-1", plan_id="plan-1", skill_id="inspect_git_status"
                )
            self.assertEqual(ctx.exception.code, "charter_schema_migration_required")

    def test_no_public_update_save_or_append_action(self):
        queue = ActionQueue(Path("/tmp/does-not-matter"))
        self.assertFalse(hasattr(queue, "update"))
        self.assertFalse(hasattr(queue, "save"))
        self.assertFalse(hasattr(queue, "append_action"))


class RuntimeBridgeOrchestratorFailClosedTests(unittest.TestCase):
    def test_execute_rejects_orchestrator_skill_before_subprocess(self):
        bridge = RuntimeBridge(ROOT)

        action = skill_runtime.make_action(
            mission_id="mission-1",
            plan_id="plan-1",
            skill_id="run_deterministic_audit_checks",
            arguments={},
        )

        with tempfile.TemporaryDirectory() as workspace:
            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                bridge.execute(
                    workspace_root=Path(workspace),
                    action=action,
                )
        self.assertEqual(ctx.exception.code, "skill_forbidden")


if __name__ == "__main__":
    unittest.main()
