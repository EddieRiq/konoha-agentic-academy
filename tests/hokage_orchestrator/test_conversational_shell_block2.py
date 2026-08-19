import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator import authority
from tools.hokage_orchestrator.audit_flow import (
    AuditFlowError,
    canonical_json,
    sha256_text,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "tools"
    / "hokage_orchestrator"
    / "run_conversational_hokage.py"
)


def load_script():
    spec = importlib.util.spec_from_file_location(
        "run_conversational_hokage_block2",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def reject_until(shell, action, target_skill_id):
    """Walk the queue rejecting every action until target_skill_id is
    reached, never approving anything - avoids ever dispatching
    run_deterministic_audit_checks (which shells out to
    `python -m unittest discover -s tests/hokage_orchestrator` and would
    recursively re-run this very suite) or invoke_local_model_audit
    (needs a live Ollama-backed audit tool this sandbox doesn't have)."""

    while action["skill_id"] != target_skill_id:
        result = shell.reject_action(action, action["rejection_phrase"])
        assert result["status"] == "passed", result
        action = result["next_action"]
    return action


class ConversationalShellBlock2Tests(unittest.TestCase):
    def setUp(self):
        self.module = load_script()

    def make_shell(self, root: Path):
        return self.module.ConversationalHokage(
            repo_root=ROOT,
            workspace_root=root / "workspace",
            state_root=root / "runtime",
            memory_root=root / "obsidian",
            actor="Eduardo",
        )

    def test_full_mission_flow_and_resume_preserve_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)

            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            self.assertEqual(proposal["status_code"], "CHARTER_PROPOSED")
            mission_id = proposal["mission_id"]
            mission_dir = shell.mission_dir(mission_id)

            # Decision 1.1 and the proposed Charter are on disk before
            # approval, but no receipt exists yet.
            self.assertTrue(authority.mission_decision_path(mission_dir).exists())
            self.assertTrue(authority.mission_charter_path(mission_dir).exists())
            self.assertFalse(
                authority.mission_authority_receipt_path(mission_dir).exists()
            )

            approved = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            self.assertEqual(
                approved["status_code"], "CHARTER_APPROVED_ACTIONS_PROPOSED"
            )
            # The single event that turns a proposal into real authority.
            self.assertTrue(
                authority.mission_authority_receipt_path(mission_dir).exists()
            )

            first = approved["next_action"]
            self.assertEqual(first["skill_id"], "inspect_python_runtime")
            first_result = shell.approve_action(first, first["approval_phrase"])
            self.assertEqual(first_result["status_code"], "ACTION_COMPLETED")

            second = first_result["next_action"]
            self.assertEqual(second["skill_id"], "inspect_git_status")
            rejected = shell.reject_action(second, second["rejection_phrase"])
            self.assertEqual(rejected["status_code"], "ACTION_REJECTED")

            # A fresh process/shell instance, from the same directories,
            # must reconstruct the same state - only from the persisted
            # truth source.
            resumed = self.make_shell(root)
            self.assertIsNone(resumed.resume_diagnostic)
            status = resumed.status_payload()
            actions_by_id = {
                a["action_id"]: a for a in status["action_queue"]["actions"]
            }
            self.assertEqual(
                actions_by_id[first["action_id"]]["status"], "completed"
            )
            self.assertEqual(
                actions_by_id[second["action_id"]]["status"], "rejected"
            )
            # No auto-dispatch on resume: the remaining pending actions
            # are still exactly "proposed", never advanced by restore().
            remaining = [
                a
                for a in status["action_queue"]["actions"]
                if a["action_id"] not in (first["action_id"], second["action_id"])
            ]
            self.assertTrue(remaining)
            self.assertTrue(
                all(a["status"] == "proposed" for a in remaining)
            )

    def test_resume_with_interrupted_claim_reports_recovery_no_auto_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            approved = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = approved["next_action"]

            # Simulate a crash right after a claim was published but
            # before the CAS to running ever happened - by publishing the
            # claim directly, bypassing approve_and_dispatch().
            from tools.hokage_orchestrator import skill_runtime

            mission_dir = shell.mission_dir(proposal["mission_id"])
            skill_runtime._publish_execution_claim(
                mission_dir,
                action,
                approved_by="Eduardo",
                approved_at=skill_runtime.utc_now(),
            )

            resumed = self.make_shell(root)
            status = resumed.status_payload()
            recovery = status["recovery"]
            self.assertIsNotNone(recovery)
            matching = [
                c for c in recovery if c["action_id"] == action["action_id"]
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["recovery_status"], "interrupted_claimed")

            # Still exactly "proposed" - restore() never auto-dispatches.
            actions_by_id = {
                a["action_id"]: a for a in status["action_queue"]["actions"]
            }
            self.assertEqual(
                actions_by_id[action["action_id"]]["status"], "proposed"
            )

            # A normal approval attempt on the same action_id must fail
            # closed as a recovery case, never a plain phrase mismatch,
            # and never silently retry.
            retry = resumed.approve_action(action, action["approval_phrase"])
            self.assertEqual(retry["status_code"], "RECOVERY_REQUIRED")

    def test_render_action_works_on_a_real_1_1_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            approved = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = approved["next_action"]
            text = self.module.render_action(action)
            self.assertIn(action["action_id"], text)
            self.assertIn("Mutación:", text)
            self.assertIn("Red:", text)
            self.assertIn("Contexto privado:", text)

    def test_patch_action_approval_is_bound_to_patch_sha256(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            # "patch" makes real_allowed_followup_skills() include
            # apply_validated_patch/run_post_patch_tests; "revisá" still
            # drives intent_type to inspect_and_review so the audit
            # sequence (and reject_until) works the same as other tests.
            # No "no modifi..." wording here - that would set
            # human_constraints.mutation_forbidden=True, which charter
            # construction correctly rejects for a mutates_files=True
            # followup like apply_validated_patch.
            proposal = shell.one_shot(
                "Revisá este repositorio y preparar un patch de "
                "documentación."
            )
            approved = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = reject_until(
                shell, approved["next_action"], "invoke_local_model_audit"
            )

            # Isolate the actual patch target from the real working
            # tree: RealSupervisedAuditFlow.apply_patch() operates
            # against repo_root, and this is a negative test - if the
            # sha256 gate ever regressed, it must never be able to touch
            # ROOT/README.md. Swap shell.audit_flow for one bound to an
            # isolated temp repo (same pattern as test_real_supervised_
            # audit_flow.py's make_flow()), keeping the real mission_dir/
            # mission_id so the actual queue state stays consistent.
            isolated_repo = root / "isolated_repo"
            isolated_repo.mkdir()
            readme_path = isolated_repo / "README.md"
            readme_path.write_text("# Isolated test repo\n", encoding="utf-8")
            tool_path = (
                isolated_repo
                / "tools"
                / "local_model_audit"
                / "manage_local_model_audit.py"
            )
            tool_path.parent.mkdir(parents=True)
            tool_path.write_text("# placeholder\n", encoding="utf-8")

            mission_id = proposal["mission_id"]
            flow = self.module.RealSupervisedAuditFlow(
                repo_root=isolated_repo,
                workspace_root=shell.workspace_root,
                mission_dir=shell.mission_dir(mission_id),
                memory_root=shell.memory_root,
                mission_id=mission_id,
                actor="Eduardo",
                model=shell.local_model,
            )
            shell.audit_flow = flow

            # Build a real, deterministic patch proposal against the
            # isolated repo using the same helpers RealSupervisedAudit
            # Flow.run_model_audit() itself uses
            # (_rc_issue_and_operation()/_patch_preview()) - no Ollama
            # involved.
            issue, operation = flow._rc_issue_and_operation()
            self.assertIsNotNone(operation)
            operations = [operation]
            preview = flow._patch_preview(operations)
            material = {
                "mission_id": flow.mission_id,
                "operations": operations,
                "preview": preview,
            }
            digest = sha256_text(canonical_json(material))

            patch_plan = {
                "schema_version": "1.0.0",
                "report_type": "local_repo_patch_plan",
                "generated_at": self.module.utc_now(),
                "mission_id": flow.mission_id,
                "authority": {
                    "patch_plan_is_not_permission": True,
                    "apply_requires_separate_approval": True,
                    "patch_plan_uses_validated_issues_only": True,
                    "git_operations_are_not_authorized": True,
                },
                "summary": "Test-constructed validated patch plan.",
                "issues_considered": [issue],
                "operations": operations,
                "recommended_commit_message": (
                    "Document Conversational Hokage release candidate"
                ),
                "requires_approval_token": "APPLY_LOCAL_MODEL_DOC_PATCH",
            }
            flow.patch_plan_path.parent.mkdir(parents=True, exist_ok=True)
            flow.patch_plan_path.write_text(
                json.dumps(patch_plan), encoding="utf-8"
            )

            changed_paths = sorted({str(item["path"]) for item in operations})
            proposal_record = {
                "schema_version": "1.0.0",
                "report_type": "conversational_patch_proposal",
                "patch_id": f"patch-{digest[:10]}",
                "mission_id": flow.mission_id,
                "created_at": self.module.utc_now(),
                "status": "proposed",
                "operation_count": len(operations),
                "changed_paths": changed_paths,
                "patch_plan": str(
                    flow.patch_plan_path.relative_to(flow.mission_dir)
                ),
                "patch_preview": preview,
                "patch_sha256": digest,
                "approval_phrase": f"APROBAR PATCH-{digest[:10].upper()}",
                "rejection_phrase": f"RECHAZAR PATCH-{digest[:10].upper()}",
                "authority": {
                    "proposal_is_not_permission": True,
                    "approval_is_bound_to_patch_sha256": True,
                    "arguments_change_invalidates_approval": True,
                    "git_operations_are_not_authorized": True,
                },
            }
            flow.patch_proposal_path.parent.mkdir(parents=True, exist_ok=True)
            flow.patch_proposal_path.write_text(
                json.dumps(proposal_record), encoding="utf-8"
            )

            # A real apply_validated_patch action: correct patch_id and
            # changed_paths, matching the real proposal exactly - only
            # patch_sha256 is tampered.
            patch_action = shell.action_queue.append_action_checked(
                mission_id=mission_id,
                plan_id=f"{mission_id}-plan",
                skill_id="apply_validated_patch",
                extra_arguments={
                    "patch_id": proposal_record["patch_id"],
                    "patch_sha256": "0" * 64,
                    "patch_plan": proposal_record["patch_plan"],
                    "changed_paths": changed_paths,
                },
            )
            self.assertEqual(
                patch_action["arguments"]["patch_id"], proposal_record["patch_id"]
            )
            self.assertEqual(
                patch_action["arguments"]["changed_paths"], changed_paths
            )
            self.assertNotEqual(
                patch_action["arguments"]["patch_sha256"],
                proposal_record["patch_sha256"],
            )

            readme_before = readme_path.read_text(encoding="utf-8")

            # The real public gate: human approval_phrase ->
            # ActionQueue.approve_and_dispatch() -> _dispatch_for() ->
            # exact patch binding check -> sha256 mismatch -> fail closed.
            result = shell.approve_action(
                patch_action, patch_action["approval_phrase"]
            )
            self.assertEqual(result["status_code"], "ACTION_EXECUTION_FAILED")

            persisted = next(
                a
                for a in shell.action_queue.load()["actions"]
                if a["action_id"] == patch_action["action_id"]
            )
            self.assertEqual(persisted["status"], "failed")

            reloaded_proposal = json.loads(
                flow.patch_proposal_path.read_text(encoding="utf-8")
            )
            self.assertEqual(reloaded_proposal["status"], "proposed")
            self.assertFalse(flow.patch_apply_path.exists())
            self.assertEqual(
                readme_path.read_text(encoding="utf-8"), readme_before
            )

    def test_model_action_dispatch_uses_a_single_action_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            approved = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = reject_until(
                shell, approved["next_action"], "invoke_local_model_audit"
            )

            grant = shell.audit_flow.build_model_grant(action)
            self.assertEqual(grant["approval_phrase"], action["approval_phrase"])

    def test_run_technical_plan_dispatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            fake_action = {
                "skill_id": "run_technical_plan",
                "arguments": {
                    "provider": "codex",
                    "model": "provider_default",
                    "strategy": "remote",
                },
            }
            with self.assertRaises(AuditFlowError):
                shell._dispatch_for(fake_action)

    def test_no_legacy_queue_mutation_paths_remain(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("action_queue.update(", source)
        self.assertNotIn("action_queue.save(", source)
        self.assertNotIn(".append_action(", source)
        self.assertIn("approve_and_dispatch(", source)
        self.assertIn("append_action_checked(", source)
        self.assertIn("reject_action_checked(", source)


if __name__ == "__main__":
    unittest.main()
