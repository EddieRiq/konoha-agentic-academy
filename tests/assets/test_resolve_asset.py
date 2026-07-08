import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "tools" / "assets" / "resolve_asset.py"


def load_module():
    spec = importlib.util.spec_from_file_location("resolve_asset", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class AssetResolverTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_registry_asset(self, root: Path, logical_name: str, rel: str, content: str):
        (root / Path(rel).parent).mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(content, encoding="utf-8")
        registry = {
            "schema_version": "1.0.0",
            "assets": {
                logical_name: {
                    "path": rel,
                    "type": "ascii",
                    "description": "test asset",
                }
            },
        }
        (root / "asset_registry.json").write_text(json.dumps(registry), encoding="utf-8")

    def test_resolves_public_generic_asset(self):
        public_root = self.root / "shinobi" / "assets" / "generic"
        self.write_registry_asset(
            public_root,
            "status.waiting_user_input",
            "ascii/status/waiting_user_input.txt",
            "[?] waiting",
        )
        roots = self.module.default_asset_roots(self.root, None, None, public_root)
        resolution = self.module.resolve_asset("status.waiting_user_input", roots)
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(resolution.source_tier, "public_generic")
        self.assertIn("waiting", resolution.content_preview)

    def test_local_village_overrides_public_asset(self):
        public_root = self.root / "public"
        village_root = self.root / "village"
        self.write_registry_asset(public_root, "status.blocked", "ascii/status/blocked.txt", "public")
        self.write_registry_asset(village_root, "status.blocked", "ascii/status/blocked.txt", "local")
        roots = self.module.default_asset_roots(self.root, village_root, None, public_root)
        resolution = self.module.resolve_asset("status.blocked", roots)
        self.assertEqual(resolution.source_tier, "local_village")
        self.assertEqual(resolution.content_preview, "local")
        self.assertIn("$VILLAGE_ASSETS", resolution.display_path)

    def test_unknown_asset_uses_text_fallback(self):
        roots = self.module.default_asset_roots(self.root, None, None, self.root / "missing")
        resolution = self.module.resolve_asset("status.ready_for_teachback", roots)
        self.assertEqual(resolution.status, "fallback")
        self.assertEqual(resolution.source_tier, "text_fallback")
        self.assertIn("teachback", resolution.content_preview.lower())

    def test_rejects_invalid_logical_name(self):
        roots = self.module.default_asset_roots(self.root, None, None, self.root / "missing")
        with self.assertRaises(ValueError):
            self.module.resolve_asset("../secret", roots)

    def test_rejects_registry_path_traversal(self):
        public_root = self.root / "public"
        public_root.mkdir(parents=True)
        registry = {
            "schema_version": "1.0.0",
            "assets": {
                "status.blocked": {
                    "path": "../secret.txt",
                    "type": "ascii",
                    "description": "bad",
                }
            },
        }
        (public_root / "asset_registry.json").write_text(json.dumps(registry), encoding="utf-8")
        roots = self.module.default_asset_roots(self.root, None, None, public_root)
        with self.assertRaises(ValueError):
            self.module.resolve_asset("status.blocked", roots)

    def test_cli_writes_report_under_sandbox_reports(self):
        public_root = self.root / "public"
        sandbox = self.root / "sandbox"
        self.write_registry_asset(public_root, "status.closed", "ascii/status/closed.txt", "[OK]")
        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--logical-name",
                "status.closed",
                "--repo-root",
                str(self.root),
                "--public-assets-root",
                str(public_root),
                "--sandbox-root",
                str(sandbox),
                "--write-report",
                "--json",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "resolved")
        report_path = Path(report["report_path"])
        self.assertTrue(report_path.exists())
        self.assertTrue(str(report_path).endswith("_asset_resolution_report.json"))

    def test_report_declares_no_authority(self):
        public_root = self.root / "public"
        self.write_registry_asset(public_root, "status.closed", "ascii/status/closed.txt", "[OK]")
        roots = self.module.default_asset_roots(self.root, None, None, public_root)
        resolution = self.module.resolve_asset("status.closed", roots)
        report = self.module.build_report(resolution, self.root, self.root / "sandbox", False)
        self.assertTrue(report["authority"]["asset_resolution_is_evidence_only"])
        self.assertEqual(report["boundaries"]["git_operations"], "blocked")


if __name__ == "__main__":
    unittest.main()
