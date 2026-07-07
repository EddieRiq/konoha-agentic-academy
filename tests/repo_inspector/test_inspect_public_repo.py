import tempfile
import unittest
from pathlib import Path

from tools.repo_inspector.inspect_public_repo import inspect_repo, is_blocked_path


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class RepoInspectorTests(unittest.TestCase):
    def make_minimal_repo(self, root: Path) -> None:
        write(
            root / "README.md",
            "Konoha test repo. It does not execute missions. Git operations are blocked. Private context is blocked.",
        )
        write(root / "CHANGELOG.md", "# Changelog\n")
        write(root / "docs/guides/README.md", "# Guides\n")
        write(root / "scrolls/README.md", "# Scrolls\n")
        write(root / "tools/runtime_runner/run_dry_run_runtime.py", "print('runner safe')\n")
        write(root / "tools/runtime_validator/validate_runtime_package.py", "print('validator safe')\n")
        write(root / "tools/runtime_builder/create_dry_run_package.py", "print('builder safe')\n")
        write(root / "tools/runtime_inspector/inspect_runtime_package.py", "print('inspector safe')\n")
        write(root / "tools/runtime_registry/list_runtime_runs.py", "print('registry safe')\n")
        write(root / "tools/sandbox_boundary/prepare_sandbox_run.py", "print('sandbox safe')\n")
        write(root / "examples/dry_run_packages/example.json", '{"mode": "dry_run"}\n')

    def test_minimal_repo_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            report = inspect_repo(root)
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["summary"]["errors"], 0)

    def test_missing_required_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            (root / "README.md").unlink()
            report = inspect_repo(root)
            self.assertEqual(report["status"], "failed")
            self.assertGreaterEqual(report["summary"]["errors"], 1)

    def test_public_private_leakage_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            write(root / "docs/guides/leak.md", "This mentions private-library in public docs.")
            report = inspect_repo(root)
            self.assertEqual(report["status"], "passed")
            self.assertGreaterEqual(report["summary"]["warnings"], 1)
            codes = {finding["code"] for finding in report["findings"]}
            self.assertIn("private_leakage_signal", codes)

    def test_dangerous_python_pattern_is_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            write(root / "tools/demo/unsafe.py", "import subprocess\n")
            report = inspect_repo(root)
            self.assertEqual(report["status"], "passed")
            codes = {finding["code"] for finding in report["findings"]}
            self.assertIn("dangerous_python_pattern", codes)

    def test_executable_examples_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            write(root / "examples/demo/run.py", "print('not allowed')\n")
            report = inspect_repo(root)
            self.assertEqual(report["status"], "failed")
            codes = {finding["code"] for finding in report["findings"]}
            self.assertIn("executable_example", codes)

    def test_blocked_private_path_is_not_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_minimal_repo(root)
            write(root / "alliance/kirigakure/private-library/leak.md", "password=secret")
            report = inspect_repo(root)
            self.assertEqual(report["status"], "passed")
            paths = {finding["path"] for finding in report["findings"]}
            self.assertFalse(any("kirigakure" in path for path in paths))
            self.assertTrue(is_blocked_path(root / "alliance/kirigakure/private-library/leak.md"))


if __name__ == "__main__":
    unittest.main()
