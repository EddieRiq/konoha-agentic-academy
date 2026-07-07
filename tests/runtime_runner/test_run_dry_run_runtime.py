from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.runtime_inspector.inspect_runtime_package import inspect_runtime_package  # noqa: E402
from tools.runtime_runner.run_dry_run_runtime import (  # noqa: E402
    main as runner_main,
    run_dry_run_runtime,
)
from tools.runtime_validator.validate_runtime_package import validate_runtime_package  # noqa: E402


class DryRunRuntimeRunnerTests(unittest.TestCase):
    def test_runner_creates_valid_inspectable_package_inside_sandbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp) / "sandbox"

            summary = run_dry_run_runtime(
                title="Unit test dry-run runtime",
                scope="Generate, validate, and inspect a package inside a temp sandbox.",
                run_id="unit-runtime-run",
                sandbox_root=sandbox_root,
            )

            self.assertEqual(summary["status"], "passed")
            run_dir = sandbox_root / "runs" / "unit-runtime-run"

            package_path = run_dir / "runtime_package.json"
            validation_report_path = run_dir / "validation_report.json"
            inspection_report_path = run_dir / "inspection_report.json"
            summary_path = run_dir / "runtime_run_summary.json"
            sandbox_manifest_path = run_dir / "sandbox_run_manifest.json"

            self.assertTrue(package_path.exists())
            self.assertTrue(validation_report_path.exists())
            self.assertTrue(inspection_report_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(sandbox_manifest_path.exists())

            package = json.loads(package_path.read_text(encoding="utf-8"))
            validation = validate_runtime_package(package)
            inspection = inspect_runtime_package(package)

            self.assertTrue(validation.passed, validation.errors)
            self.assertTrue(inspection.passed, [finding.message for finding in inspection.findings])
            self.assertFalse(package["execution_authorized"])
            self.assertFalse(package["safety_flags"]["shell_execution"])
            self.assertEqual(package["runtime_state"]["state"], "review_ready")

    def test_cli_prints_passed_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp) / "sandbox"
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = runner_main(
                    [
                        "--title",
                        "CLI dry-run runtime",
                        "--scope",
                        "Exercise the CLI from a unit test.",
                        "--run-id",
                        "cli-runtime-run",
                        "--sandbox-root",
                        str(sandbox_root),
                    ]
                )

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("DRY-RUN RUNTIME PASSED", output)
            self.assertIn("Execution: blocked", output)
            self.assertIn("Git operations: blocked", output)
            self.assertTrue((sandbox_root / "runs" / "cli-runtime-run" / "runtime_run_summary.json").exists())

    def test_cli_json_output_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp) / "sandbox"
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = runner_main(
                    [
                        "--title",
                        "JSON dry-run runtime",
                        "--scope",
                        "Exercise JSON output from a unit test.",
                        "--run-id",
                        "json-runtime-run",
                        "--sandbox-root",
                        str(sandbox_root),
                        "--json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["safety_boundary"]["execution"], "blocked")
            self.assertEqual(payload["safety_boundary"]["filesystem_mutation"], "sandbox_only")

    def test_path_traversal_run_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp) / "sandbox"
            stdout = StringIO()

            with redirect_stdout(stdout):
                exit_code = runner_main(
                    [
                        "--title",
                        "Traversal test",
                        "--scope",
                        "Reject unsafe run identifiers.",
                        "--run-id",
                        "../escape",
                        "--sandbox-root",
                        str(sandbox_root),
                    ]
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("DRY-RUN RUNTIME FAILED", stdout.getvalue())
            self.assertFalse((Path(tmp) / "escape").exists())

    def test_existing_run_requires_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sandbox_root = Path(tmp) / "sandbox"

            first = runner_main(
                [
                    "--title",
                    "Existing run test",
                    "--scope",
                    "Create the run once.",
                    "--run-id",
                    "existing-run",
                    "--sandbox-root",
                    str(sandbox_root),
                ]
            )

            second = runner_main(
                [
                    "--title",
                    "Existing run test",
                    "--scope",
                    "Attempt to create the same run without force.",
                    "--run-id",
                    "existing-run",
                    "--sandbox-root",
                    str(sandbox_root),
                ]
            )

            third = runner_main(
                [
                    "--title",
                    "Existing run test",
                    "--scope",
                    "Overwrite the same run with force.",
                    "--run-id",
                    "existing-run",
                    "--sandbox-root",
                    str(sandbox_root),
                    "--force",
                ]
            )

            self.assertEqual(first, 0)
            self.assertEqual(second, 1)
            self.assertEqual(third, 0)


if __name__ == "__main__":
    unittest.main()
