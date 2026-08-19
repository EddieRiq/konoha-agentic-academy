import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator import authority
from tools.hokage_orchestrator import charter as charter_module
from tools.hokage_orchestrator import mission_decision
from tools.hokage_orchestrator import skill_runtime
from tools.hokage_orchestrator.skill_runtime import ActionQueue

INTENT_IMPLEMENT = {
    "schema_version": "1.0.0",
    "report_type": "conversational_intent",
    "intent_type": "implement_change",
    "objective": "fix the failing audit checks",
    "targets": ["/repo"],
    "constraints": [],
    "requested_outputs": ["patch_proposal", "test_evidence"],
    "missing_context": [],
    "risk_level": "medium",
    "requires_charter": True,
    "authority": {
        "intent_is_not_permission": True,
        "model_output_is_evidence_only": True,
        "explicit_approval_required": True,
    },
}

READY_SNAPSHOT = {
    "providers": [
        {"provider": "codex", "status": "ready"},
        {"provider": "ollama", "status": "ready"},
    ]
}

OLLAMA_ONLY_SNAPSHOT = {
    "providers": [
        {"provider": "codex", "status": "not_ready"},
        {"provider": "ollama", "status": "ready"},
    ]
}

HUMAN_CONSTRAINTS = {
    "mutation_forbidden": False,
    "network_blocked": False,
    "local_model_only": False,
    "private_context_restricted": True,
}


def _mission_dir(root: Path, mission_id: str = "mission-1") -> Path:
    mission_dir = root / "missions" / mission_id
    mission_dir.mkdir(parents=True)
    return mission_dir


def _build_and_approve(root: Path, mission_id: str = "mission-1", *, snapshot=READY_SNAPSHOT):
    mission_dir = _mission_dir(root, mission_id)
    decision = mission_decision.build_decision_1_1(
        mission_id=mission_id,
        intent=INTENT_IMPLEMENT,
        bootstrap_snapshot=snapshot,
        local_model="qwen2.5-coder:7b",
        human_constraints=HUMAN_CONSTRAINTS,
        provider_skill_id="invoke_local_model_audit",
    )
    charter = charter_module.build_charter_1_1(
        INTENT_IMPLEMENT,
        decision,
        actor="Eduardo",
        human_constraints=HUMAN_CONSTRAINTS,
    )
    approved = charter_module.approve_charter_1_1(
        mission_dir,
        charter,
        decision,
        approval_phrase=charter["approval_phrase"],
        approved_by="Eduardo",
    )
    return mission_dir, charter, decision, approved


