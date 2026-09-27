"""User journeys through the normal conversation with real synthetic studies."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tools.konoha_v4 import conversation as cli
from tools.konoha_v4.repository_conversation import RepositoryConversation
from tools.konoha_v4.terminal_input import TerminalTurnReader
from tools.repo_evidence import workflow as wf


class RepositoryConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.fixture("target")
        self.donor = self.fixture("donor")
        self.state = self.base / "state"
        self.output = io.StringIO()
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)

    def fixture(self, name):
        repo = self.base / name
        repo.mkdir()
        (repo / "app.py").write_text("def main(): return 1\ndef unused(): return 2\n")
        (repo / "test_app.py").write_text("import app\n")
        (repo / "orphan.py").write_text("def unused(): return 2\n")
        (repo / "README.md").write_text("# Synthetic application\nA small local test application.\n")
        (repo / "private").mkdir()
        (repo / "private" / "hidden.py").write_text("PRIVATE_FIXTURE_SENTINEL = 1\n")
        return repo

    def turn(self, text):
        result = self.ui.handle(text)
        self.assertTrue(result.handled)
        return result

    def start(self):
        self.turn("understand this repository")
        return self.ui.active.study_id

    def test_self_study_explanation_evidence_and_no_workspace_mutation(self):
        before = {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()}
        identity = self.start()
        self.turn("explain")
        self.turn("show me the evidence")
        rendered = self.output.getvalue()
        for value in (identity, "Currentness: current", "Repository identity:", "Evidence pack:", "app.py", "Static evidence only"):
            self.assertIn(value, rendered)
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", rendered)
        self.assertEqual(before, {p.relative_to(self.repo): p.read_bytes() for p in self.repo.rglob("*") if p.is_file()})

    def test_teachback_exact_human_command_only(self):
        self.start()
        for text in ("ok", "yes", "understood", "thanks", "explain that again", "what does this component do?", " :entendido", ":ENTENDIDO", ":entendido "):
            self.turn(text)
            record, _, _ = self.ui.active.load()
            self.assertEqual("awaiting_human", record["teachback"]["status"])
        self.turn(":entendido")
        record, _, _ = self.ui.active.load()
        self.assertTrue(record["teachback"]["completed_by_user"])
        self.assertFalse((self.state / "missions").exists())

    def test_resume_preserves_identity_and_stale_stops_without_acquisition(self):
        identity = self.start()
        self.turn(":entendido")
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
        with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("silent refresh")):
            self.turn(f":repo resume {identity}")
            self.assertEqual(identity, self.ui.active.study_id)
            self.assertEqual("understood", self.ui.active.load()[0]["teachback"]["status"])
            (self.repo / "app.py").write_text("def changed(): return 3\n")
            self.turn("resume the repository study")
            self.turn("show me the evidence")
            self.turn("explain Konoha to me")
        self.assertIn("stale", self.output.getvalue())
        self.assertIn("new study", self.output.getvalue())

    def test_external_authorization_precedes_target_read(self):
        with mock.patch.object(wf, "start_study", wraps=wf.start_study) as start:
            self.turn(f"study this authorized local repository {self.donor}")
            start.assert_not_called()
            self.turn("yes")
            start.assert_not_called()
            command = self.ui.authorization_command
            self.turn(command.upper())
            start.assert_not_called()
            self.turn(command)
            start.assert_called_once()
        self.assertEqual(self.donor, self.ui.active.repo)
        self.assertNotIn("PRIVATE_FIXTURE_SENTINEL", self.output.getvalue())

    def test_recommendations_and_model_suggestions_remain_distinct(self):
        self.start()
        self.turn("what could Konoha improve?")
        self.assertIn("requires_human_entendido", self.output.getvalue())
        self.turn(":entendido")
        original = wf.recommend_study
        ref = self.ui.active.load()[1].facts[0]["evidence_ref"]
        suggestions = [{"recommendation": "Investigate structure", "risk": "Unknown runtime use", "scope": "One module", "evidence_refs": [ref]},
                       {"recommendation": "SUPPRESSED_CONTENT", "evidence_refs": ["invented"]}]
        with mock.patch.object(wf, "recommend_study", side_effect=lambda *args: original(*args, model_suggestions=suggestions)):
            self.turn("what could Konoha improve?")
        rendered = self.output.getvalue()
        for value in ("Deterministic finding", "Model suggestion", "locator_linkage_only_not_deterministic_truth", "Suppressed", "Risk:", "Scope:", "Recommendation is not permission"):
            self.assertIn(value, rendered)
        self.assertNotIn("SUPPRESSED_CONTENT", rendered)

    def test_donor_requires_both_teachbacks_and_preserves_provenance(self):
        target_id = self.start()
        self.turn(f":repo study {self.donor}")
        self.turn(self.ui.authorization_command)
        donor_id = self.ui.active.study_id
        self.turn("compare this authorized repo with Konoha")
        self.assertIn("requires_human_entendido", self.output.getvalue())
        self.turn(":entendido")
        self.turn("compare this authorized repo with Konoha")
        self.assertIsNone(self.ui.report)
        self.turn(f":repo resume {target_id}")
        self.turn(":entendido")
        self.turn(f":repo resume {donor_id} {self.donor}")
        self.turn("compare this authorized repo with Konoha")
        self.turn("show donor evidence")
        self.turn("show Konoha evidence")
        self.turn("what are the compatibility risks?")
        rendered = self.output.getvalue()
        for value in (target_id, donor_id, "Observed donor fact", "Konoha comparison", "Candidate lesson", "Compatibility/risk", "Recommendation is not permission"):
            self.assertIn(value, rendered)
        self.assertFalse(self.ui.report["authorizes_action"])

    def test_implement_recommendation_returns_planning_evidence_only(self):
        self.start()
        self.turn(":entendido")
        self.turn("what could Konoha improve?")
        result = self.turn("implement recommendation 1")
        self.assertIsNotNone(result.planning_evidence)
        self.assertFalse(result.planning_evidence["authorizes_action"])
        self.assertFalse((self.state / "missions").exists())

    def test_implementation_enters_existing_approval_path_with_exact_human_request(self):
        for plan_only in (False, True):
            with self.subTest(plan_only=plan_only):
                turns = ["understand this repository", ":entendido", "what could Konoha improve?", "implement recommendation 1", "exit"]
                acquired = SimpleNamespace(provider_readiness={}, as_dict=lambda: {})
                plan = mock.Mock()
                with mock.patch.object(cli, "default_state_root", return_value=self.state), \
                     mock.patch.object(cli, "_read_turn", side_effect=turns), \
                     mock.patch.object(cli, "CapabilityRegistry"), \
                     mock.patch.object(cli, "acquire_context", return_value=acquired), \
                     mock.patch.object(cli, "_build_validated_plan", return_value=(plan, [], 1)) as build, \
                     mock.patch.object(cli, "_approval_loop", return_value=None) as approval, \
                     mock.patch.object(cli, "_run_resumable_execution") as execute, contextlib.redirect_stdout(self.output):
                    self.assertEqual(0, cli.run(self.repo, plan_only=plan_only))
                build.assert_called_once()
                args = build.call_args.args
                self.assertEqual("implement recommendation 1", args[1])
                self.assertFalse(args[2]["recommendation_evidence_only"]["authorizes_action"])
                approval.assert_called_once()
                self.assertEqual(plan_only, approval.call_args.kwargs["plan_only"])
                self.assertIs(plan, approval.call_args.args[3])
                execute.assert_not_called()

    def test_stale_report_cannot_enter_planning(self):
        self.start()
        self.turn(":entendido")
        self.turn("what could Konoha improve?")
        (self.repo / "app.py").write_text("# changed\n")
        with mock.patch.object(wf, "acquire_repo_evidence", side_effect=AssertionError("refresh")):
            result = self.turn("implement recommendation 1")
        self.assertIsNone(result.planning_evidence)
        self.assertIn("Currentness: stale", self.output.getvalue())

    def test_external_resume_requires_fresh_authorization_in_new_session(self):
        self.turn(f":repo study {self.donor}")
        self.turn(self.ui.authorization_command)
        identity = self.ui.active.study_id
        self.ui = RepositoryConversation(self.repo, self.state, self.output.write)
        with mock.patch.object(wf, "load_study", wraps=wf.load_study) as load:
            self.turn(f":repo resume {identity} {self.donor}")
            load.assert_not_called()
            self.turn("ok")
            load.assert_not_called()
            self.turn(self.ui.authorization_command)
            self.assertTrue(load.called)
        self.assertEqual(identity, self.ui.active.study_id)

    def test_unsafe_roots_remote_paths_and_public_state_are_refused(self):
        for path in (str(self.repo / "private"), "https://example.org/repo", "../relative"):
            with mock.patch.object(wf, "start_study") as start:
                self.turn(f":repo study {path}")
                start.assert_not_called()
        public_state = self.repo / "public-state"
        self.ui = RepositoryConversation(self.repo, public_state, self.output.write)
        self.turn("understand this repository")
        self.assertIsNone(self.ui.active)
        self.assertFalse(public_state.exists())

    def test_multiline_mission_is_not_intercepted_and_leave_does_not_close(self):
        self.assertFalse(self.ui.handle("understand this repository\nthen prepare a migration plan").handled)
        identity = self.start()
        self.turn(":repo leave")
        self.assertIsNone(self.ui.active)
        self.turn(f":repo resume {identity}")
        self.assertEqual("awaiting_human", self.ui.active.load()[0]["teachback"]["status"])


    def test_main_loop_deterministic_routes_never_invoke_provider_or_executor(self):
        turns = ["understand this repository", "ok", "explain that again", ":entendido", "what could Konoha improve?", "exit"]
        with mock.patch.object(cli, "default_state_root", return_value=self.state), mock.patch.object(cli, "_read_turn", side_effect=turns), \
             mock.patch.object(cli, "acquire_context", side_effect=AssertionError("provider probe")), \
             mock.patch.object(cli, "_build_validated_plan", side_effect=AssertionError("provider planning")), \
             mock.patch.object(cli, "_run_resumable_execution", side_effect=AssertionError("execution")), contextlib.redirect_stdout(self.output):
            self.assertEqual(0, cli.run(self.repo))

    def test_exact_command_whitespace_survives_terminal_reader(self):
        for text in (":entendido", " :entendido", ":entendido ", ":ENTENDIDO"):
            reader = TerminalTurnReader(io.StringIO(text + "\n"), self.output)
            with mock.patch.object(cli, "_TERMINAL_INPUT", reader):
                self.assertEqual(text, cli._read_turn())


if __name__ == "__main__":
    unittest.main()
