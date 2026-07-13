import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "konoha_cli.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "konoha_cli",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class KonohaCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_version_is_release_aligned(self):
        self.assertEqual(self.module.VERSION, "3.3.0")
        self.assertEqual(
            self.module.main(["--version"]),
            0,
        )

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


if __name__ == "__main__":
    unittest.main()
