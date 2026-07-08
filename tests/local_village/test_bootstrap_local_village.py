import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.local_village import bootstrap_local_village as tool


class LocalVillageBootstrapTests(unittest.TestCase):
    def test_profile_preview_does_not_write_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "profile.json"
            code = tool.main([
                "profile",
                "--repo-root", str(tmp_path),
                "--village-root", str(tmp_path / "kirigakure"),
                "--village-name", "kirigakure",
                "--profile-id", "profile-smoke",
                "--output", str(output),
            ])
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())

    def test_confirmed_profile_writes_output_with_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "profile.json"
            code = tool.main([
                "profile",
                "--repo-root", str(tmp_path),
                "--village-root", str(tmp_path / "kirigakure"),
                "--village-name", "kirigakure",
                "--profile-id", "profile-smoke",
                "--confirm-profile",
                "--approval-token", tool.PROFILE_TOKEN,
                "--output", str(output),
                "--force",
            ])
            self.assertEqual(code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["boundaries"]["git_operations"], "blocked")
            self.assertFalse(payload["privacy"]["env_files_read"])

    def test_bad_profile_token_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = tool.main([
                "profile",
                "--repo-root", tmp,
                "--village-root", str(Path(tmp) / "kirigakure"),
                "--village-name", "kirigakure",
                "--confirm-profile",
                "--approval-token", "WRONG",
            ])
            self.assertEqual(code, 1)

    def test_bootstrap_preview_does_not_create_village(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kirigakure"
            code = tool.main([
                "bootstrap",
                "--repo-root", tmp,
                "--village-root", str(root),
                "--village-name", "kirigakure",
                "--bootstrap-id", "bootstrap-smoke",
            ])
            self.assertEqual(code, 0)
            self.assertFalse((root / "config" / "local_village_config.json").exists())

    def test_confirmed_bootstrap_creates_private_skeleton(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kirigakure"
            code = tool.main([
                "bootstrap",
                "--repo-root", tmp,
                "--village-root", str(root),
                "--village-name", "kirigakure",
                "--bootstrap-id", "bootstrap-smoke",
                "--confirm-bootstrap",
                "--approval-token", tool.BOOTSTRAP_TOKEN,
                "--force",
            ])
            self.assertEqual(code, 0)
            self.assertTrue((root / "README.md").exists())
            self.assertTrue((root / "config" / "local_village_config.json").exists())
            self.assertTrue((root / "memory" / "vault" / "10-requests").exists())
            report = root / "reports" / "bootstrap-smoke_local_village_bootstrap_report.json"
            self.assertTrue(report.exists())
            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["authority"]["local_config_does_not_authorize_execution"], True)

    def test_bad_bootstrap_token_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kirigakure"
            code = tool.main([
                "bootstrap",
                "--repo-root", tmp,
                "--village-root", str(root),
                "--village-name", "kirigakure",
                "--confirm-bootstrap",
                "--approval-token", "WRONG",
            ])
            self.assertEqual(code, 1)
            self.assertFalse((root / "README.md").exists())

    def test_doctor_reports_missing_before_bootstrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "kirigakure"
            code = tool.main([
                "doctor",
                "--village-root", str(root),
                "--json",
            ])
            self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
