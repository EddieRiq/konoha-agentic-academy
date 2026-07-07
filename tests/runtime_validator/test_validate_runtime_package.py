from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tools" / "runtime_validator" / "validate_runtime_package.py"
FIXTURES = REPO_ROOT / "tests" / "runtime_validator" / "fixtures"


class RuntimeValidatorTests(unittest.TestCase):
    def run_validator(self, fixture_name: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(FIXTURES / fixture_name)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_valid_package_passes(self) -> None:
        result = self.run_validator("valid_runtime_package.json")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("VALIDATION PASSED", result.stdout)
        self.assertIn("Execution: blocked", result.stdout)
        self.assertIn("Git operations: blocked", result.stdout)

    def test_invalid_execution_enabled_fails(self) -> None:
        result = self.run_validator("invalid_execution_enabled.json")
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("VALIDATION FAILED", result.stdout)
        self.assertIn("shell_execution must be false", result.stdout)
        self.assertIn("execution_allowed must be false", result.stdout)
        self.assertIn("invocation_allowed must be false", result.stdout)

    def test_json_output_is_machine_readable(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(FIXTURES / "valid_runtime_package.json"), "--json"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])
        self.assertEqual(payload["mode"], "dry_run")
        self.assertEqual(payload["safety_boundary"]["filesystem_mutation"], "blocked")


if __name__ == "__main__":
    unittest.main()
