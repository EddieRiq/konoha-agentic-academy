import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[2] / "tools" / "local_model_audit" / "manage_local_model_audit.py"
    spec = importlib.util.spec_from_file_location("manage_local_model_audit", path)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class LocalModelAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "README.md").write_text("# Demo Repo\n\nOld status.\n", encoding="utf-8")
        (self.repo / "CHANGELOG.md").write_text("## [Unreleased]\n\n### Added\n\n", encoding="utf-8")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "roadmap.md").write_text("# Roadmap\n", encoding="utf-8")
        (self.repo / "tools" / "beta_runtime").mkdir(parents=True)
        (self.repo / "tools" / "beta_runtime" / "run_konoha_beta.py").write_text("print('x')\n", encoding="utf-8")
        self.m = load_module()

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, args):
        cwd = Path.cwd()
        try:
            import os
            os.chdir(self.repo)
            return self.m.main(args)
        finally:
            import os
            os.chdir(cwd)

    def test_profile_writes_output_with_token(self):
        out = self.root / "profile.json"
        rc = self.run_cli([
            "profile", "--repo-root", ".", "--sandbox-root", "./sandbox",
            "--output", str(out), "--confirm-profile",
            "--approval-token", "PROFILE_LOCAL_COMPUTER", "--force", "--json"
        ])
        self.assertEqual(rc, 0)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["report_type"], "local_computer_profile")
        self.assertIn("python_version", data["runtime"])

    def test_recommend_blocks_bad_token(self):
        out = self.root / "rec.json"
        rc = self.run_cli([
            "recommend", "--output", str(out), "--confirm-recommendation",
            "--approval-token", "WRONG", "--json"
        ])
        self.assertEqual(rc, 1)
        self.assertFalse(out.exists())

    def test_install_plan_writes_no_execution_plan(self):
        out = self.root / "install.json"
        rc = self.run_cli([
            "install-plan", "--output", str(out), "--confirm-plan",
            "--approval-token", "PLAN_OLLAMA_INSTALL", "--force", "--json"
        ])
        self.assertEqual(rc, 0)
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertTrue(data["authority"]["install_plan_is_not_permission"])
        self.assertIn("ollama.com/install.sh", data["manual_command_for_user_review"])

    def test_mock_audit_generates_patch_plan(self):
        outdir = self.root / "audit"
        rc = self.run_cli([
            "audit-repo", "--repo-root", ".", "--audit-id", "test-audit",
            "--model", "mock", "--output-dir", str(outdir), "--mock-local-model",
            "--confirm-audit", "--approval-token", "RUN_LOCAL_MODEL_AUDIT",
            "--force", "--json"
        ])
        self.assertEqual(rc, 0)
        audit = json.loads((outdir / "test-audit_repo_consistency_audit.json").read_text(encoding="utf-8"))
        plan = json.loads((outdir / "test-audit_repo_patch_plan.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(audit["inconsistencies"]), 1)
        self.assertGreaterEqual(len(plan["operations"]), 1)

    def test_apply_doc_patch_changes_docs_once(self):
        outdir = self.root / "audit"
        self.run_cli([
            "audit-repo", "--repo-root", ".", "--audit-id", "test-audit",
            "--model", "mock", "--output-dir", str(outdir), "--mock-local-model",
            "--confirm-audit", "--approval-token", "RUN_LOCAL_MODEL_AUDIT",
            "--force", "--json"
        ])
        report = self.root / "apply.json"
        rc = self.run_cli([
            "apply-doc-patch", "--repo-root", ".", "--patch-plan", str(outdir / "test-audit_repo_patch_plan.json"),
            "--output", str(report), "--confirm-apply", "--approval-token", "APPLY_LOCAL_MODEL_DOC_PATCH",
            "--force", "--json"
        ])
        self.assertEqual(rc, 0)
        readme = (self.repo / "README.md").read_text(encoding="utf-8")
        self.assertIn("Konoha Beta Local Model Audit", readme)
        # idempotent second apply should skip markers, not duplicate
        rc2 = self.run_cli([
            "apply-doc-patch", "--repo-root", ".", "--patch-plan", str(outdir / "test-audit_repo_patch_plan.json"),
            "--output", str(report), "--confirm-apply", "--approval-token", "APPLY_LOCAL_MODEL_DOC_PATCH",
            "--force", "--json"
        ])
        self.assertEqual(rc2, 0)
        readme2 = (self.repo / "README.md").read_text(encoding="utf-8")
        self.assertEqual(readme2.count("Konoha Beta Local Model Audit"), 1)

    def test_forbidden_paths_not_in_inventory(self):
        (self.repo / "alliance" / "kirigakure").mkdir(parents=True)
        (self.repo / "alliance" / "kirigakure" / "secret.md").write_text("secret", encoding="utf-8")
        files = self.m.repo_file_inventory(self.repo)
        self.assertNotIn("alliance/kirigakure/secret.md", files)

    def test_states(self):
        rc = self.run_cli(["states", "--json"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
