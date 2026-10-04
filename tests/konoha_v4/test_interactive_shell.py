from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from tools.konoha_v4 import cli, conversation
from tools.konoha_v4.interactive_shell import (
    MASCOTS,
    ProjectInfo,
    dashboard_lines,
    detect_project,
    print_splash,
    safe_remote_identity,
    sanitize_display,
    state_root_for_project,
)


class InteractiveShellTests(unittest.TestCase):
    def init_repo(self, path: Path) -> None:
        subprocess.run(["git", "init", "-b", "main", str(path)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_project_metadata_reads_git_only_and_distinguishes_same_names(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "one" / "media"
            second = Path(temp) / "two" / "media"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "README.private-marker").write_text("must not be read")
            self.init_repo(first)
            self.init_repo(second)
            a = detect_project(first)
            b = detect_project(second)
            self.assertEqual(a.name, "media")
            self.assertEqual(a.branch, "main")
            self.assertEqual(a.git_state, "dirty")
            self.assertNotEqual(a.identity, b.identity)
            self.assertEqual(a.git_root, first.resolve())

    def test_project_detection_does_not_open_repository_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            (root / "README.md").write_text("private marker")
            with patch.object(Path, "read_text", side_effect=AssertionError("repository file read")):
                self.assertEqual(detect_project(root).name, root.name)

    def test_git_clean_and_dirty_display(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            clean = detect_project(root)
            self.assertEqual(clean.git_state, "clean")
            (root / "new.txt").write_text("x")
            self.assertEqual(detect_project(root).git_state, "dirty")

    def test_non_git_directory_has_deterministic_path_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plain"
            root.mkdir()
            info = detect_project(root)
            self.assertIsNone(info.git_root)
            self.assertEqual(info.name, "plain")
            self.assertEqual(info.git_state, "not a Git repository")

    def test_remote_identity_strips_credentials_query_and_fragment(self):
        result = safe_remote_identity("https://token:secret@git.example/org/media.git?key=x#top")
        self.assertEqual(result, "https://git.example/org/media")
        self.assertNotIn("secret", result)
        self.assertEqual(safe_remote_identity("git@git.example:org/media.git"),
                         "ssh://git.example/org/media")

    def test_terminal_display_metadata_replaces_controls_and_preserves_unicode(self):
        remote = safe_remote_identity("https://git.example/org/\x1b[31m媒体\x07.git?token=x")
        info = ProjectInfo(
            cwd=Path("/work/\x1b\n"), git_root=Path("/repo/\x1b[31m媒体"),
            name="Médiá\n_日本", branch="feat\x07ure", git_state="dirty\x1b",
            remote_identity=remote, identity="abc123",
        )
        lines = dashboard_lines(info, Path("/state/\x1b\n"))
        rendered = "\n".join(lines)
        self.assertTrue(all(character.isprintable() for line in lines for character in line))
        self.assertIn("Médiá�_日本", rendered)
        self.assertIn("�[31m媒体", rendered)
        self.assertIn("Workspace path: /state/��", rendered)
        self.assertEqual(sanitize_display("Unicode café 日本"), "Unicode café 日本")

    def test_workspace_confirmation_sanitizes_path_for_terminal(self):
        output = io.StringIO()
        with patch.object(conversation._TERMINAL_INPUT, "read_exact_line", return_value="no"), patch(
            "sys.stdout", output
        ):
            self.assertFalse(conversation._confirm_project_workspace(Path("/state/\x1b\n\x07")))
        self.assertTrue(all(character.isprintable() for character in output.getvalue().rstrip("\n")))
        self.assertIn("/state/���", output.getvalue())

    def test_state_location_is_xdg_local_and_not_repository(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.init_repo(root)
            info = detect_project(root)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(root / "xdg")}, clear=False):
                state = state_root_for_project(info)
            self.assertEqual(state.parent.name, "projects")
            self.assertNotEqual(state, root)
            self.assertFalse(state.exists())

    def test_splash_selection_no_color_and_non_tty_fallback(self):
        with patch.dict(os.environ, {"KONOHA_MASCOT": "rookie_shinobi", "NO_COLOR": "1"}, clear=False):
            output = io.StringIO()
            with patch("sys.stdout", output):
                selected = print_splash(tty=True)
            self.assertEqual(selected, "rookie_shinobi")
            self.assertIn("K O N O H A", output.getvalue())
            self.assertNotIn("\033[", output.getvalue())
        output = io.StringIO()
        with patch("sys.stdout", output):
            self.assertIsNone(print_splash(tty=False))
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(set(MASCOTS), {
            "rookie_shinobi", "masked_scout", "wandering_swordsman",
            "storm_captain", "spirit_guard", "scroll_keeper",
        })
        with patch("tools.konoha_v4.interactive_shell.random.choice",
                   return_value="scroll_keeper"):
            from tools.konoha_v4.interactive_shell import select_mascot
            self.assertEqual(select_mascot()[0], "scroll_keeper")

    def test_chafa_absent_and_unconfigured_art_are_safe_fallbacks(self):
        with tempfile.TemporaryDirectory() as temp:
            art = Path(temp)
            with patch("tools.konoha_v4.interactive_shell.shutil.which", return_value=None):
                from tools.konoha_v4.interactive_shell import render_local_art_if_available
                self.assertFalse(render_local_art_if_available(art))
                self.assertFalse(render_local_art_if_available(None))

    def test_local_art_symlinks_are_not_rendered(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            art = base / "art"
            art.mkdir()
            external = base / "outside.png"
            external.write_bytes(b"synthetic")
            (art / "outside.png").symlink_to(external)
            from tools.konoha_v4.interactive_shell import render_local_art_if_available
            with patch("tools.konoha_v4.interactive_shell.shutil.which", return_value="/usr/bin/chafa"), patch(
                "tools.konoha_v4.interactive_shell.subprocess.run"
            ) as run:
                self.assertFalse(render_local_art_if_available(art))
                run.assert_not_called()

    def test_tty_default_dispatch_and_non_tty_compatibility(self):
        with patch.object(cli.sys.stdin, "isatty", return_value=True), patch.object(
            cli.sys.stdout, "isatty", return_value=True
        ), patch.object(cli, "run", return_value=0
        ) as run:
            self.assertEqual(cli.main([]), 0)
            self.assertTrue(run.call_args.kwargs["interactive_shell"])
        with patch.object(cli.sys.stdin, "isatty", return_value=False), patch.object(
            cli.sys.stdout, "isatty", return_value=True
        ), patch.object(cli, "run", return_value=0
        ) as run:
            self.assertEqual(cli.main([]), 0)
            self.assertFalse(run.call_args.kwargs["interactive_shell"])
        with patch.object(cli, "run", return_value=0) as run:
            self.assertEqual(cli.main(["shell", "--no-splash"]), 0)
            self.assertTrue(run.call_args.kwargs["interactive_shell"])

        with patch.object(cli.sys.stdin, "isatty", return_value=True), patch.object(
            cli.sys.stdout, "isatty", return_value=False
        ), patch.object(cli, "run", return_value=0) as run:
            self.assertEqual(cli.main([]), 0)
            self.assertFalse(run.call_args.kwargs["interactive_shell"])

        with patch.object(cli.sys.stdin, "isatty", return_value=True), patch.object(
            cli.sys.stdout, "isatty", return_value=True
        ), patch.object(cli, "run", return_value=0) as run:
            self.assertEqual(cli.main(["--plan-only"]), 0)
            self.assertFalse(run.call_args.kwargs["interactive_shell"])
            self.assertTrue(run.call_args.kwargs["plan_only"])

        with patch.object(cli.sys.stdin, "isatty", return_value=False), patch.object(
            cli.sys.stdout, "isatty", return_value=False
        ), patch.object(cli, "run", return_value=0) as run:
            self.assertEqual(cli.main(["shell", "--plan-only"]), 0)
            self.assertTrue(run.call_args.kwargs["interactive_shell"])
            self.assertTrue(run.call_args.kwargs["plan_only"])

    def test_startup_does_not_create_workspace_or_invoke_model(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            state = Path(temp) / "xdg" / "projects" / "id"
            with patch.dict(os.environ, {"KONOHA_NO_SPLASH": "1"}, clear=False), patch.object(
                conversation, "_read_turn", return_value=":exit"
            ), patch.object(conversation, "acquire_context", side_effect=AssertionError("provider path reached")):
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(conversation.run(root, interactive_shell=True,
                                                      state_dir_override=state), 0)
            self.assertFalse(state.exists())

    def test_colon_line_is_single_command_and_exit_is_clean(self):
        for control in (":status", ":help", ":whatever"):
            with self.subTest(control=control), patch.object(
                conversation._TERMINAL_INPUT, "read_exact_line", return_value=control
            ), patch.object(conversation._TERMINAL_INPUT, "read_block_until") as capture:
                self.assertEqual(conversation._read_turn(interactive_controls=True), control)
                capture.assert_not_called()

    def test_legacy_colon_mission_text_still_uses_block_capture(self):
        output = io.StringIO()
        reader = conversation.TerminalTurnReader(
            io.StringIO(":custom-mission-text\nsecond line\n:fin\n"), output
        )
        with patch.object(conversation, "_TERMINAL_INPUT", reader), patch("sys.stdout", output):
            self.assertEqual(conversation._read_turn(), ":custom-mission-text\nsecond line")

    def test_legacy_repo_controls_remain_single_line(self):
        for control in (":repo", ":repo anything", ":entendido"):
            with self.subTest(control=control), patch.object(
                conversation._TERMINAL_INPUT, "read_exact_line", return_value=control
            ), patch.object(conversation._TERMINAL_INPUT, "read_block_until") as capture:
                self.assertEqual(conversation._read_turn(), control)
                capture.assert_not_called()

    def test_run_enables_colon_controls_only_in_interactive_shell(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plain"
            root.mkdir()
            for enabled in (False, True):
                with self.subTest(interactive_shell=enabled), patch.object(
                    conversation, "_read_turn", return_value="salir"
                ) as read_turn, patch("sys.stdout", io.StringIO()):
                    self.assertEqual(conversation.run(root, interactive_shell=enabled), 0)
                self.assertEqual(read_turn.call_args.kwargs["interactive_controls"], enabled)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            state = Path(temp) / "state"
            with patch.dict(os.environ, {"KONOHA_NO_SPLASH": "1"}, clear=False), patch.object(
                conversation, "_read_turn", return_value=":exit"
            ):
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(conversation.run(root, interactive_shell=True,
                                                      state_dir_override=state), 0)
            self.assertFalse(state.exists())

    def test_natural_text_requires_explicit_workspace_choice_before_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            state = Path(temp) / "xdg" / "projects" / "id"
            with patch.dict(os.environ, {"KONOHA_NO_SPLASH": "1"}, clear=False), patch.object(
                conversation, "_read_turn", side_effect=["me conecto a stream en 30 minutos", ":exit"]
            ), patch.object(conversation._TERMINAL_INPUT, "read_exact_line", return_value="no") as answer, patch.object(
                conversation, "acquire_context", side_effect=AssertionError("request was submitted")
            ):
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(conversation.run(root, interactive_shell=True,
                                                      state_dir_override=state), 0)
            answer.assert_called_once()
            self.assertFalse(state.exists())

    def test_study_creates_project_state_only_after_operator_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            state = Path(temp) / "xdg" / "projects" / "id"
            with patch.dict(os.environ, {"KONOHA_NO_SPLASH": "1"}, clear=False), patch.object(
                conversation, "_read_turn", side_effect=[":study", ":exit"]
            ), patch.object(conversation._TERMINAL_INPUT, "read_exact_line", return_value="yes"), patch.object(
                conversation, "acquire_context", side_effect=AssertionError("study invoked planner")
            ):
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(conversation.run(root, interactive_shell=True,
                                                      state_dir_override=state), 0)
            self.assertTrue(state.is_dir())
            self.assertFalse((root / "memory").exists())

    def test_media_dogfood_routes_natural_input_to_existing_supervised_planner(self):
        """Exercise the real shell routing with provider/planner boundaries stubbed."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            self.init_repo(root)
            state_base = Path(temp) / "local-state"
            output = io.StringIO()
            planned = []

            def planner(*args, **kwargs):
                planned.append((args, kwargs))
                print("Next supervised step proposed; approval remains pending.")
                return SimpleNamespace(mission_id="mission-media-dogfood"), [], 1

            with patch.dict(os.environ, {"XDG_STATE_HOME": str(state_base),
                                          "KONOHA_NO_SPLASH": "1"}, clear=False), patch.object(
                conversation, "_read_turn", side_effect=[
                    "me conecto a stream en 30 minutos", ":exit"
                ]
            ), patch.object(conversation._TERMINAL_INPUT, "read_exact_line", return_value="yes"), patch.object(
                conversation, "acquire_context",
                return_value=SimpleNamespace(provider_readiness={}, as_dict=lambda: {}),
            ), patch.object(conversation, "CapabilityRegistry", return_value=object()), patch.object(
                conversation, "_acquire_repo_evidence_for_planning", return_value=object()
            ), patch.object(
                conversation, "_repository_state_unavailable_reason", return_value=None
            ), patch.object(conversation, "_repo_state", return_value={}), patch.object(
                conversation, "_build_validated_plan", side_effect=planner
            ), patch.object(conversation, "_approval_loop", return_value=conversation._SESSION_EXIT) as approval_gate:
                with patch("sys.stdout", output):
                    self.assertEqual(conversation.run(root, interactive_shell=True), 0)

            self.assertEqual(len(planned), 1, output.getvalue())
            self.assertEqual(planned[0][0][1], "me conecto a stream en 30 minutos")
            approval_gate.assert_called_once()
            self.assertIn("Project: media", output.getvalue())
            self.assertIn("Next supervised step proposed", output.getvalue())
            self.assertNotIn("stream", str(root / "memory"))
            self.assertFalse((root / "memory").exists())
            self.assertTrue(list((state_base / "konoha" / "projects").iterdir()))

    def test_resume_finds_project_scoped_mission_and_preserves_legacy_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "media"
            root.mkdir()
            self.init_repo(root)
            xdg = Path(temp) / "xdg"
            project_state = xdg / "konoha" / "projects" / detect_project(root).identity
            mission_id = "mission-media"
            (project_state / "missions" / mission_id).mkdir(parents=True)
            with patch.dict(os.environ, {"XDG_STATE_HOME": str(xdg)}, clear=False), patch.object(
                conversation, "CapabilityRegistry", return_value=object()
            ), patch.object(conversation, "_run_resumable_execution", return_value="paused") as resume:
                self.assertEqual(conversation.resume_mission(root, mission_id), 0)
            self.assertEqual(resume.call_args.args[1], project_state)

            with patch.dict(os.environ, {"XDG_STATE_HOME": str(xdg)}, clear=False), patch.object(
                conversation, "CapabilityRegistry", return_value=object()
            ), patch.object(conversation, "_run_resumable_execution", return_value="paused") as resume:
                self.assertEqual(conversation.resume_mission(root, "legacy-mission"), 0)
            self.assertEqual(resume.call_args.args[1], xdg / "konoha" / "v4")


if __name__ == "__main__":
    unittest.main()