class MissionDecisionTests(unittest.TestCase):
    def test_decision_1_1_is_valid_and_binds_selection_source(self):
        decision = mission_decision.build_decision_1_1(
            mission_id="mission-1",
            intent=INTENT_IMPLEMENT,
            bootstrap_snapshot=READY_SNAPSHOT,
            local_model="qwen2.5-coder:7b",
            human_constraints=HUMAN_CONSTRAINTS,
            provider_skill_id="invoke_local_model_audit",
        )
        self.assertEqual(decision["schema_version"], "1.1.0")
        self.assertEqual(decision["selection"]["provider"], "ollama")
        self.assertIn("selection_source", decision["selection"])
        # Full shape acceptance is delegated to authority.py's own
        # validator - the real, single source of truth for this shape.
        authority._validate_decision_shape(decision)

    def test_provider_skill_governs_candidate_providers(self):
        # invoke_local_model_audit is ollama-only, regardless of codex
        # readiness or category - never a candidate substitution.
        decision = mission_decision.build_decision_1_1(
            mission_id="mission-1",
            intent=INTENT_IMPLEMENT,
            bootstrap_snapshot=READY_SNAPSHOT,
            local_model="qwen2.5-coder:7b",
            human_constraints=HUMAN_CONSTRAINTS,
            provider_skill_id="invoke_local_model_audit",
        )
        self.assertEqual(decision["selection"]["provider"], "ollama")

    def test_no_compatible_provider_fails_closed_before_charter(self):
        with self.assertRaises(mission_decision.ProviderSelectionError):
            mission_decision.build_decision_1_1(
                mission_id="mission-1",
                intent=INTENT_IMPLEMENT,
                bootstrap_snapshot={"providers": [{"provider": "codex", "status": "ready"}]},
                local_model="qwen2.5-coder:7b",
                human_constraints=HUMAN_CONSTRAINTS,
                provider_skill_id="invoke_local_model_audit",
            )

    def test_malformed_human_constraints_fail_closed(self):
        bad = dict(HUMAN_CONSTRAINTS)
        bad["mutation_forbidden"] = "no"  # not an exact bool
        with self.assertRaises(mission_decision.ProviderSelectionError):
            mission_decision.select_provider_and_model_1_1(
                mission_decision.classify_mission(INTENT_IMPLEMENT),
                READY_SNAPSHOT,
                human_constraints=bad,
                local_model="qwen2.5-coder:7b",
                provider_skill_id="invoke_local_model_audit",
            )

        missing = {k: v for k, v in HUMAN_CONSTRAINTS.items() if k != "network_blocked"}
        with self.assertRaises(mission_decision.ProviderSelectionError):
            mission_decision.select_provider_and_model_1_1(
                mission_decision.classify_mission(INTENT_IMPLEMENT),
                READY_SNAPSHOT,
                human_constraints=missing,
                local_model="qwen2.5-coder:7b",
                provider_skill_id="invoke_local_model_audit",
            )


class CharterTests(unittest.TestCase):
    def test_charter_1_1_binds_exactly_the_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)
            self.assertEqual(charter["decision_id"], decision["decision_id"])
            self.assertEqual(charter["decision_digest"], authority.canonical_digest(decision))
            self.assertTrue(set(charter["proposed_skills"]) <= set(skill_runtime.SKILLS))

    def test_receipt_is_write_once_and_second_approval_never_mutates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)

            decision_path = authority.mission_decision_path(mission_dir)
            charter_path = authority.mission_charter_path(mission_dir)
            receipt_path = authority.mission_authority_receipt_path(mission_dir)

            decision_bytes = decision_path.read_bytes()
            charter_bytes = charter_path.read_bytes()
            receipt_bytes = receipt_path.read_bytes()

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                charter_module.approve_charter_1_1(
                    mission_dir,
                    charter,  # the original, still schema-"proposed" object
                    decision,
                    approval_phrase=charter["approval_phrase"],
                    approved_by="Eduardo",
                )
            self.assertEqual(ctx.exception.code, "authority_receipt_invalid")

            self.assertEqual(decision_path.read_bytes(), decision_bytes)
            self.assertEqual(charter_path.read_bytes(), charter_bytes)
            self.assertEqual(receipt_path.read_bytes(), receipt_bytes)

    def test_approve_requires_matching_human_typed_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = _mission_dir(root)
            decision = mission_decision.build_decision_1_1(
                mission_id="mission-1",
                intent=INTENT_IMPLEMENT,
                bootstrap_snapshot=READY_SNAPSHOT,
                local_model="qwen2.5-coder:7b",
                human_constraints=HUMAN_CONSTRAINTS,
                provider_skill_id="invoke_local_model_audit",
            )
            charter = charter_module.build_charter_1_1(
                INTENT_IMPLEMENT, decision, actor="Eduardo", human_constraints=HUMAN_CONSTRAINTS
            )
            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                charter_module.approve_charter_1_1(
                    mission_dir,
                    charter,
                    decision,
                    approval_phrase="WRONG PHRASE",
                    approved_by="Eduardo",
                )
            self.assertEqual(ctx.exception.code, "approval_binding_mismatch")
            self.assertFalse(authority.mission_charter_path(mission_dir).exists())

    def test_modifying_charter_after_approval_invalidates_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)

            charter_path = authority.mission_charter_path(mission_dir)
            tampered = json.loads(charter_path.read_text(encoding="utf-8"))
            tampered["proposed_skills"] = list(tampered["proposed_skills"]) + [
                "apply_validated_patch"
            ]
            charter_path.write_text(json.dumps(tampered), encoding="utf-8")

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                authority.load_authoritative_state(mission_dir)
            self.assertEqual(ctx.exception.code, "charter_immutable_violation")

    def test_modifying_decision_after_approval_invalidates_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)

            decision_path = authority.mission_decision_path(mission_dir)
            tampered_decision = json.loads(decision_path.read_text(encoding="utf-8"))
            tampered_decision["selection"]["model"] = "some-other-model"
            decision_path.write_text(json.dumps(tampered_decision), encoding="utf-8")

            # Isolate the receipt-based immutability check directly via
            # authority.py's own public helper, using the untouched
            # in-memory approved charter (mission_charter.json was never
            # written to) against the tampered decision now on disk. This
            # exercises exactly the Decision-vs-receipt property, without
            # depending on load_authoritative_state()'s internal
            # validation order, which would instead surface its earlier
            # charter<->decision cross-check for this same tamper.
            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                authority.verify_authority_receipt(
                    mission_dir, charter=approved, decision=tampered_decision
                )
            self.assertEqual(ctx.exception.code, "decision_immutable_violation")

            # The end-to-end public entry point still fails closed too -
            # via whichever check fires first; that ordering is an
            # internal detail this test does not pin down.
            with self.assertRaises(authority.AuthorityBindingError):
                authority.load_authoritative_state(mission_dir)


