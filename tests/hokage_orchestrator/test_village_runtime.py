from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.hokage_orchestrator.village_runtime import (
    REQUIRED_DIRS,
    VillageInitializer,
    safe_village_name,
)


class VillageInitializerTests(unittest.TestCase):
    def test_safe_village_name_rejects_traversal(self):
        for value in ("../x", "..", "/tmp/x", "a/b", "a\\b"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    safe_village_name(value)

    def test_future_village_matches_trailing_slash_ignore_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(
                ["git", "init", "-q", str(repo)],
                check=True,
            )
            (repo / ".gitignore").write_text(
                "alliance/*/\n",
                encoding="utf-8",
            )
            (repo / "alliance").mkdir()

            initializer = VillageInitializer(repo_root=repo)
            status = initializer.inspect()

            self.assertTrue(status["git_ignored"])
            self.assertFalse(status["exists"])
            self.assertFalse(status["ready"])

    def test_inspection_is_evidence_only(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            initializer = VillageInitializer(repo_root=repo)
            with patch(
                "tools.hokage_orchestrator.village_runtime.git_ignored",
                return_value=True,
            ):
                status = initializer.inspect()
            self.assertFalse(status["ready"])
            self.assertTrue(
                status["authority"]["inspection_is_evidence_only"]
            )

    def test_exact_approval_required(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            initializer = VillageInitializer(repo_root=repo)
            with patch(
                "tools.hokage_orchestrator.village_runtime.git_ignored",
                return_value=True,
            ):
                with self.assertRaises(PermissionError):
                    initializer.initialize("WRONG")

    def test_initialization_creates_private_structure(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            initializer = VillageInitializer(repo_root=repo)
            with patch(
                "tools.hokage_orchestrator.village_runtime.git_ignored",
                return_value=True,
            ):
                result = initializer.initialize(
                    initializer.approval_phrase
                )
            self.assertTrue(result["ready"])
            for name in REQUIRED_DIRS:
                self.assertTrue(
                    (initializer.village_root / name).is_dir()
                )
            self.assertTrue(initializer.manifest_path.is_file())


if __name__ == "__main__":
    unittest.main()
