import importlib.util
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
        report=self.module.inspect(ROOT)
        self.assertEqual(report["status"],"passed")
        self.assertEqual(report["values"]["package_version"],"3.5.1")
        self.assertEqual(report["values"]["runtime_version"],"3.5.1")
        self.assertEqual(report["values"]["runtime_tag"],"v3.5.1")
        self.assertEqual(report["values"]["installer_tag"],"v3.5.1")

    def test_detects_runtime_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/"tools").mkdir()
            (root/"scripts").mkdir()
            (root/"pyproject.toml").write_text('[project]\nversion = "3.5.1"\n',encoding="utf-8")
            (root/"tools/version.py").write_text('VERSION = "3.4.0"\nTAG = "v3.4.0"\n',encoding="utf-8")
            (root/"scripts/install.sh").write_text('VERSION="v3.5.1"\n',encoding="utf-8")
            report=self.module.inspect(root)
            self.assertEqual(report["status"],"failed")
            self.assertTrue(report["errors"])

if __name__=="__main__":
    unittest.main()