class ActionQueueAuthorityGateTests(unittest.TestCase):
    def test_action_queue_does_not_start_before_approval_and_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir = _mission_dir(root)
            queue = ActionQueue(mission_dir)
            with self.assertRaises(authority.AuthorityBindingError):
                queue.initialize(mission_id="mission-1", plan_id="plan-1")

    def test_only_proposed_skills_generate_initial_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            skill_ids = {a["skill_id"] for a in payload["actions"]}
            self.assertEqual(skill_ids, set(approved["proposed_skills"]))
            for skill_id in skill_ids:
                self.assertNotIn(skill_id, approved["forbidden_skills"])

    def test_legacy_action_queue_cannot_be_started_via_initialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)
            queue = ActionQueue(mission_dir)

            legacy_payload = {
                "schema_version": "1.0.0",
                "report_type": "conversational_action_queue",
                "mission_id": "mission-1",
                "plan_id": "plan-1",
                "actions": [],
            }
            authority.atomic_write_json(queue.path, legacy_payload)

            with self.assertRaises(authority.AuthorityBindingError) as ctx:
                queue.initialize(mission_id="mission-1", plan_id="plan-1")
            self.assertEqual(ctx.exception.code, "charter_schema_migration_required")
            # And the legacy file was never overwritten by initialize().
            self.assertEqual(
                json.loads(queue.path.read_text(encoding="utf-8"))["schema_version"], "1.0.0"
            )


class ActionArgumentsHashTests(unittest.TestCase):
    def test_arguments_hash_changes_with_plan_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_dir, charter, decision, approved = _build_and_approve(root)

            action_plan_1 = skill_runtime._build_action(
                mission_id="mission-1",
                plan_id="plan-1",
                skill_id="inspect_python_runtime",
                tier="initial",
                charter=approved,
                decision=decision,
            )
            action_plan_2 = skill_runtime._build_action(
                mission_id="mission-1",
                plan_id="plan-2",
                skill_id="inspect_python_runtime",
                tier="initial",
                charter=approved,
                decision=decision,
            )
            self.assertNotEqual(action_plan_1["arguments_hash"], action_plan_2["arguments_hash"])
            self.assertNotEqual(action_plan_1["action_id"], action_plan_2["action_id"])


if __name__ == "__main__":
    unittest.main()
