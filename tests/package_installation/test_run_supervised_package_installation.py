import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "tools"
    / "package_installation"
    / "run_supervised_package_installation.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "run_supervised_package_installation",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SupervisedPackageInstallationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()

        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Konoha Test"],
            cwd=self.repo,
            check=True,
        )

        (self.repo / "README.md").write_text(
            "# Base\n",
            encoding="utf-8",
        )
        (self.repo / ".gitignore").write_text(
            "sandbox/\n",
            encoding="utf-8",
        )
        subprocess.run(
            ["git", "add", "README.md", ".gitignore"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Base"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )

        self.base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        remote = Path(self.tmp.name) / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", str(remote)],
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(remote)],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=self.repo,
            check=True,
            text=True,
            capture_output=True,
        )

        self.direct_paths = [
            "docs/new-guide.md",
            "examples/package-installation-manifest.json",
        ]
        self.helper_paths = ["README.md"]
        self.final_paths = sorted(
            self.direct_paths + self.helper_paths
        )

        for relative in self.direct_paths:
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"direct file: {relative}\n",
                encoding="utf-8",
            )

        self.helper_path = (
            self.repo
            / "sandbox"
            / "tmp"
            / "package"
            / "apply.py"
        )
        self.helper_path.parent.mkdir(parents=True, exist_ok=True)
        self.write_helper()

        self.manifest = {
            "schema_version": "1.0.0",
            "report_type": (
                "supervised_package_installation_manifest"
            ),
            "installation_id": "test-package-installation",
            "expected_base_commit": self.base,
            "expected_branch": "main",
            "tracking_ref": "origin/main",
            "direct_repo_paths": self.direct_paths,
            "helper_modified_paths": self.helper_paths,
            "expected_public_paths": self.final_paths,
            "helper_path": "sandbox/tmp/package/apply.py",
            "helper_approval_token": "APPLY_TEST_PACKAGE_HELPER",
            "authority": {
                "manifest_is_not_permission": True,
                "install_token_required": True,
                "helper_is_bounded": True,
                "git_operations_blocked": True,
                "network_access_blocked": True,
                "private_context_blocked": True,
            },
        }

        self.manifest_path = (
            self.repo
            / "examples"
            / "package-installation-manifest.json"
        )
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.write_manifest()

    def tearDown(self):
        self.tmp.cleanup()

    def write_helper(
        self,
        *,
        mutate_direct=False,
        fail=False,
    ):
        direct_mutation = ""
        if mutate_direct:
            direct_mutation = """
Path("docs/new-guide.md").write_text(
    "helper mutated direct path\\n",
    encoding="utf-8",
)
"""

        exit_line = "raise SystemExit(1)" if fail else ""

        helper = f"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--repo-root", default=".")
parser.add_argument("--apply", action="store_true")
parser.add_argument("--approval-token", default="")
args = parser.parse_args()

if not args.apply:
    raise SystemExit(1)

if args.approval_token != "APPLY_TEST_PACKAGE_HELPER":
    raise SystemExit(1)

repo = Path(args.repo_root).resolve()
path = repo / "README.md"
text = path.read_text(encoding="utf-8")
marker = "## Package installed"

if marker not in text:
    path.write_text(
        text + "\\n" + marker + "\\n",
        encoding="utf-8",
    )

