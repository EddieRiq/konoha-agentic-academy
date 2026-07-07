from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.runtime_builder.create_dry_run_package import (  # noqa: E402
    BuildRequest,
    build_runtime_package,
    main as builder_main,
    write_runtime_package,
)
from tools.runtime_validator.validate_runtime_package import validate_runtime_package  # noqa: E402


class DryRunPackageBuilderTests(unittest.TestCase):
    def test_build_package_passes_runtime_validator(self) -> None:
        request = BuildRequest(
            package_id="unit-test-package",
            mission_id="mission-unit-test-package",
            mission_title="Unit test dry-run package",
            scope="Generate a package for validator compatibility testing.",
            requested_by="unit-test",
            mission_charter_reference="tests/runtime_builder/test_create_dry_run_package.py",
            output=Path("sandbox/tmp/unit-test-package"),
        )

        package = build_runtime_package(request)
        result = validate_runtime_package(package)

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(package["mode"], "dry_run")
        self.assertFalse(package["execution_authorized"])
        self.assertFalse(package["safety_flags"]["shell_execution"])
        self.assertFalse(package["safety_flags"]["filesystem_mutation"])
        self.assertFalse(package["safety_flags"]["git_operations"])
        self.assertFalse(package["safety_flags"]["private_context_access"])

    def test_cli_generates_package_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "generated-package"
            exit_code = builder_main([
                "--title",
                "Generated package test",
                "--scope",
                "Generate a dry-run package inside a temporary test directory.",
                "--output",
                str(output_dir),
                "--allow-output-outside-sandbox",
            ])

            self.assertEqual(exit_code, 0)
            package_file = output_dir / "runtime_package.json"
            self.assertTrue(package_file.exists())

            package = json.loads(package_file.read_text(encoding="utf-8"))
            result = validate_runtime_package(package)
            self.assertTrue(result.passed, result.errors)

    def test_cli_refuses_existing_output_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_file = Path(tmp) / "runtime_package.json"
            output_file.write_text("{}", encoding="utf-8")

            exit_code = builder_main([
                "--title",
                "Overwrite refusal test",
                "--scope",
                "Attempt to overwrite an existing package.",
                "--output",
                str(output_file),
                "--allow-output-outside-sandbox",
            ])

            self.assertEqual(exit_code, 1)
            self.assertEqual(output_file.read_text(encoding="utf-8"), "{}")

    def test_cli_blocks_private_village_output(self) -> None:
        exit_code = builder_main([
            "--title",
            "Private path refusal test",
            "--scope",
            "Attempt to write into a private local Village path.",
            "--output",
            "alliance/kirigakure/generated/runtime_package.json",
            "--allow-output-outside-sandbox",
        ])

        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
