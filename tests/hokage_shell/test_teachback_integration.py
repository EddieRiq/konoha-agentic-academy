import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "hokage_shell" / "run_hokage_shell.py"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "hokage_shell_teachback_test",
        TOOL,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HokageTeachbackIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.workspace = self.root / "workspace"
        self.memory = self.root / "memory"
        self.repo.mkdir()
        (self.repo / "README.md").write_text(
            "# Test repo\n",
            encoding="utf-8",
        )
        self.paths = self.module.make_paths(
            str(self.repo),
            str(self.workspace),
            str(self.memory),
        )
        self.persona = self.module.DEFAULT_PERSONAS[
            "calm_mentor"
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_session_writes_teachback_manifest(self):
        session = self.module.create_session(
            self.paths,
            "Inspect repository evidence.",
            self.persona,
            "shell-teachback",
        )
        manifest = json.loads(
            (
                self.workspace
                / "missions"
                / session["mission_id"]
                / "mission_manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(manifest["teachback"]["required"])
        self.assertEqual(
            manifest["teachback"]["required_level"],
            2,
        )

    def test_confirmed_review_writes_human_review_record(self):
        mission_id = "shell-review"
        self.module.create_session(
            self.paths,
            "Review deterministic evidence.",
            self.persona,
            mission_id,
        )
        steps = (
            self.workspace
            / "missions"
            / mission_id
            / "step_reports"
        )
        steps.mkdir(parents=True, exist_ok=True)
        (steps / "001-review.md").write_text(
            "# Review evidence\n",
            encoding="utf-8",
        )

        rc = self.module.main(
            [
                "--repo-root",
                str(self.repo),
                "--workspace-root",
                str(self.workspace),
                "--memory-root",
                str(self.memory),
                "--plain",
                "review",
                "--mission-id",
                mission_id,
                "--confirm-review",
                "--approval-token",
                "RECORD_HOKAGE_REVIEW",
                "--decision",
                "approved",
                "--review-id",
                "human-review",
                "--review-summary",
                (
                    "The human reviewer approved the report "
                    "and documented the remaining limitations."
                ),
                "--human-actor",
                "eduardo",
                "--json",
            ]
        )
        self.assertEqual(rc, 0)
        record = (
            self.workspace
            / "missions"
            / mission_id
            / "reports"
            / "human-review_konoha_human_review_record.json"
        )
        payload = json.loads(record.read_text(encoding="utf-8"))
        self.assertEqual(
            payload["review_decision"],
            "approved",
        )
        self.assertTrue(payload["human_approval"])


if __name__ == "__main__":
    unittest.main()
