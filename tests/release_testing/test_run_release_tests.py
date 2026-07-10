import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "tools" / "release_testing" / "run_release_tests.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_release_tests", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PASSING_TEST = """import unittest

class PassingTest(unittest.TestCase):
    def test_passes(self):
        self.assertTrue(True)
"""

FAILING_TEST = """import unittest

class FailingTest(unittest.TestCase):
    def test_fails(self):
        self.assertEqual(1, 2)
"""


class CanonicalReleaseTestGateTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.tests_root = self.repo / "tests"
        self.tests_root.mkdir(parents=True)
        (self.repo / "sandbox").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def make_suite(self, name, content=PASSING_TEST):
        suite = self.tests_root / name
        suite.mkdir(parents=True)
        (suite / "test_sample.py").write_text(content, encoding="utf-8")
        return suite

    def test_discovers_immediate_suites_without_init_files(self):
        self.make_suite("alpha")
        self.make_suite("beta")
        (self.tests_root / "__pycache__").mkdir()
        (self.tests_root / "notes").mkdir()
        (self.tests_root / "notes" / "README.md").write_text("not a test", encoding="utf-8")
        suites = self.module.discover_suite_directories(self.tests_root)
        self.assertEqual([suite.name for suite in suites], ["alpha", "beta"])
        self.assertFalse((self.tests_root / "alpha" / "__init__.py").exists())

    def test_aggregates_passing_suites(self):
        self.make_suite("alpha")
        self.make_suite("beta")
        report = self.module.build_report(self.repo, self.tests_root, timeout_seconds=30)
        self.assertTrue(report["passed"])
        self.assertEqual(report["summary"]["selected_suite_count"], 2)
        self.assertEqual(report["summary"]["passed_suite_count"], 2)
        self.assertEqual(report["summary"]["test_count"], 2)

    def test_failure_does_not_stop_later_suite(self):
        self.make_suite("a_failing", FAILING_TEST)
        self.make_suite("z_passing", PASSING_TEST)
        report = self.module.build_report(self.repo, self.tests_root, timeout_seconds=30)
        self.assertFalse(report["passed"])
        self.assertEqual([item["suite"] for item in report["suites"]], ["a_failing", "z_passing"])
        self.assertFalse(report["suites"][0]["passed"])
        self.assertTrue(report["suites"][1]["passed"])
        self.assertEqual(report["summary"]["failed_suite_count"], 1)
        self.assertEqual(report["summary"]["test_count"], 2)

    def test_cli_returns_nonzero_and_json_on_failure(self):
        self.make_suite("failing", FAILING_TEST)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo-root", str(self.repo), "--json"],
            text=True,
            capture_output=True,
            timeout=30,
        )
        self.assertEqual(proc.returncode, 1, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["summary"]["failed_suite_count"], 1)

    def test_suite_filter_runs_only_requested_suite(self):
        self.make_suite("alpha")
        self.make_suite("beta")
        report = self.module.build_report(
            self.repo,
            self.tests_root,
            timeout_seconds=30,
            requested_suites=["beta"],
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["summary"]["discovered_suite_count"], 2)
        self.assertEqual(report["summary"]["selected_suite_count"], 1)
        self.assertEqual(report["suites"][0]["suite"], "beta")

    def test_output_path_is_restricted_to_sandbox(self):
        allowed = self.module.validate_output_path(
            self.repo, Path("sandbox/reports/release-tests.json")
        )
        self.assertEqual(
            allowed,
            (self.repo / "sandbox" / "reports" / "release-tests.json").resolve(),
        )
        with self.assertRaises(self.module.ReleaseTestGateError):
            self.module.validate_output_path(
                self.repo, Path("reports/outside-sandbox.json")
            )


if __name__ == "__main__":
    unittest.main()
