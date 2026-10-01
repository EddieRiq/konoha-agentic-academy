import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "konoha-ci.yml"
CANONICAL_RELATIVE = "tools/release_testing/run_release_tests.py"
CANONICAL_COMMAND = f"python {CANONICAL_RELATIVE}"

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


def workflow_run_commands(text):
    """Return the run: commands of the workflow, joining `run: |` blocks."""
    commands = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith("- run:"):
            stripped = stripped[2:]
        if stripped.startswith("run:"):
            value = stripped[len("run:"):].strip()
            if value in ("|", ">"):
                indent = len(lines[index]) - len(lines[index].lstrip())
                block = []
                index += 1
                while index < len(lines):
                    line = lines[index]
                    if line.strip() and len(line) - len(line.lstrip()) <= indent:
                        break
                    block.append(line.strip())
                    index += 1
                commands.append(" ".join(part.rstrip("\\").strip() for part in block if part))
                continue
            commands.append(value)
        index += 1
    return commands


class CiFullSuiteRoutingTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.commands = workflow_run_commands(self.text)

    def test_full_suite_step_invokes_canonical_runner(self):
        self.assertIn(CANONICAL_COMMAND, self.commands)
        self.assertTrue((REPO_ROOT / CANONICAL_RELATIVE).is_file())

    def test_workflow_has_no_root_unittest_discovery(self):
        self.assertNotIn("unittest discover", self.text)
        for command in self.commands:
            self.assertNotIn("-m unittest", command)

    def test_integrated_smoke_step_remains_independent(self):
        smoke = [c for c in self.commands if "tools/integration/run_integrated_smoke_tests.py" in c]
        self.assertEqual(len(smoke), 1)
        self.assertNotIn(CANONICAL_RELATIVE, smoke[0])


class CiCommandSurfacesNonPackageFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        tests_root = self.repo / "tests"
        tests_root.mkdir(parents=True)
        script_target = self.repo / CANONICAL_RELATIVE
        script_target.parent.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / CANONICAL_RELATIVE, script_target)

        package_suite = tests_root / "a_package"
        package_suite.mkdir()
        (package_suite / "__init__.py").write_text("", encoding="utf-8")
        (package_suite / "test_sample.py").write_text(PASSING_TEST, encoding="utf-8")
        for name, content in (("b_failing", FAILING_TEST), ("c_passing", PASSING_TEST)):
            suite = tests_root / name
            suite.mkdir()
            (suite / "test_sample.py").write_text(content, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_in_repo(self, argv):
        return subprocess.run(
            argv,
            cwd=self.repo,
            text=True,
            capture_output=True,
            timeout=60,
        )

    def test_ci_command_fails_on_non_package_suite_and_runs_later_suites(self):
        commands = [c for c in workflow_run_commands(WORKFLOW.read_text(encoding="utf-8"))
                    if CANONICAL_RELATIVE in c]
        self.assertEqual(len(commands), 1)
        argv = shlex.split(commands[0])
        self.assertEqual(argv[0], "python")
        proc = self.run_in_repo([sys.executable, *argv[1:]])
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("PASS a_package", proc.stdout)
        self.assertIn("FAIL b_failing", proc.stdout)
        self.assertIn("PASS c_passing", proc.stdout)
        self.assertIn("failed suites: 1", proc.stdout)

    def test_root_discovery_misses_the_same_failure(self):
        proc = self.run_in_repo(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Ran 1 test", proc.stderr)


if __name__ == "__main__":
    unittest.main()
