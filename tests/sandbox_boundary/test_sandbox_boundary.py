from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from tools.sandbox_boundary.prepare_sandbox_run import (
    MANIFEST_FILENAME,
    main,
    prepare_sandbox_run,
)
from tools.sandbox_boundary.sandbox_guard import (
    SandboxBoundaryError,
    sandbox_subdir,
    validate_safe_id,
)


class SandboxBoundaryTests(unittest.TestCase):
    def test_validate_safe_id_accepts_plain_identifier(self) -> None:
        self.assertEqual(validate_safe_id("run-001", "run_id"), "run-001")

    def test_validate_safe_id_rejects_traversal(self) -> None:
        with self.assertRaises(SandboxBoundaryError):
            validate_safe_id("../escape", "run_id")

    def test_sandbox_subdir_rejects_nested_segment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with self.assertRaises(SandboxBoundaryError):
                sandbox_subdir(root, "runs", "bad/segment")

    def test_prepare_sandbox_run_writes_manifest_inside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sandbox"
            manifest_path = prepare_sandbox_run(
                sandbox_root=root,
                run_id="unit-test-run",
                mission_title="Unit test sandbox run",
            )

            self.assertTrue(manifest_path.exists())
            self.assertEqual(manifest_path.name, MANIFEST_FILENAME)
            self.assertTrue(str(manifest_path.resolve()).startswith(str(root.resolve())))

            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "dry_run")
            self.assertEqual(payload["execution"], "blocked")
            self.assertEqual(payload["filesystem_mutation"], "sandbox_only")
            self.assertEqual(payload["git_operations"], "blocked")
            self.assertEqual(payload["adapter_execution"], "blocked")
            self.assertEqual(payload["private_context_access"], "blocked")
            self.assertEqual(payload["network_access"], "blocked")

    def test_prepare_sandbox_run_requires_force_for_existing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sandbox"
            prepare_sandbox_run(
                sandbox_root=root,
                run_id="same-run",
                mission_title="First run",
            )

            with self.assertRaises(SandboxBoundaryError):
                prepare_sandbox_run(
                    sandbox_root=root,
                    run_id="same-run",
                    mission_title="Second run",
                )

    def test_cli_returns_zero_for_valid_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "sandbox"
            exit_code = main(
                [
                    "--sandbox-root",
                    str(root),
                    "--run-id",
                    "cli-run",
                    "--mission-title",
                    "CLI run",
                ]
            )
            self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
