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

MISSION_TEXT = (
    "Revisá este repositorio con controles determinísticos. "
    "No modifiques archivos."
)


def load_script():
    spec = importlib.util.spec_from_file_location(
        "run_conversational_hokage_reject_charter",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class CharterRejectionContinuityTests(unittest.TestCase):
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

    def _user_state(self, root: Path) -> dict:
        return json.loads(
            (root / "runtime" / "user_state.json").read_text(encoding="utf-8")
        )

    def _active_mission(self, root: Path) -> dict:
        return json.loads(
            (root / "runtime" / "active_mission.json").read_text(
                encoding="utf-8"
            )
        )

    def test_a_normal_rejection_clears_continuity_and_no_stale_reentry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            mission_id = proposal["mission_id"]
            mission_dir = shell.mission_dir(mission_id)

            self.assertEqual(
                self._user_state(root)["active_mission_id"], mission_id
            )

            result = shell.reject_charter(
                proposal["charter"]["rejection_phrase"]
            )
            self.assertEqual(result["status_code"], "CHARTER_REJECTED")

            self.assertIsNone(self._user_state(root)["active_mission_id"])
            self.assertEqual(
                self._active_mission(root)["state"], "rejected"
            )
            self.assertIn("rejected_at", self._active_mission(root))

            # Historical artifacts preserved, never deleted.
            self.assertTrue(
                (mission_dir / "mission_charter.json").exists()
            )
            self.assertTrue(
                (mission_dir / "mission_decision.json").exists()
            )
            self.assertTrue(
                (mission_dir / "conversational_intent.json").exists()
            )

            # Fresh process from the same directories.
            resumed = self.make_shell(root)
            self.assertIsNone(resumed.pending_charter)
            self.assertIsNone(resumed.pending_decision)
            self.assertIsNone(resumed.active_mission)
            self.assertIsNone(resumed.resume_diagnostic)
            self.assertIsNone(
                self._user_state(root)["active_mission_id"]
            )

            # The rejected charter's own phrase no longer targets
            # anything - the user can propose a brand-new mission.
            second = resumed.one_shot(
                "Revisá otra parte distinta del repositorio con "
                "controles determinísticos."
            )
            self.assertEqual(second["status_code"], "CHARTER_PROPOSED")
            self.assertNotEqual(second["mission_id"], mission_id)

    def test_b_legacy_stale_charter_without_mission_id_still_resolves_and_rejects(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            mission_id = proposal["mission_id"]
            rejection_phrase = proposal["charter"]["rejection_phrase"]

            # Real repro: pending_charter recovered but missing its own
            # mission_id field, and pending_decision could not be
            # recovered either. active_mission/user_state are the only
            # remaining sources of evidence, and they still agree with
            # each other - resolution must succeed from them alone.
            stale_charter = dict(shell.pending_charter)
            del stale_charter["mission_id"]
            shell.pending_charter = stale_charter
            shell.pending_decision = None

            self.assertEqual(
                self._user_state(root)["active_mission_id"], mission_id
            )
            self.assertEqual(
                shell.active_mission["mission_id"], mission_id
            )

            result = shell.reject_charter(rejection_phrase)
            self.assertEqual(result["status_code"], "CHARTER_REJECTED")
            self.assertEqual(result["mission_id"], mission_id)
            self.assertIsNone(self._user_state(root)["active_mission_id"])
            self.assertEqual(
                self._active_mission(root)["state"], "rejected"
            )

            resumed = self.make_shell(root)
            self.assertIsNone(resumed.pending_charter)
            self.assertIsNone(resumed.active_mission)

    def test_pending_charter_mission_id_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            rejection_phrase = proposal["charter"]["rejection_phrase"]

            # pending_charter disagrees with active_mission/user_state on
            # mission_id - two distinct non-null candidates.
            tampered_charter = dict(shell.pending_charter)
            tampered_charter["mission_id"] = "mission-does-not-match"
            shell.pending_charter = tampered_charter

            before_user_state = self._user_state(root)
            before_active_mission = self._active_mission(root)

            result = shell.reject_charter(rejection_phrase)
            self.assertEqual(
                result["status_code"], "CHARTER_REJECTION_BINDING_MISMATCH"
            )

            # Zero mutation.
            self.assertEqual(self._user_state(root), before_user_state)
            self.assertEqual(
                self._active_mission(root), before_active_mission
            )
            self.assertIsNotNone(shell.pending_charter)
            self.assertIsNotNone(shell.active_mission)

    def test_pending_charter_with_no_resolvable_mission_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            rejection_phrase = proposal["charter"]["rejection_phrase"]

            # No source has a usable mission_id: pending_charter is
            # missing it, active_mission is gone, and user_state's
            # active_mission_id has been cleared too.
            stale_charter = dict(shell.pending_charter)
            del stale_charter["mission_id"]
            shell.pending_charter = stale_charter
            shell.pending_decision = None
            shell.active_mission = None

            from tools.hokage_orchestrator.continuity import write_json

            user_state = shell.continuity.load_user_state()
            user_state["active_mission_id"] = None
            write_json(shell.continuity.user_state_path, user_state)

            before_user_state = self._user_state(root)
            before_active_mission = self._active_mission(root)

            result = shell.reject_charter(rejection_phrase)
            self.assertEqual(
                result["status_code"], "CHARTER_REJECTION_MISSION_UNKNOWN"
            )

            # Zero mutation.
            self.assertEqual(self._user_state(root), before_user_state)
            self.assertEqual(
                self._active_mission(root), before_active_mission
            )
            self.assertIsNotNone(shell.pending_charter)

    def test_c_wrong_rejection_phrase_does_not_change_continuity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            mission_id = proposal["mission_id"]

            result = shell.reject_charter("esto no es la frase correcta")
            self.assertEqual(
                result["status_code"], "CHARTER_REJECTION_MISMATCH"
            )

            self.assertIsNotNone(shell.pending_charter)
            self.assertEqual(
                self._user_state(root)["active_mission_id"], mission_id
            )
            self.assertEqual(
                self._active_mission(root)["state"], "charter_proposed"
            )

    def test_d_exit_handoff_after_rejection_does_not_reannounce_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shell = self.make_shell(root)
            proposal = shell.one_shot(MISSION_TEXT)
            shell.reject_charter(proposal["charter"]["rejection_phrase"])

            shell.continuity.record_handoff(
                active_mission=shell.active_mission,
                next_safe_action=shell.next_safe_action_text(),
            )
            handoff = json.loads(
                (root / "runtime" / "last_handoff.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertIsNone(handoff["active_mission"])


if __name__ == "__main__":
    unittest.main()
