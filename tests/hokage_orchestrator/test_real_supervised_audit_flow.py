import json
import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator.audit_flow import (
    RC_README_MARKER,
    RealSupervisedAuditFlow,
    normalize_ollama_host,
)
from tools.hokage_orchestrator.skill_runtime import (
    ActionQueue,
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

    def test_action_queue_uses_real_audit_sequence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mission = root / "missions" / "mission-1"
            queue = ActionQueue(mission)
            payload = queue.initialize(
                mission_id="mission-1",
                plan_id="plan-1",
                charter={
                    "proposed_skills": [
                        "inspect_public_repo",
                        "invoke_local_model",
                    ]
                },
                runtime_proposals=[],
                local_model="qwen2.5-coder:7b",
            )
            skills = [
                item["skill_id"]
                for item in payload["actions"]
            ]
            self.assertEqual(
                skills,
                [
                    "run_deterministic_audit_checks",
                    "invoke_local_model_audit",
                ],
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
            self.assertTrue(
                grant["approval_phrase"].startswith(
                    "APROBAR SESION-MODELO-"
                )
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
