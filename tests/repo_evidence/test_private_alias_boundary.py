"""Synthetic public aliases must not make excluded material public."""
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest import mock

from tools.repo_evidence.acquire_repo_evidence import Authorization, acquire_repo_evidence
from tools.repo_evidence import acquire_repo_evidence as acquisition


class PrivateAliasTests(unittest.TestCase):
    def test_git_alias_and_swap_after_enumeration_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "private").mkdir()
            hidden = root / "private" / "source.py"
            hidden.write_text("def synthetic_private_marker(): return 1\n")
            alias = root / "alias.py"
            alias.symlink_to(hidden)
            pack = acquire_repo_evidence(root, Authorization("human", "fixture"))
            self.assertNotIn("alias.py", pack.scan_paths)
            alias.unlink()
            alias.write_text("def public(): return 1\n")
            original = acquisition._read_and_classify_all
            def swap(repo, eligible):
                alias.unlink()
                alias.symlink_to(hidden)
                return original(repo, eligible)
            with mock.patch.object(acquisition, "_read_and_classify_all", side_effect=swap):
                with self.assertRaises(acquisition.RepositoryEvidenceError):
                    acquire_repo_evidence(root, Authorization("human", "fixture"))

    def test_public_symlink_cannot_read_excluded_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "excluded").mkdir()
            (root / "excluded" / "source.py").write_text("def private_fixture_marker(): return 1\n")
            (root / "alias.py").symlink_to(root / "excluded" / "source.py")
            pack = acquire_repo_evidence(root, Authorization("human", "synthetic", ("excluded",)))
            self.assertNotIn("alias.py", pack.scan_paths)
            self.assertFalse(pack.symbols)

    def test_private_directories_are_excluded_without_gitignore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("private", "local", "secrets"):
                (root / name).mkdir()
                (root / name / "source.py").write_text("def private_fixture_marker(): return 1\n")
            pack = acquire_repo_evidence(root, Authorization("human", "synthetic"))
            self.assertEqual(pack.scan_paths, [])
