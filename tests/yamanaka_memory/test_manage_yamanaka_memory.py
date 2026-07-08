import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "yamanaka_memory" / "manage_yamanaka_memory.py"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_yamanaka_memory", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class YamanakaMemoryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"
        self.memory = self.root / "memory" / "vault"
        self.mission_id = "mission-alpha"
        self.mission = self.workspace / "missions" / self.mission_id
        for rel in ["plans", "reports", "approvals", "evidence", "outputs", "context"]:
            (self.mission / rel).mkdir(parents=True, exist_ok=True)
        (self.mission / "mission_manifest.json").write_text(
            json.dumps(
                {
                    "mission_id": self.mission_id,
                    "title": "Mission Alpha",
                    "scope": "Validate Yamanaka memory capture.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (self.mission / "mission_status.json").write_text(
            json.dumps({"status": "ready_for_memory"}, indent=2),
            encoding="utf-8",
        )
        (self.mission / "mission_notification_state.json").write_text(
            json.dumps({"state": "ready_for_review"}, indent=2),
            encoding="utf-8",
        )
        (self.mission / "evidence" / "review.md").write_text("# Review\n", encoding="utf-8")
        (self.mission / "reports" / "report.json").write_text('{"ok": true}\n', encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, args):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.module.main(args)
        return code, stdout.getvalue()

    def test_init_creates_vault_directories(self):
        code, out = self.run_cli(["init", "--memory-root", str(self.memory)])
        self.assertEqual(code, 0, out)
        self.assertTrue((self.memory / "10-missions").is_dir())
        self.assertTrue((self.memory / "60-context-packs").is_dir())
        self.assertTrue((self.memory / "README.md").is_file())

    def test_capture_preview_does_not_write_note(self):
        code, out = self.run_cli(
            [
                "capture-mission",
                "--workspace-root",
                str(self.workspace),
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--capture-id",
                "preview",
            ]
        )
        self.assertEqual(code, 0, out)
        self.assertIn("YAMANAKA MEMORY CAPTURE PREVIEW", out)
        self.assertFalse((self.memory / "10-missions").exists())

    def test_capture_confirmed_writes_note_and_report(self):
        code, out = self.run_cli(
            [
                "capture-mission",
                "--workspace-root",
                str(self.workspace),
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--capture-id",
                "capture-001",
                "--human-actor",
                "eduardo",
                "--confirm-capture",
                "--approval-token",
                "RECORD_YAMANAKA_MEMORY",
                "--force",
            ]
        )
        self.assertEqual(code, 0, out)
        note = self.memory / "10-missions" / "mission-alpha_capture-001.md"
        report = self.memory / "_reports" / "capture-001_yamanaka_memory_capture_report.json"
        self.assertTrue(note.is_file())
        self.assertTrue(report.is_file())
        self.assertIn("Mission Memory Note", note.read_text(encoding="utf-8"))
        data = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(data["status"], "passed")
        self.assertEqual(data["mission_id"], self.mission_id)

    def test_capture_rejects_wrong_token(self):
        code, out = self.run_cli(
            [
                "capture-mission",
                "--workspace-root",
                str(self.workspace),
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--capture-id",
                "bad-token",
                "--confirm-capture",
                "--approval-token",
                "WRONG",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("YAMANAKA MEMORY CAPTURE FAILED", out)

    def test_context_pack_preview_does_not_write(self):
        self.run_cli(["init", "--memory-root", str(self.memory)])
        code, out = self.run_cli(
            [
                "build-context-pack",
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--context-pack-id",
                "pack-preview",
            ]
        )
        self.assertEqual(code, 0, out)
        self.assertIn("YAMANAKA CONTEXT PACK PREVIEW", out)
        self.assertFalse((self.memory / "60-context-packs" / "pack-preview.md").exists())

    def test_context_pack_confirmed_writes_pack_and_manifest(self):
        self.run_cli(
            [
                "capture-mission",
                "--workspace-root",
                str(self.workspace),
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--capture-id",
                "capture-002",
                "--confirm-capture",
                "--approval-token",
                "RECORD_YAMANAKA_MEMORY",
                "--force",
            ]
        )
        code, out = self.run_cli(
            [
                "build-context-pack",
                "--memory-root",
                str(self.memory),
                "--mission-id",
                self.mission_id,
                "--context-pack-id",
                "pack-001",
                "--purpose",
                "Unit test context pack.",
                "--confirm-build",
                "--approval-token",
                "BUILD_CONTEXT_PACK",
                "--force",
            ]
        )
        self.assertEqual(code, 0, out)
        pack = self.memory / "60-context-packs" / "pack-001.md"
        manifest = self.memory / "60-context-packs" / "pack-001.manifest.json"
        self.assertTrue(pack.is_file())
        self.assertTrue(manifest.is_file())
        self.assertIn("Context packs are not permission", pack.read_text(encoding="utf-8"))
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["context_pack_id"], "pack-001")

    def test_index_and_inspect(self):
        self.run_cli(["init", "--memory-root", str(self.memory)])
        code, out = self.run_cli(["index", "--memory-root", str(self.memory), "--json"])
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["index_type"], "yamanaka_memory_index")
        self.assertTrue((self.memory / "_index" / "yamanaka_memory_index.json").is_file())

        code, out = self.run_cli(["inspect", "--memory-root", str(self.memory), "--json"])
        self.assertEqual(code, 0, out)
        inspect = json.loads(out)
        self.assertEqual(inspect["status"], "passed")
        self.assertIn("_index", inspect["counts"])


if __name__ == "__main__":
    unittest.main()
