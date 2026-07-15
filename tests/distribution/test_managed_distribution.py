import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
MANAGER = ROOT / "tools/distribution/manage_konoha_distribution.py"
SMOKE = ROOT / "tools/distribution/run_clean_install_smoke.py"
INSTALLER = ROOT / "scripts/install.sh"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ManagedDistributionTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module(
            "managed_distribution_test_module",
            MANAGER,
        )
        self.tmp = tempfile.TemporaryDirectory(
            prefix="konoha-distribution-test-",
            dir=Path.home(),
        )
        self.base = Path(self.tmp.name)
        self.root = self.base / "data" / "konoha-agentic-academy"
        self.venv = self.root / ".venv"
        self.bin_path = self.base / "bin" / "konoha"
        self.state_file = self.base / "state" / "konoha" / "install.json"
        self.root.mkdir(parents=True)
        (self.root / ".git").mkdir()
        (self.root / "tools").mkdir()
        (self.root / "tools/konoha_cli.py").write_text(
            "# cli\n",
            encoding="utf-8",
        )
        (self.root / "tools/version.py").write_text(
            'VERSION = "3.5.1"\n',
            encoding="utf-8",
        )
        (self.venv / "bin").mkdir(parents=True)
        (self.venv / "bin/python").write_text(
            "#!/bin/sh\n",
            encoding="utf-8",
        )
        self.bin_path.parent.mkdir(parents=True)
        self.bin_path.write_text(
            "#!/bin/sh\n",
            encoding="utf-8",
        )
        self.state = {
            "schema_version": "1.0.0",
            "report_type": "managed_konoha_install_state",
            "managed": True,
            "repository": "EddieRiq/konoha-agentic-academy",
            "version": "v3.3.0",
            "commit": "a" * 40,
            "install_root": str(self.root),
            "venv_root": str(self.venv),
            "bin_path": str(self.bin_path),
            "state_file": str(self.state_file),
            "marker_id": "b" * 32,
            "wrapper_sha256": hashlib.sha256(
                self.bin_path.read_bytes()
            ).hexdigest(),
            "installed_at": "2026-07-13T00:00:00+00:00",
        }
        self.marker = {
            "schema_version": "1.0.0",
            "report_type": "managed_konoha_install_marker",
            "repository": "EddieRiq/konoha-agentic-academy",
            "version": "v3.3.0",
            "commit": "a" * 40,
            "install_root": str(self.root),
            "marker_id": "b" * 32,
            "wrapper_sha256": self.state["wrapper_sha256"],
            "installed_at": "2026-07-13T00:00:00+00:00",
        }
        self.state_file.parent.mkdir(parents=True)
        self.state_file.write_text(
            json.dumps(self.state),
            encoding="utf-8",
        )
        (self.root / self.module.MARKER_NAME).write_text(
            json.dumps(self.marker),
            encoding="utf-8",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_version_accepts_semver_tag(self):
        self.assertEqual(
            self.module.parse_version("v3.3.0"),
            (3, 3, 0),
        )

    def test_parse_version_rejects_non_tag(self):
        with self.assertRaises(self.module.DistributionError):
            self.module.parse_version("3.3.0")

    def test_validate_state_accepts_managed_state(self):
        validated = self.module.validate_state(self.state)
        self.assertEqual(validated["version"], "v3.3.0")

    def test_validate_state_rejects_wrong_repository(self):
        payload = dict(self.state)
        payload["repository"] = "other/repo"
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "repository mismatch",
        ):
            self.module.validate_state(payload)

    def test_user_managed_path_rejects_outside_home(self):
        with self.assertRaises(self.module.DistributionError):
            self.module.ensure_user_managed_path(
                Path("/tmp/konoha-outside-home"),
                "install_root",
            )

    def test_load_state_rejects_marker_mismatch(self):
        marker = dict(self.marker)
        marker["marker_id"] = "c" * 32
        (self.root / self.module.MARKER_NAME).write_text(
            json.dumps(marker),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "identity mismatch",
        ):
            self.module.load_managed_state(self.state_file)

    def test_inspect_state_reports_healthy(self):
        responses = {
            ("rev-parse", "HEAD"): "a" * 40,
            (
                "describe",
                "--tags",
                "--exact-match",
                "HEAD",
            ): "v3.3.0",
            (
                "remote",
                "get-url",
                "origin",
            ): self.module.REPO_HTTPS,
            (
                "status",
                "--porcelain=v1",
            ): "",
        }

        with patch.object(
            self.module,
            "git_stdout",
            side_effect=lambda _root, *args: responses[args],
        ):
            report = self.module.inspect_state(self.state)

        self.assertTrue(report["healthy"])
        self.assertEqual(
            report["status_code"],
            "MANAGED_INSTALL_HEALTHY",
        )

    def test_inspect_state_reports_degraded_without_binary(self):
        self.bin_path.unlink()
        with patch.object(
            self.module,
            "git_stdout",
            side_effect=self.module.DistributionError("git unavailable"),
        ):
            report = self.module.inspect_state(self.state)
        self.assertFalse(report["healthy"])
        self.assertFalse(report["checks"]["binary_exists"])

    def test_upgrade_requires_network_before_mutation(self):
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "allow-network",
        ):
            self.module.perform_upgrade(
                self.state_file,
                self.state,
                target_version="v3.5.1",
                allow_network=False,
                confirm_upgrade=True,
                approval_token=self.module.UPGRADE_TOKEN,
            )

    def test_upgrade_requires_exact_token(self):
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "approval-token",
        ):
            self.module.perform_upgrade(
                self.state_file,
                self.state,
                target_version="v3.5.1",
                allow_network=True,
                confirm_upgrade=True,
                approval_token="WRONG",
            )

    def test_upgrade_rejects_same_or_older_version(self):
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "newer",
        ):
            self.module.perform_upgrade(
                self.state_file,
                self.state,
                target_version="v3.3.0",
                allow_network=True,
                confirm_upgrade=True,
                approval_token=self.module.UPGRADE_TOKEN,
            )

    def test_uninstall_requires_confirmation(self):
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "confirm-uninstall",
        ):
            self.module.perform_uninstall(
                self.state_file,
                self.state,
                confirm_uninstall=False,
                approval_token=self.module.UNINSTALL_TOKEN,
            )

    def test_uninstall_requires_exact_token(self):
        with self.assertRaisesRegex(
            self.module.DistributionError,
            "approval-token",
        ):
            self.module.perform_uninstall(
                self.state_file,
                self.state,
                confirm_uninstall=True,
                approval_token="WRONG",
            )

    def test_installer_has_valid_bash_syntax(self):
        completed = subprocess.run(
            ["bash", "-n", str(INSTALLER)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_installer_requires_explicit_token(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("INSTALL_KONOHA_CLI", source)
        self.assertIn("--confirm-install", source)
        self.assertIn("/.venv/", source)
        self.assertIn("/.konoha-managed-install.json", source)
        self.assertIn("PYTHONDONTWRITEBYTECODE=1", source)
        self.assertIn("canonical public Konoha repository", source)
        self.assertIn('TAG_TYPE', source)
        self.assertNotIn("git checkout -f", source)
        self.assertNotIn("git reset --hard", source)

    def test_pyproject_and_cli_version_are_aligned(self):
        pyproject = (ROOT / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        version = (ROOT / "tools/version.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('version = "3.5.1"', pyproject)
        self.assertIn('VERSION = "3.5.1"', version)



    def test_installer_fetches_annotated_tag_without_clone_warning_path(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn("git init --quiet", source)
        self.assertIn("refs/tags/$VERSION:refs/tags/$VERSION", source)
        self.assertIn("checkout --quiet --detach", source)
        self.assertNotIn("git clone", source)

    def test_installer_prints_quickstart_next_action(self):
        source = INSTALLER.read_text(encoding="utf-8")
        self.assertIn(
            "konoha quickstart --confirm-quickstart",
            source,
        )
        self.assertIn(
            "START_KONOHA_QUICKSTART",
            source,
        )

    def test_upgrade_checks_out_resolved_commit_quietly(self):
        source = MANAGER.read_text(encoding="utf-8")
        self.assertIn('"advice.detachedHead=false"', source)
        self.assertIn('"--quiet"', source)
        self.assertIn("target_commit", source)
        self.assertNotIn(
            '["git", "checkout", "--detach", target_version]',
            source,
        )

    def test_healthy_status_has_product_next_action(self):
        responses = {
            ("rev-parse", "HEAD"): "a" * 40,
            (
                "describe",
                "--tags",
                "--exact-match",
                "HEAD",
            ): "v3.3.0",
            (
                "remote",
                "get-url",
                "origin",
            ): self.module.REPO_HTTPS,
            (
                "status",
                "--porcelain=v1",
            ): "",
        }
        with patch.object(
            self.module,
            "git_stdout",
            side_effect=lambda _root, *args: responses[args],
        ):
            report = self.module.inspect_state(self.state)
        self.assertEqual(report["next_action"], "Run `konoha next`.")

    def test_upgrade_report_declares_product_reentry(self):
        source = MANAGER.read_text(encoding="utf-8")
        self.assertIn(
            "Run `konoha welcome` and `konoha next`.",
            source,
        )

class CleanInstallSmokeTests(unittest.TestCase):
    def test_clean_install_smoke_passes(self):
        module = load_module(
            "clean_install_smoke_test_module",
            SMOKE,
        )
        report = module.execute_smoke(
            ROOT,
            expected_version="3.5.1",
        )
        self.assertEqual(
            report["status_code"],
            "CLEAN_INSTALL_SMOKE_PASSED",
        )
        self.assertEqual(report["observed_version"], "3.5.1")


if __name__ == "__main__":
    unittest.main()
