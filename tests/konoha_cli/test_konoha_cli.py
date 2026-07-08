import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "konoha_cli.py"


def load_module():
    spec = importlib.util.spec_from_file_location("konoha_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class KonohaCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_version(self):
        self.assertEqual(self.module.main(["--version"]), 0)

    def test_unknown_command_fails(self):
        self.assertEqual(self.module.main(["unknown", "command"]), 2)

    def test_mission_dry_run_is_allowlisted(self):
        self.assertIn(("mission", "dry-run"), self.module.TOOL_SCRIPTS)

    def test_alias_normalization(self):
        self.assertEqual(
            self.module.normalize_args(["--target-repo-root", "."]),
            ["--repo-root", "."],
        )

    def test_dispatch_preserves_allowlisted_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            script = repo / "tools" / "mission_workflow" / "run_dry_run_mission.py"
            script.parent.mkdir(parents=True)
            script.write_text("# stub\n", encoding="utf-8")

            with patch.object(self.module, "repo_root", return_value=repo):
                with patch.object(self.module.subprocess, "run") as run_mock:
                    run_mock.return_value.returncode = 0
                    code = self.module.dispatch("mission", "dry-run", ["--help"])

            self.assertEqual(code, 0)
            command = run_mock.call_args.args[0]
            self.assertIn(str(script.resolve()), command)


if __name__ == "__main__":
    unittest.main()
