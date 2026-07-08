import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "tools" / "config_validator" / "validate_konoha_config.py"
EXAMPLE = REPO_ROOT / "konoha.config.example.json"


class ConfigValidatorTests(unittest.TestCase):
    def run_validator(self, path: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(TOOL), str(path), *extra],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def load_example(self) -> dict:
        return json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def write_temp_config(self, data: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
        with tmp:
            json.dump(data, tmp)
        return Path(tmp.name)

    def test_valid_example_passes(self):
        result = self.run_validator(EXAMPLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CONFIG VALIDATION PASSED", result.stdout)

    def test_json_output_passes(self):
        result = self.run_validator(EXAMPLE, "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["safety"]["git_push"], "blocked")

    def test_execution_must_be_blocked(self):
        data = self.load_example()
        data["safety"]["execution_blocked"] = False
        path = self.write_temp_config(data)
        try:
            result = self.run_validator(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("execution_blocked", result.stdout)
        finally:
            path.unlink(missing_ok=True)

    def test_allowed_paths_must_not_include_private_context(self):
        data = self.load_example()
        data["paths"]["allowed_apply_destinations"].append("alliance/kirigakure")
        path = self.write_temp_config(data)
        try:
            result = self.run_validator(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("private path", result.stdout)
        finally:
            path.unlink(missing_ok=True)

    def test_absolute_paths_are_rejected(self):
        data = self.load_example()
        data["sandbox"]["root"] = "C:/unsafe/sandbox"
        path = self.write_temp_config(data)
        try:
            result = self.run_validator(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("safe repo-relative path", result.stdout)
        finally:
            path.unlink(missing_ok=True)

    def test_approval_tokens_are_exact(self):
        data = self.load_example()
        data["approvals"]["git_staging_token"] = "STAGE"
        path = self.write_temp_config(data)
        try:
            result = self.run_validator(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("staging token", result.stdout)
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
