import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "tools"
    / "hokage_orchestrator"
    / "run_conversational_hokage.py"
)


def load_script():
    spec = importlib.util.spec_from_file_location(
        "run_conversational_hokage_slice2",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ConversationalActionTests(unittest.TestCase):
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

    def test_skill_registry_is_non_mutating_and_no_network(self):
        self.assertEqual(self.module.validate_skills(), [])

    def test_charter_approval_creates_runtime_plan_and_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            shell = self.make_shell(Path(tmp))
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            result = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            self.assertEqual(
                result["status_code"],
                "CHARTER_APPROVED_ACTIONS_PROPOSED",
            )
            self.assertGreaterEqual(result["action_count"], 2)
            self.assertEqual(
                result["next_action"]["skill_id"],
                "inspect_python_runtime",
            )

    def test_exact_action_approval_executes_bounded_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            shell = self.make_shell(Path(tmp))
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos. "
                "No modifiques archivos."
            )
            charter = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = charter["next_action"]
            result = shell.approve_action(
                action,
                action["approval_phrase"],
            )
            self.assertEqual(
                result["status_code"],
                "ACTION_COMPLETED",
            )
            self.assertEqual(
                result["action"]["status"],
                "completed",
            )
            evidence = result["action"]["evidence"]["runtime_result"]
            self.assertTrue(evidence["output_paths"])
            self.assertTrue(
                Path(evidence["output_paths"][0]).exists()
            )

    def test_completed_action_survives_reentry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(
                "Revisá este repositorio con controles determinísticos."
            )
            charter = shell.approve_charter(
                proposal["charter"]["approval_phrase"]
            )
            action = charter["next_action"]
            shell.approve_action(
                action,
                action["approval_phrase"],
            )

            restored = self.make_shell(root)
            queue = restored.status_payload()["action_queue"]["actions"]
            self.assertEqual(queue[0]["status"], "completed")
            self.assertEqual(
                restored.next_action()["skill_id"],
                "inspect_git_status",
            )


if __name__ == "__main__":
    unittest.main()
