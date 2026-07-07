import json
import tempfile
import unittest
from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "artifact_writer" / "write_sandbox_artifact.py"
spec = importlib.util.spec_from_file_location("write_sandbox_artifact", MODULE_PATH)
writer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(writer)


def make_manifest(run_dir: Path, run_id: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
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


class SandboxArtifactWriterTests(unittest.TestCase):
    def test_writes_artifact_apply_plan_and_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            run_dir = sandbox / "runs" / run_id
            make_manifest(run_dir, run_id)

            result = writer.write_sandbox_artifact(
                sandbox_root=str(sandbox),
                run_id=run_id,
                artifact_path_arg="docs/proposed_note.md",
                content="# Proposed note\n",
                artifact_kind="markdown",
                intended_repo_path="docs/proposed_note.md",
                force=False,
            )

            artifact = run_dir / "proposed_outputs" / "docs" / "proposed_note.md"
            self.assertTrue(artifact.exists())
            self.assertEqual(artifact.read_text(encoding="utf-8"), "# Proposed note\n")
            self.assertTrue((run_dir / "apply_plan.json").exists())
            self.assertTrue((run_dir / "artifact_write_report.json").exists())
            self.assertEqual(result["report"]["execution"], "blocked")
            self.assertEqual(result["report"]["repository_apply"], "blocked")

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            make_manifest(sandbox / "runs" / run_id, run_id)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(
                    sandbox_root=str(sandbox),
                    run_id=run_id,
                    artifact_path_arg="../escape.md",
                    content="bad",
                    artifact_kind="markdown",
                    intended_repo_path="UNASSIGNED",
                    force=False,
                )

    def test_rejects_absolute_artifact_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            make_manifest(sandbox / "runs" / run_id, run_id)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(
                    sandbox_root=str(sandbox),
                    run_id=run_id,
                    artifact_path_arg=str(Path(tmp) / "escape.md"),
                    content="bad",
                    artifact_kind="markdown",
                    intended_repo_path="UNASSIGNED",
                    force=False,
                )

    def test_rejects_unsupported_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            make_manifest(sandbox / "runs" / run_id, run_id)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(
                    sandbox_root=str(sandbox),
                    run_id=run_id,
                    artifact_path_arg="script.py",
                    content="print('bad')",
                    artifact_kind="text",
                    intended_repo_path="UNASSIGNED",
                    force=False,
                )

    def test_rejects_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            (sandbox / "runs" / run_id).mkdir(parents=True)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(
                    sandbox_root=str(sandbox),
                    run_id=run_id,
                    artifact_path_arg="docs/proposed_note.md",
                    content="# Proposed note\n",
                    artifact_kind="markdown",
                    intended_repo_path="UNASSIGNED",
                    force=False,
                )

    def test_rejects_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            make_manifest(sandbox / "runs" / run_id, run_id)

            kwargs = dict(
                sandbox_root=str(sandbox),
                run_id=run_id,
                artifact_path_arg="docs/proposed_note.md",
                content="# Proposed note\n",
                artifact_kind="markdown",
                intended_repo_path="UNASSIGNED",
            )

            writer.write_sandbox_artifact(force=False, **kwargs)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(force=False, **kwargs)

            writer.write_sandbox_artifact(force=True, **kwargs)

    def test_validates_json_artifact_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp) / "sandbox"
            run_id = "valid-run"
            make_manifest(sandbox / "runs" / run_id, run_id)

            with self.assertRaises(writer.ArtifactWriterError):
                writer.write_sandbox_artifact(
                    sandbox_root=str(sandbox),
                    run_id=run_id,
                    artifact_path_arg="reports/bad.json",
                    content="{not-json}",
                    artifact_kind="json",
                    intended_repo_path="UNASSIGNED",
                    force=False,
                )

            writer.write_sandbox_artifact(
                sandbox_root=str(sandbox),
                run_id=run_id,
                artifact_path_arg="reports/good.json",
                content='{"ok": true}',
                artifact_kind="json",
                intended_repo_path="UNASSIGNED",
                force=False,
            )
            self.assertTrue((sandbox / "runs" / run_id / "proposed_outputs" / "reports" / "good.json").exists())


if __name__ == "__main__":
    unittest.main()
