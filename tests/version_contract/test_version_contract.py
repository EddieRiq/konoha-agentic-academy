import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"tools"/"version_contract.py"

def load_module():
    spec=importlib.util.spec_from_file_location("version_contract",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

class VersionContractTests(unittest.TestCase):
    def setUp(self):
        self.module=load_module()

    def test_repository_contract_passes(self):
        # v4.0.1 release closure: product/candidate version and the last
        # public/installable release tag now intentionally converge on
        # v4.0.1. See test_candidate_version_ahead_of_installable_tag_is_accepted
        # below for the still-preserved BLOCK_4 FINDING #20 regression proof
        # that a candidate version MAY legally be ahead of the release tag.
        report=self.module.inspect(ROOT)
        self.assertEqual(report["status"],"passed")
        self.assertEqual(report["values"]["package_version"],"4.0.1")
        self.assertEqual(report["values"]["runtime_version"],"4.0.1")
        self.assertEqual(report["values"]["runtime_tag"],"v4.0.1")
        self.assertEqual(report["values"]["installer_tag"],"v4.0.1")

    def test_konoha_v4_cli_version_matches_current_release(self):
        # BLOCKER FIX: tools/konoha_v4/__init__.py.__version__ (what
        # `konoha --version` prints via the pyproject.toml console-script
        # entry point tools.konoha_v4.cli:main) must derive from the same
        # canonical tools/version.py VERSION as the managed distribution
        # surfaces, not an independent hardcoded value that can drift.
        completed = subprocess.run(
            [sys.executable, "-m", "tools.konoha_v4.cli", "--version"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "4.0.1")

    def test_candidate_version_ahead_of_installable_tag_is_accepted(self):
        # Synthetic isolation of the same scenario as
        # test_repository_contract_passes, independent of the real repo's
        # current numbers.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"tools").mkdir()
            (root/"scripts").mkdir()
            (root/"pyproject.toml").write_text('[project]\nversion = "4.0.0"\n',encoding="utf-8")
            (root/"tools/version.py").write_text('VERSION = "4.0.0"\nTAG = "v3.6.0"\n',encoding="utf-8")
            (root/"scripts/install.sh").write_text('VERSION="v3.6.0"\n',encoding="utf-8")
            report=self.module.inspect(root)
            self.assertEqual(report["status"],"passed")
            self.assertEqual(report["errors"],[])

    def test_detects_runtime_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"tools").mkdir()
            (root/"scripts").mkdir()
            (root/"pyproject.toml").write_text('[project]\nversion = "4.0.0"\n',encoding="utf-8")
            (root/"tools/version.py").write_text('VERSION = "3.6.0"\nTAG = "v3.6.0"\n',encoding="utf-8")
            (root/"scripts/install.sh").write_text('VERSION="v3.6.0"\n',encoding="utf-8")
            report=self.module.inspect(root)
            self.assertEqual(report["status"],"failed")
            self.assertTrue(any("runtime_version" in e for e in report["errors"]))

    def test_detects_release_tag_installer_tag_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"tools").mkdir()
            (root/"scripts").mkdir()
            (root/"pyproject.toml").write_text('[project]\nversion = "4.0.0"\n',encoding="utf-8")
            (root/"tools/version.py").write_text('VERSION = "4.0.0"\nTAG = "v3.6.0"\n',encoding="utf-8")
            (root/"scripts/install.sh").write_text('VERSION="v3.5.1"\n',encoding="utf-8")
            report=self.module.inspect(root)
            self.assertEqual(report["status"],"failed")
            self.assertTrue(any("runtime_tag" in e and "installer_tag" in e for e in report["errors"]))

if __name__=="__main__":
    unittest.main()
