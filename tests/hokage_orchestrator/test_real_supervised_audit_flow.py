import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator import charter as charter_module
from tools.hokage_orchestrator import mission_decision
from tools.hokage_orchestrator.audit_flow import (
    RC_README_MARKER,
    RealSupervisedAuditFlow,
    normalize_ollama_host,
)
from tools.hokage_orchestrator.intent import interpret_intent
from tools.hokage_orchestrator.skill_runtime import (
    ActionQueue,
    PROVIDER_SKILL_IDS,
    make_action,
    validate_skills,
)


class RealSupervisedAuditFlowTests(unittest.TestCase):
    def make_flow(self, root: Path):
        repo = root / "repo"
        mission = root / "workspace" / "missions" / "mission-1"
        memory = root / "obsidian"
        tool = (
            repo
            / "tools"
            / "local_model_audit"
            / "manage_local_model_audit.py"
        )
        tool.parent.mkdir(parents=True)
        tool.write_text("# placeholder\n", encoding="utf-8")
        (repo / "README.md").write_text(
            "# Test repo\n",
            encoding="utf-8",
        )
        return RealSupervisedAuditFlow(
            repo_root=repo,
            workspace_root=root / "workspace",
            mission_dir=mission,
            memory_root=memory,
            mission_id="mission-1",
            actor="Eduardo",
            model="qwen2.5-coder:7b",
        )

    def test_ollama_host_normalization_is_explicit(self):
        self.assertEqual(
            normalize_ollama_host("127.0.0.1:11434/"),
            "http://127.0.0.1:11434",
        )
        self.assertEqual(
            normalize_ollama_host("http://localhost:11434/"),
            "http://localhost:11434",
        )

    def test_construction_does_not_require_real_audit_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / "README.md").write_text(
                "# Temporary repository\n",
                encoding="utf-8",
            )
            flow = RealSupervisedAuditFlow(
                repo_root=repo,
                workspace_root=root / "workspace",
                mission_dir=(
                    root
                    / "workspace"
                    / "missions"
                    / "mission-lazy"
                ),
                memory_root=root / "obsidian",
                mission_id="mission-lazy",
                actor="Eduardo",
                model="qwen2.5-coder:3b",
            )
            self.assertFalse(flow.audit_tool.exists())
            with self.assertRaisesRegex(
                Exception,
                "Local model audit tool is unavailable",
            ):
                flow._require_audit_tool()

    def test_skill_registry_accepts_bounded_mutating_patch_only(self):
        self.assertEqual(validate_skills(), [])

    def _seed_authority_1_1(self, mission_dir: Path, mission_id: str, intent: dict):
        """Build and approve a real 1.1 authority chain via the actual
        production builders - no hand-written Decision/Charter dicts, no
        direct write_authority_receipt() shortcut. Mirrors
        tests/hokage_orchestrator/test_mission_authority_chain.py's
        pattern."""

        human_constraints = {
            "mutation_forbidden": False,
            "network_blocked": False,
            "local_model_only": True,
            "private_context_restricted": False,
        }
        proposed = charter_module.real_proposed_skills(intent)
        provider_skill_ids = sorted(set(proposed) & PROVIDER_SKILL_IDS)
        provider_skill_id = provider_skill_ids[0] if provider_skill_ids else None

        decision = mission_decision.build_decision_1_1(
            mission_id=mission_id,
            intent=intent,
            bootstrap_snapshot={
                "providers": [{"provider": "ollama", "status": "ready"}]
            },
            local_model="qwen2.5-coder:7b",
            human_constraints=human_constraints,
            provider_skill_id=provider_skill_id,
        )
        charter = charter_module.build_charter_1_1(
            intent,
            decision,
            actor="Eduardo",
            human_constraints=human_constraints,
        )
        return charter_module.approve_charter_1_1(
            mission_dir,
            charter,
            decision,
            approval_phrase=charter["approval_phrase"],
            approved_by="Eduardo",
        )

    def test_action_queue_uses_real_audit_sequence(self):
        # ActionQueue.initialize() (1.1) requires a real approved
        # authority chain on disk - it no longer accepts charter/
        # runtime_proposals/local_model arguments directly.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission_id = "mission-1"
            mission = root / "missions" / mission_id
            mission.mkdir(parents=True)

            intent = interpret_intent(
                "Revisá este repositorio con Ollama.", root
            )
            approved = self._seed_authority_1_1(mission, mission_id, intent)

            queue = ActionQueue(mission)
            payload = queue.initialize(
                mission_id=mission_id,
                plan_id="plan-1",
            )
            skills = [
                item["skill_id"]
                for item in payload["actions"]
            ]
            # The real audit sequence: deterministic checks always run
            # before the model audit, in the exact order the approved
            # Charter declared.
            self.assertEqual(skills, approved["proposed_skills"])
            self.assertIn("run_deterministic_audit_checks", skills)
            self.assertIn("invoke_local_model_audit", skills)
            self.assertLess(
                skills.index("run_deterministic_audit_checks"),
                skills.index("invoke_local_model_audit"),
            )

    def test_model_grant_is_bound_to_action_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = self.make_flow(Path(tmp))
            action = make_action(
                mission_id="mission-1",
                plan_id="plan-1",
                skill_id="invoke_local_model_audit",
                arguments={
                    "provider": "ollama",
                    "model": "qwen2.5-coder:7b",
                    "scope": "one_repo_audit_invocation",
                },
            )
            grant = flow.build_model_grant(action)
            # The single human execution gate is the action's own
            # approval_phrase - build_model_grant() binds to it rather
            # than minting an independent challenge.
            self.assertEqual(
                grant["approval_phrase"], action["approval_phrase"]
            )
            approved = flow.approve_model_grant(
                action=action,
                phrase=grant["approval_phrase"],
            )
            self.assertEqual(approved["status"], "approved")

            changed = dict(action)
            changed["arguments_hash"] = "0" * 64
            with self.assertRaises(Exception):
                flow.build_model_grant(changed)

    def test_rc_guard_creates_exact_preview_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = self.make_flow(Path(tmp))
            issue, operation = flow._rc_issue_and_operation()
            self.assertEqual(
                issue["id"],
                "readme_missing_conversational_rc",
            )
            preview = flow._patch_preview([operation])
            self.assertIn(RC_README_MARKER, preview)
            readme = flow.repo_root / "README.md"
            self.assertNotIn(
                RC_README_MARKER,
                readme.read_text(encoding="utf-8"),
            )

    def test_private_memory_note_records_tokens_and_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            flow = self.make_flow(Path(tmp))
            flow.root.mkdir(parents=True, exist_ok=True)
            flow.normalized_audit_path.write_text(
                json.dumps(
                    {
                        "provider": "ollama",
                        "model": "qwen2.5-coder:7b",
                        "usage": {
                            "input_tokens": 100,
                            "output_tokens": 20,
                            "total_duration": 123,
                        },
                        "model_suggested_issues": [{}],
                        "validated_issues": [{}, {}],
                        "suppressed_issues": [{}],
                    }
                ),
                encoding="utf-8",
            )
            flow.patch_proposal_path.write_text(
                json.dumps(
                    {
                        "status": "applied",
                        "patch_sha256": "abc",
                        "changed_paths": ["README.md"],
                    }
                ),
                encoding="utf-8",
            )
            flow.post_patch_tests_path.write_text(
                json.dumps(
                    {
                        "status": "passed",
                        "failure_count": 0,
                    }
                ),
                encoding="utf-8",
            )
            note = flow.write_private_memory_note()
            self.assertTrue(note.exists())
            text = note.read_text(encoding="utf-8")
            self.assertIn("input_tokens: `100`", text)
            self.assertIn("validated_issues: `2`", text)


if __name__ == "__main__":
    unittest.main()
