import importlib.util
import json
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
        "run_conversational_hokage_slice3",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ConversationalLifecycleTests(unittest.TestCase):
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

    def prepare_actions(self, shell):
        proposal = shell.one_shot(
            "Revisá este repositorio con controles determinísticos. "
            "No modifiques archivos."
        )
        charter = shell.approve_charter(
            proposal["charter"]["approval_phrase"]
        )
        first = charter["next_action"]
        first_result = shell.approve_action(
            first,
            first["approval_phrase"],
        )
        second = first_result["next_action"]
        second_result = shell.approve_action(
            second,
            second["approval_phrase"],
        )
        return proposal, second_result

    def test_all_actions_build_deterministic_review_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            shell = self.make_shell(Path(tmp))
            _, result = self.prepare_actions(shell)
            review = result["review_proposal"]
            self.assertEqual(review["status"], "proposed")
            self.assertTrue(
                review["approval_phrase"].startswith(
                    "APROBAR REVIEW-"
                )
            )
            summary_path = (
                shell.lifecycle.execution_summary_path
            )
            summary = json.loads(
                summary_path.read_text(encoding="utf-8")
            )
            self.assertEqual(summary["status"], "passed")
            self.assertEqual(
                summary["counts"]["completed"],
                2,
            )
            self.assertEqual(summary["counts"]["failed"], 0)

    def test_review_teachback_and_closure_complete_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal, actions = self.prepare_actions(shell)

            review = actions["review_proposal"]
            reviewed = shell.approve_review(
                review,
                review["approval_phrase"],
            )
            request = reviewed["teachback_request"]
            self.assertEqual(
                request["status"],
                "awaiting_user_explanation",
            )

            explained = shell.record_teachback(
                request,
                (
                    "TEACHBACK: Se ejecutaron dos inspecciones "
                    "de solo lectura, sus resultados quedaron como "
                    "evidencia y toda acción nueva requiere otra "
                    "aprobación humana."
                ),
            )
            closure = explained["closure_proposal"]
            self.assertTrue(
                closure["approval_phrase"].startswith(
                    "APROBAR CIERRE-"
                )
            )

            closed = shell.approve_closure(
                closure,
                closure["approval_phrase"],
            )
            self.assertEqual(
                closed["status_code"],
                "MISSION_CLOSED",
            )

            mission_id = proposal["mission_id"]
            mission_status = (
                root
                / "workspace"
                / "missions"
                / mission_id
                / "mission_status.json"
            )
            self.assertTrue(mission_status.exists())
            status = json.loads(
                mission_status.read_text(encoding="utf-8")
            )
            self.assertEqual(status["status"], "closed")

            user_state = json.loads(
                (
                    root
                    / "runtime"
                    / "user_state.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIsNone(
                user_state["active_mission_id"]
            )
            self.assertEqual(
                user_state["last_mission_id"],
                mission_id,
            )

            memory_note = (
                root
                / "obsidian"
                / "10-missions"
                / f"{mission_id}.md"
            )
            self.assertTrue(memory_note.exists())

    def test_wrong_closure_phrase_does_not_close(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal, actions = self.prepare_actions(shell)
            review = actions["review_proposal"]
            reviewed = shell.approve_review(
                review,
                review["approval_phrase"],
            )
            taught = shell.record_teachback(
                reviewed["teachback_request"],
                (
                    "TEACHBACK: Entiendo la ejecución, su evidencia "
                    "y que el cierre necesita una aprobación distinta."
                ),
            )
            result = shell.approve_closure(
                taught["closure_proposal"],
                "sí, cerrar",
            )
            self.assertEqual(
                result["status_code"],
                "CLOSURE_APPROVAL_MISMATCH",
            )
            mission_status = (
                root
                / "workspace"
                / "missions"
                / proposal["mission_id"]
                / "mission_status.json"
            )
            self.assertFalse(mission_status.exists())


if __name__ == "__main__":
    unittest.main()
