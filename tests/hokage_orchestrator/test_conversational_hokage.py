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
        "run_conversational_hokage",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ConversationalHokageTests(unittest.TestCase):
    def setUp(self):
        self.module = load_script()

    def test_intent_interprets_repo_review_and_constraints(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            payload = self.module.interpret_intent(
                (
                    "Revisá este repositorio con checks determinísticos "
                    "y Ollama. No modifiques nada. Medí tokens y tiempo."
                ),
                repo,
            )
            self.assertEqual(payload["intent_type"], "inspect_and_review")
            self.assertEqual(payload["targets"], [str(repo.resolve())])
            self.assertIn(
                "deterministic checks before model invocation",
                payload["constraints"],
            )
            self.assertIn("local model only", payload["constraints"])
            self.assertIn("usage_report", payload["requested_outputs"])
            self.assertEqual(
                self.module.validate_intent(payload, repo),
                [],
            )

    def test_charter_uses_exact_approval_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            intent = self.module.interpret_intent(
                "Revisá este repositorio sin modificarlo.",
                repo,
            )
            charter = self.module.build_charter(intent, "Eduardo")
            self.assertTrue(
                charter["approval_phrase"].startswith(
                    "APROBAR CHARTER-"
                )
            )
            self.assertTrue(
                charter["authority"]["charter_is_not_permission"]
            )

    def test_continuity_distinguishes_first_and_returning_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self.module.ContinuityStore(
                root / "runtime",
                root / "obsidian",
                "Eduardo",
            )
            first = store.start_session()
            second = store.start_session()
            self.assertTrue(first["first_session"])
            self.assertFalse(second["first_session"])
            self.assertIn("Bienvenido de nuevo", second["greeting"])
            self.assertTrue(
                (root / "obsidian" / "00-home" / "dashboard.md").exists()
            )

    def test_one_shot_creates_charter_without_tool_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            shell = self.module.ConversationalHokage(
                repo_root=repo,
                workspace_root=root / "workspace",
                state_root=root / "runtime",
                memory_root=root / "obsidian",
                actor="Eduardo",
                json_mode=True,
            )
            result = shell.one_shot(
                "Revisá este repositorio sin modificar archivos."
            )
            self.assertEqual(result["status_code"], "CHARTER_PROPOSED")
            self.assertTrue(
                result["authority"]["no_tool_execution_occurred"]
            )
            self.assertTrue(Path(result["paths"]["charter_json"]).exists())

    def test_charter_approval_proposes_but_does_not_execute_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.module.ConversationalHokage(
                repo_root=ROOT,
                workspace_root=root / "workspace",
                state_root=root / "runtime",
                memory_root=root / "obsidian",
                actor="Eduardo",
            )
            proposed = shell.one_shot(
                "Revisá este repositorio sin modificarlo."
            )
            result = shell.approve_charter(
                proposed["charter"]["approval_phrase"]
            )
            self.assertEqual(
                result["status_code"],
                "CHARTER_APPROVED_ACTIONS_PROPOSED",
            )
            self.assertTrue(
                result["authority"][
                    "charter_approval_does_not_authorize_actions"
                ]
            )
            queue = shell.status_payload()["action_queue"]["actions"]
            self.assertTrue(queue)
            self.assertTrue(
                all(item["status"] == "proposed" for item in queue)
            )

    def test_generated_mission_id_is_ascii_runtime_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            shell = self.module.ConversationalHokage(
                repo_root=repo,
                workspace_root=root / "workspace",
                state_root=root / "runtime",
                memory_root=root / "obsidian",
                actor="Eduardo",
            )
            result = shell.one_shot(
                "Revisá este repositorio y medí la ejecución."
            )
            mission_id = result["mission_id"]
            self.assertRegex(
                mission_id,
                r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,120}$",
            )
            mission_id.encode("ascii")

    def test_wrong_approval_phrase_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            shell = self.module.ConversationalHokage(
                repo_root=repo,
                workspace_root=root / "workspace",
                state_root=root / "runtime",
                memory_root=root / "obsidian",
                actor="Eduardo",
            )
            shell.one_shot("Revisá este repositorio.")
            result = shell.approve_charter("sí")
            self.assertEqual(
                result["status_code"],
                "CHARTER_APPROVAL_MISMATCH",
            )


if __name__ == "__main__":
    unittest.main()
