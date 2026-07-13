import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "tools"
    / "product_experience"
    / "run_product_experience.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "product_experience_under_test",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ProductExperienceTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.workspace_rel = "sandbox/workspace"
        self.workspace = self.repo / self.workspace_rel

    def tearDown(self):
        self.tmp.cleanup()

    def write_workspace(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "missions").mkdir(exist_ok=True)
        (self.workspace / "workspace_manifest.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "workspace_type": (
                        "konoha_product_runtime_workspace"
                    ),
                }
            ),
            encoding="utf-8",
        )

    def mission(self, mission_id="mission-001"):
        self.write_workspace()
        mission = self.workspace / "missions" / mission_id
        (mission / "reports").mkdir(parents=True, exist_ok=True)
        (mission / "evidence" / "command_results").mkdir(
            parents=True,
            exist_ok=True,
        )
        return mission

    def write_json(self, path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def test_resolve_workspace_accepts_sandbox(self):
        resolved = self.module.resolve_workspace(
            self.repo,
            self.workspace_rel,
        )
        self.assertEqual(resolved, self.workspace.resolve())

    def test_resolve_workspace_rejects_repo_root(self):
        with self.assertRaises(
            self.module.ProductExperienceError
        ):
            self.module.resolve_workspace(self.repo, ".")

    def test_choose_latest_mission_uses_mtime(self):
        first = self.mission("mission-001")
        second = self.mission("mission-002")
        first.touch()
        second.touch()
        second_time = first.stat().st_mtime + 20
        import os
        os.utime(second, (second_time, second_time))
        self.assertEqual(
            self.module.choose_latest_mission(
                self.workspace / "missions"
            ).name,
            "mission-002",
        )

    def test_inspect_without_workspace_requires_quickstart(self):
        report = self.module.inspect_product(
            self.repo,
            self.workspace_rel,
        )
        self.assertEqual(
            report["status_code"],
            "QUICKSTART_REQUIRED",
        )
        self.assertIn(
            self.module.QUICKSTART_TOKEN,
            report["latest_mission"]["next_command"],
        )

    def test_quickstart_requires_confirmation(self):
        with self.assertRaisesRegex(
            self.module.ProductExperienceError,
            "confirm-quickstart",
        ):
            self.module.run_quickstart(
                self.repo,
                self.workspace_rel,
                human_actor="Eduardo",
                persona="calm_mentor",
                confirm_quickstart=False,
                approval_token=self.module.QUICKSTART_TOKEN,
            )

    def test_quickstart_requires_exact_token(self):
        with self.assertRaisesRegex(
            self.module.ProductExperienceError,
            "approval-token",
        ):
            self.module.run_quickstart(
                self.repo,
                self.workspace_rel,
                human_actor="Eduardo",
                persona="calm_mentor",
                confirm_quickstart=True,
                approval_token="WRONG",
            )

    def test_quickstart_rejects_unknown_persona(self):
        with self.assertRaisesRegex(
            self.module.ProductExperienceError,
            "persona",
        ):
            self.module.run_quickstart(
                self.repo,
                self.workspace_rel,
                human_actor="Eduardo",
                persona="unknown",
                confirm_quickstart=True,
                approval_token=self.module.QUICKSTART_TOKEN,
            )

    def test_quickstart_creates_workspace_and_state(self):
        report = self.module.run_quickstart(
            self.repo,
            self.workspace_rel,
            human_actor="Eduardo",
            persona="calm_mentor",
            confirm_quickstart=True,
            approval_token=self.module.QUICKSTART_TOKEN,
        )
        self.assertEqual(
            report["status_code"],
            "QUICKSTART_READY",
        )
        self.assertFalse(report["idempotent"])
        self.assertTrue(
            (self.workspace / "workspace_manifest.json").is_file()
        )
        self.assertTrue(
            (self.workspace / "product_experience.json").is_file()
        )

    def test_quickstart_same_state_is_idempotent(self):
        kwargs = dict(
            human_actor="Eduardo",
            persona="calm_mentor",
            confirm_quickstart=True,
            approval_token=self.module.QUICKSTART_TOKEN,
        )
        self.module.run_quickstart(
            self.repo,
            self.workspace_rel,
            **kwargs,
        )
        report = self.module.run_quickstart(
            self.repo,
            self.workspace_rel,
            **kwargs,
        )
        self.assertTrue(report["idempotent"])

    def test_quickstart_conflicting_actor_blocks(self):
        self.module.run_quickstart(
            self.repo,
            self.workspace_rel,
            human_actor="Eduardo",
            persona="calm_mentor",
            confirm_quickstart=True,
            approval_token=self.module.QUICKSTART_TOKEN,
        )
        with self.assertRaisesRegex(
            self.module.ProductExperienceError,
            "conflicts",
        ):
            self.module.run_quickstart(
                self.repo,
                self.workspace_rel,
                human_actor="Other",
                persona="calm_mentor",
                confirm_quickstart=True,
                approval_token=self.module.QUICKSTART_TOKEN,
            )

    def test_initialized_workspace_is_ready_for_first_mission(self):
        self.write_workspace()
        report = self.module.inspect_product(
            self.repo,
            self.workspace_rel,
        )
        self.assertEqual(
            report["status_code"],
            "READY_FOR_FIRST_MISSION",
        )

    def test_execution_evidence_routes_to_review(self):
        mission = self.mission()
        self.write_json(
            mission
            / "evidence"
            / "command_results"
            / "execution.json",
            {"status": "passed"},
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(stage["stage"], "READY_FOR_REVIEW")

    def test_approved_review_routes_to_teachback(self):
        mission = self.mission()
        self.write_json(
            mission
            / "reports"
            / "review_konoha_human_review_record.json",
            {
                "status": "passed",
                "review_decision": "approved",
                "human_approval": True,
            },
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(
            stage["stage"],
            "READY_FOR_TEACHBACK",
        )

    def test_changes_requested_routes_to_rework(self):
        mission = self.mission()
        self.write_json(
            mission
            / "reports"
            / "review_konoha_human_review_record.json",
            {
                "status": "passed",
                "review_decision": "changes_requested",
                "human_approval": False,
            },
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(
            stage["stage"],
            "REVIEW_CHANGES_REQUESTED",
        )

    def test_passed_teachback_routes_to_close(self):
        mission = self.mission()
        self.write_json(
            mission
            / "reports"
            / "tb_teachback_record.json",
            {
                "status": "passed",
                "result": "passed",
            },
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(
            stage["stage"],
            "READY_FOR_MISSION_CLOSE",
        )

    def test_incomplete_teachback_routes_to_status(self):
        mission = self.mission()
        self.write_json(
            mission
            / "reports"
            / "tb_teachback_record.json",
            {
                "status": "passed",
                "result": "needs_clarification",
            },
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(
            stage["stage"],
            "TEACHBACK_NEEDS_WORK",
        )

    def test_closed_mission_routes_to_new_mission(self):
        mission = self.mission()
        self.write_json(
            mission
            / "reports"
            / "close_mission_closure_report.json",
            {
                "status": "passed",
                "mission_status": "closed",
            },
        )
        stage = self.module.mission_stage(mission)
        self.assertEqual(stage["stage"], "MISSION_CLOSED")

    def test_main_json_emits_machine_readable_report(self):
        with patch("builtins.print") as print_mock:
            code = self.module.main(
                [
                    "welcome",
                    "--repo-root",
                    str(self.repo),
                    "--workspace-root",
                    self.workspace_rel,
                    "--json",
                ]
            )
        self.assertEqual(code, 0)
        payload = json.loads(print_mock.call_args.args[0])
        self.assertEqual(
            payload["status_code"],
            "QUICKSTART_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
