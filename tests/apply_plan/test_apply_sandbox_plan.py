import json
import tempfile
import unittest
from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "apply_plan" / "apply_sandbox_plan.py"
spec = importlib.util.spec_from_file_location("apply_sandbox_plan", MODULE_PATH)
applier = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(applier)


def make_run_with_plan(root: Path, run_id: str, intended_repo_path: str = "docs/proposed_note.md") -> tuple[Path, Path]:
    sandbox = root / "sandbox"
    run_dir = sandbox / "runs" / run_id
    proposed = run_dir / "proposed_outputs" / "docs" / "proposed_note.md"
    proposed.parent.mkdir(parents=True, exist_ok=True)
    proposed.write_text("# Proposed note\n", encoding="utf-8")

    manifest = {
        "schema_version": "0.1",
        "run_id": run_id,
        "mode": "dry_run",
        "execution": "blocked",
        "filesystem_mutation": "sandbox_only",
        "git_operations": "blocked",
        "adapter_execution": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
    }
    (run_dir / "sandbox_run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    plan = {
        "schema_version": "0.1",
        "plan_id": f"apply-plan-{run_id}",
        "mode": "dry_run",
        "run_id": run_id,
        "status": "proposed",
        "execution": "blocked",
        "filesystem_mutation": "sandbox_only",
        "git_operations": "blocked",
        "adapter_execution": "blocked",
        "private_context_access": "blocked",
        "network_access": "blocked",
        "planned_changes": [
            {
                "change_id": "change-001",
                "operation": "propose_file",
                "artifact_kind": "markdown",
                "sandbox_artifact_path": "proposed_outputs/docs/proposed_note.md",
                "intended_repo_path": intended_repo_path,
                "apply_status": "not_applied",
                "requires_human_approval": True,
                "execution": "blocked",
                "git_operations": "blocked",
            }
        ],
    }
    (run_dir / "apply_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    return sandbox, run_dir


class HumanApprovedApplyPlanTests(unittest.TestCase):
    def test_preview_does_not_write_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, run_dir = make_run_with_plan(root, "preview-run")

            result = applier.apply_sandbox_plan(
                sandbox_root=str(sandbox),
                run_id="preview-run",
                repo_root=str(repo),
                confirm_apply=False,
                approval_token="",
                allow_overwrite=False,
                write_report=True,
            )

            self.assertEqual(result["report"]["status"], "preview")
            self.assertFalse((repo / "docs" / "proposed_note.md").exists())
            self.assertTrue((run_dir / "human_approved_apply_report.json").exists())

    def test_confirmed_apply_writes_allowlisted_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, _ = make_run_with_plan(root, "apply-run")

            result = applier.apply_sandbox_plan(
                sandbox_root=str(sandbox),
                run_id="apply-run",
                repo_root=str(repo),
                confirm_apply=True,
                approval_token=applier.APPROVAL_TOKEN,
                allow_overwrite=False,
                write_report=True,
            )

            destination = repo / "docs" / "proposed_note.md"
            self.assertTrue(destination.exists())
            self.assertEqual(destination.read_text(encoding="utf-8"), "# Proposed note\n")
            self.assertEqual(result["report"]["repository_apply"], "applied")

    def test_confirmed_apply_requires_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, _ = make_run_with_plan(root, "token-run")

            with self.assertRaises(applier.ApplyPlanError):
                applier.apply_sandbox_plan(
                    sandbox_root=str(sandbox),
                    run_id="token-run",
                    repo_root=str(repo),
                    confirm_apply=True,
                    approval_token="wrong",
                    allow_overwrite=False,
                    write_report=False,
                )

    def test_rejects_private_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, _ = make_run_with_plan(
                root,
                "private-run",
                intended_repo_path="alliance/kirigakure/private.md",
            )

            with self.assertRaises(applier.ApplyPlanError):
                applier.apply_sandbox_plan(
                    sandbox_root=str(sandbox),
                    run_id="private-run",
                    repo_root=str(repo),
                    confirm_apply=False,
                    approval_token="",
                    allow_overwrite=False,
                    write_report=False,
                )

    def test_rejects_destination_outside_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, _ = make_run_with_plan(root, "outside-run", intended_repo_path="README.md")

            with self.assertRaises(applier.ApplyPlanError):
                applier.apply_sandbox_plan(
                    sandbox_root=str(sandbox),
                    run_id="outside-run",
                    repo_root=str(repo),
                    confirm_apply=False,
                    approval_token="",
                    allow_overwrite=False,
                    write_report=False,
                )

    def test_rejects_source_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            sandbox, run_dir = make_run_with_plan(root, "traversal-run")
            plan = json.loads((run_dir / "apply_plan.json").read_text(encoding="utf-8"))
            plan["planned_changes"][0]["sandbox_artifact_path"] = "proposed_outputs/../escape.md"
            (run_dir / "apply_plan.json").write_text(json.dumps(plan), encoding="utf-8")

            with self.assertRaises(applier.ApplyPlanError):
                applier.apply_sandbox_plan(
                    sandbox_root=str(sandbox),
                    run_id="traversal-run",
                    repo_root=str(repo),
                    confirm_apply=False,
                    approval_token="",
                    allow_overwrite=False,
                    write_report=False,
                )

    def test_rejects_overwrite_without_allow_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            destination = repo / "docs" / "proposed_note.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("existing\n", encoding="utf-8")
            sandbox, _ = make_run_with_plan(root, "overwrite-run")

            with self.assertRaises(applier.ApplyPlanError):
                applier.apply_sandbox_plan(
                    sandbox_root=str(sandbox),
                    run_id="overwrite-run",
                    repo_root=str(repo),
                    confirm_apply=True,
                    approval_token=applier.APPROVAL_TOKEN,
                    allow_overwrite=False,
                    write_report=False,
                )


if __name__ == "__main__":
    unittest.main()
