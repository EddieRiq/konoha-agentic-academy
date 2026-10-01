import importlib.util
import io
import re
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "konoha_cli.py"
VERSION_SCRIPT = ROOT / "tools" / "version.py"
PYPROJECT = ROOT / "pyproject.toml"


def load_module(name="konoha_cli", path=SCRIPT):
    spec = importlib.util.spec_from_file_location(
        name,
        path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def project_version(pyproject_text):
    # Python 3.10 has no tomllib: isolate [project] and require exactly one
    # anchored double-quoted version assignment inside it.
    sections = re.findall(
        r"^\[project\][ \t]*\n(.*?)(?=^\[|\Z)",
        pyproject_text,
        re.MULTILINE | re.DOTALL,
    )
    if len(sections) != 1:
        raise AssertionError(
            f"expected one [project] section, found {len(sections)}"
        )
    assignments = re.findall(
        r"^version[ \t]*=.*$",
        sections[0],
        re.MULTILINE,
    )
    if len(assignments) != 1:
        raise AssertionError(
            "expected one [project] version assignment, "
            f"found {len(assignments)}"
        )
    match = re.fullmatch(
        r'version[ \t]*=[ \t]*"([^"\\]+)"[ \t]*',
        assignments[0],
    )
    if match is None:
        raise AssertionError(
            f"unsupported [project] version assignment: {assignments[0]!r}"
        )
    return match.group(1)


class KonohaCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_version_is_release_aligned(self):
        canonical = load_module(
            "konoha_version",
            VERSION_SCRIPT,
        ).VERSION
        package_version = project_version(
            PYPROJECT.read_text(encoding="utf-8")
        )
        self.assertEqual(canonical, package_version)
        self.assertEqual(self.module.VERSION, canonical)

        output = io.StringIO()
        with redirect_stdout(output):
            code = self.module.main(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(output.getvalue(), f"{canonical}\n")

    def test_project_version_requires_one_project_assignment(self):
        self.assertEqual(
            project_version(
                '[project]\nname = "x"\nversion = "1.2.3"\n'
                '[tool.x]\nversion = "9.9.9"\n'
            ),
            "1.2.3",
        )
        invalid = {
            "no_project": '[tool.x]\nversion = "1.2.3"\n',
            "missing": '[project]\nname = "x"\n[tool.x]\nversion = "1"\n',
            "duplicate": '[project]\nversion = "1"\nversion = "2"\n',
            "two_sections": '[project]\nversion = "1"\n[project]\n',
            "unquoted": "[project]\nversion = 1.2.3\n",
        }
        for label, text in invalid.items():
            with self.subTest(label):
                with self.assertRaises(AssertionError):
                    project_version(text)

    def test_unknown_command_fails(self):
        self.assertEqual(
            self.module.main(["unknown", "command"]),
            2,
        )

    def test_active_registry_paths_exist(self):
        self.assertEqual(
            self.module.validate_registry(ROOT),
            [],
        )

    def test_canonical_mission_commands_are_registered(self):
        required = {
            ("mission", "start"),
            ("mission", "run"),
            ("mission", "plan"),
            ("mission", "review"),
            ("mission", "teachback"),
            ("mission", "close"),
            ("mission", "status"),
        }
        self.assertTrue(
            required.issubset(
                self.module.COMMAND_REGISTRY
            )
        )

    def test_top_level_command_resolution(self):
        key, args = self.module.resolve_command(
            ["doctor", "--json"]
        )
        self.assertEqual(key, ("doctor",))
        self.assertEqual(args, ["--json"])

    def test_grouped_command_resolution(self):
        key, args = self.module.resolve_command(
            [
                "mission",
                "teachback",
                "--mission-id",
                "m1",
            ]
        )
        self.assertEqual(
            key,
            ("mission", "teachback"),
        )
        self.assertEqual(
            args,
            ["--mission-id", "m1"],
        )

    def test_alias_normalization(self):
        self.assertEqual(
            self.module.normalize_args(
                ["--target-repo-root", "."]
            ),
            ["--repo-root", "."],
        )

    def test_dispatch_preserves_registered_script_and_fixed_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = (
                repo
                / "tools"
                / "teachback"
                / "manage_teachback.py"
            )
            script.parent.mkdir(parents=True)
            script.write_text(
                "# stub\n",
                encoding="utf-8",
            )

            with patch.object(
                self.module,
                "repo_root",
                return_value=repo,
            ):
                with patch.object(
                    self.module.subprocess,
                    "run",
                ) as run_mock:
                    run_mock.return_value.returncode = 0
                    code = self.module.dispatch_key(
                        ("mission", "teachback"),
                        ["--help"],
                    )

            self.assertEqual(code, 0)
            command = run_mock.call_args.args[0]
            self.assertEqual(
                command[1],
                str(script.resolve()),
            )
            self.assertEqual(command[2], "record")
            self.assertIn("--help", command)

    def test_package_install_does_not_inject_approval_token(self):
        with patch.object(
            self.module.subprocess,
            "run",
        ) as run_mock:
            run_mock.return_value.returncode = 0
            code = self.module.dispatch_key(
                ("package", "install"),
                ["--manifest", "manifest.json"],
            )

        self.assertEqual(code, 0)
        command = run_mock.call_args.args[0]
        self.assertIn("--apply", command)
        self.assertNotIn(
            "APPLY_SUPERVISED_PACKAGE_INSTALLATION",
            command,
        )
        self.assertNotIn("--allow-network", command)

    def test_legacy_command_is_marked_deprecated(self):
        entry = self.module.LEGACY_COMMANDS[
            ("mission", "dry-run")
        ]
        self.assertEqual(entry["status"], "deprecated")
        self.assertEqual(
            entry["replacement"],
            "mission run",
        )



    def test_conversational_shell_is_primary_product_entry(self):
        entry = self.module.COMMAND_REGISTRY[("shell",)]
        self.assertEqual(
            entry["script"],
            (
                "tools/hokage_orchestrator/"
                "run_conversational_hokage.py"
            ),
        )
        self.assertEqual(entry["fixed_args"], [])
        self.assertEqual(entry["network"], "blocked")

    def test_legacy_shell_remains_available_for_recovery(self):
        entry = self.module.COMMAND_REGISTRY[("shell", "legacy")]
        self.assertEqual(
            entry["script"],
            "tools/hokage_shell/run_hokage_shell.py",
        )
        self.assertEqual(entry["fixed_args"], ["interactive"])

    def test_mission_dash_help_uses_group_help(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = self.module.main(["mission", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("Konoha supervised mission flow", output.getvalue())

    def test_product_experience_commands_are_registered(self):
        self.assertIn(("welcome",), self.module.COMMAND_REGISTRY)
        self.assertIn(("quickstart",), self.module.COMMAND_REGISTRY)
        self.assertIn(("next",), self.module.COMMAND_REGISTRY)

    def test_quickstart_registry_retains_explicit_token_metadata(self):
        entry = self.module.COMMAND_REGISTRY[("quickstart",)]
        self.assertEqual(
            entry["approval_token"],
            "START_KONOHA_QUICKSTART",
        )
        self.assertNotIn(
            "--approval-token",
            entry["fixed_args"],
        )

    def test_default_help_uses_installed_command(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.module.print_help()
        value = output.getvalue()
        self.assertIn("konoha quickstart", value)
        self.assertNotIn("python tools/konoha_cli.py", value)

    def test_all_help_includes_deprecated_commands(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.module.print_help(show_all=True)
        value = output.getvalue()
        self.assertIn("Deprecated compatibility commands", value)
        self.assertIn("konoha mission dry-run", value)

    def test_mission_help_explains_complete_flow(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = self.module.print_help_topic(["mission"])
        value = output.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("konoha mission review", value)
        self.assertIn("konoha mission teachback", value)
        self.assertIn("konoha mission close", value)

    def test_maintainer_commands_are_hidden_from_default_help(self):
        default = io.StringIO()
        with redirect_stdout(default):
            self.module.print_help()
        self.assertNotIn("konoha release deliver", default.getvalue())

        maintainer = io.StringIO()
        with redirect_stdout(maintainer):
            self.module.print_maintainer_help()
        self.assertIn(
            "konoha release deliver",
            maintainer.getvalue(),
        )

    def test_unknown_command_offers_close_match(self):
        error = io.StringIO()
        with redirect_stderr(error):
            self.module.print_unknown(["quikstart"])
        value = error.getvalue()
        self.assertIn("konoha quickstart", value)
        self.assertIn("konoha help", value)

    def test_empty_invocation_delegates_to_conversational_shell(self):
        with patch.object(
            self.module,
            "dispatch_key",
            return_value=0,
        ) as dispatch_mock:
            code = self.module.main([])
        self.assertEqual(code, 0)
        dispatch_mock.assert_called_once_with(("shell",), [])

if __name__ == "__main__":
    unittest.main()