{direct_mutation}
{exit_line}
"""
        self.helper_path.write_text(
            textwrap.dedent(helper).lstrip("\n"),
            encoding="utf-8",
        )

    def write_manifest(self, payload=None):
        self.manifest_path.write_text(
            json.dumps(
                payload or self.manifest,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def output_path(self, name="report.json"):
        return self.repo / "sandbox" / "reports" / name

    def run_cli(
        self,
        *,
        apply=False,
        token="",
        output=None,
    ):
        command = [
            sys.executable,
            "-S",
            str(MODULE_PATH),
            "--repo-root",
            str(self.repo),
            "--manifest",
            str(self.manifest_path),
            "--output",
            str(output or self.output_path()),
            "--force",
            "--json",
        ]
        if apply:
            command.append("--apply")
        if token:
            command.extend(["--approval-token", token])

        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )

    def test_validate_manifest_accepts_exact_union(self):
        validated = self.module.validate_manifest(self.manifest)

        self.assertEqual(
            validated["expected_public_paths"],
            self.final_paths,
        )

    def test_validate_manifest_rejects_overlap(self):
        payload = deepcopy(self.manifest)
        payload["helper_modified_paths"].append(
            self.direct_paths[0]
        )
        payload["expected_public_paths"] = sorted(
            set(payload["direct_repo_paths"])
            | set(payload["helper_modified_paths"])
        )

        with self.assertRaisesRegex(
            self.module.InstallationError,
            "overlap",
        ):
            self.module.validate_manifest(payload)

    def test_validate_manifest_rejects_union_mismatch(self):
        payload = deepcopy(self.manifest)
        payload["expected_public_paths"] = self.direct_paths

        with self.assertRaisesRegex(
            self.module.InstallationError,
            "exact union",
        ):
            self.module.validate_manifest(payload)

    def test_validate_manifest_rejects_private_path(self):
        payload = deepcopy(self.manifest)
        payload["direct_repo_paths"].append(
            "vault/private.json"
        )
        payload["expected_public_paths"].append(
            "vault/private.json"
        )

        with self.assertRaisesRegex(
            self.module.InstallationError,
            "blocked context",
        ):
            self.module.validate_manifest(payload)

    def test_preview_reports_ready_without_mutation(self):
        before = (self.repo / "README.md").read_text(
            encoding="utf-8"
        )

        completed = self.run_cli()

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(
            report["status_code"],
            "READY_FOR_HELPER_APPLY",
        )
        self.assertFalse(report["installed"])
        self.assertEqual(
            (self.repo / "README.md").read_text(encoding="utf-8"),
            before,
        )

    def test_apply_installs_exact_union(self):
        completed = self.run_cli(
            apply=True,
            token=self.module.INSTALL_TOKEN,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["status_code"], "INSTALLED")
        self.assertTrue(report["installed"])
        self.assertEqual(
            report["scope"]["actual_after"],
            self.final_paths,
        )
        self.assertTrue(
            report["scope"]["direct_hashes_preserved"]
        )

    def test_second_apply_is_idempotent(self):
        first = self.run_cli(
            apply=True,
            token=self.module.INSTALL_TOKEN,
        )
        self.assertEqual(first.returncode, 0, first.stderr)

        second = self.run_cli(
            apply=True,
            token=self.module.INSTALL_TOKEN,
            output=self.output_path("second.json"),
        )

        self.assertEqual(second.returncode, 0, second.stderr)
        report = json.loads(second.stdout)
        self.assertEqual(report["status_code"], "INSTALLED")
        self.assertIsNone(report["helper"])

    def test_extra_public_path_blocks(self):
        (self.repo / "extra.txt").write_text(
            "unexpected\n",
            encoding="utf-8",
        )

        completed = self.run_cli()

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertEqual(
            report["status_code"],
            "BLOCKED_INSTALLATION",
        )
        self.assertIn("scope mismatch", report["blocker"])

    def test_staged_change_blocks(self):
        subprocess.run(
            ["git", "add", "docs/new-guide.md"],
            cwd=self.repo,
            check=True,
        )

        completed = self.run_cli()

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn("staged changes", report["blocker"])

    def test_missing_install_token_blocks_before_helper(self):
        before = (self.repo / "README.md").read_text(
            encoding="utf-8"
        )

        completed = self.run_cli(apply=True)

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn("--approval-token", report["blocker"])
        self.assertEqual(
            (self.repo / "README.md").read_text(encoding="utf-8"),
            before,
        )

    def test_helper_direct_path_mutation_blocks(self):
        self.write_helper(mutate_direct=True)

        completed = self.run_cli(
            apply=True,
            token=self.module.INSTALL_TOKEN,
        )

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertIn(
            "helper modified direct package paths",
            report["blocker"],
        )

    def test_output_outside_sandbox_blocks_without_file(self):
        unsafe = self.repo / "unsafe.json"

        completed = self.run_cli(output=unsafe)

        self.assertEqual(completed.returncode, 1)
        report = json.loads(completed.stdout)
        self.assertEqual(
            report["status_code"],
            "BLOCKED_INSTALLATION",
        )
        self.assertFalse(unsafe.exists())


if __name__ == "__main__":
    unittest.main()
