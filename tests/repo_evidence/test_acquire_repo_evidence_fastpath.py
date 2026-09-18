"""Correctness tests for the Git-index-based enumeration fast path in
tools/repo_evidence/acquire_repo_evidence.py (Gate C1 performance
correction).

These are correctness tests only - no timing/performance assertions here
(the real-repo benchmark is a separate, manually-run, foreground
measurement; encoding a wall-clock threshold into a unit test would make
the suite flaky across machines and CI environments).

Every scenario compares the Git fast path's observable behavior against the
documented invariants: a tracked file stays in scan scope even if it later
becomes gitignored; a tracked-but-deleted file participates in
scan_scope_digest via MISSING_TRACKED rather than being silently dropped;
symlink safety is always a real, unconditional filesystem check, never
inferred from Git's own index mode; and the non-Git walk fallback keeps
working unchanged.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.repo_evidence.acquire_repo_evidence import (
    Authorization,
    MISSING_TRACKED_SENTINEL,
    acquire_repo_evidence,
    git_identity,
    is_evidence_current,
)

_AUTH = Authorization(authorized_by="test", authorization_note="fastpath correctness test")


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(["init", "-q"], root)
    _git(["add", "-A"], root)
    _git(["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], root)


class TrackedButDeletedParticipatesInFingerprintTest(unittest.TestCase):
    """Council correction: a tracked-but-deleted file must never be
    silently excluded from scan_scope_digest."""

    def test_present_to_deleted_is_detected_as_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 2\n", encoding="utf-8")
            _init_repo(root)
            pack = acquire_repo_evidence(root, _AUTH)
            self.assertEqual(pack.missing_tracked_files, [])

            (root / "b.py").unlink()
            self.assertFalse(is_evidence_current(pack, root))

    def test_reacquired_pack_records_missing_tracked_and_sentinel(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 2\n", encoding="utf-8")
            _init_repo(root)
            (root / "b.py").unlink()

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertIn("b.py", pack.missing_tracked_files)
            self.assertIn("b.py", pack.scan_paths)
            self.assertTrue(
                any(u["path"] == "b.py" and u["reason"] == "tracked_path_deleted_in_worktree"
                    for u in pack.unknowns)
            )
            self.assertTrue(is_evidence_current(pack, root))

    def test_deleted_to_still_deleted_remains_current(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 2\n", encoding="utf-8")
            _init_repo(root)
            (root / "b.py").unlink()
            pack = acquire_repo_evidence(root, _AUTH)

            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")  # no-op rewrite
            self.assertTrue(is_evidence_current(pack, root))

    def test_deleted_to_restored_is_detected_as_stale(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 2\n", encoding="utf-8")
            _init_repo(root)
            (root / "b.py").unlink()
            pack = acquire_repo_evidence(root, _AUTH)

            (root / "b.py").write_text("VALUE = 2\n", encoding="utf-8")
            self.assertFalse(is_evidence_current(pack, root))

            restored_pack = acquire_repo_evidence(root, _AUTH)
            self.assertEqual(restored_pack.missing_tracked_files, [])
            self.assertTrue(is_evidence_current(restored_pack, root))


class GitignoreSemanticsTest(unittest.TestCase):
    """Approved semantics: --exclude-standard only ever prunes --others, so
    a tracked file stays in scope even if a later .gitignore pattern would
    otherwise match it."""

    def test_tracked_file_stays_in_scope_when_later_gitignored(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_repo(root)
            (root / ".gitignore").write_text("a.py\nignored.txt\n", encoding="utf-8")
            (root / "ignored.txt").write_text("nope\n", encoding="utf-8")
            (root / "visible.txt").write_text("yes\n", encoding="utf-8")

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertIn("a.py", pack.scan_paths)
            self.assertNotIn("ignored.txt", pack.scan_paths)
            self.assertIn("visible.txt", pack.scan_paths)
            self.assertIn(".gitignore", pack.scan_paths)


class SymlinkSafetyViaGitFastPathTest(unittest.TestCase):
    """Git is used only for path enumeration - symlink safety is always a
    real, unconditional filesystem check, never inferred from Git's index
    mode."""

    def test_untracked_symlink_file_escaping_root_is_refused(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_repo(root)
            outside = Path(outside_td)
            (outside / "secret.txt").write_text("nope\n", encoding="utf-8")
            (root / "escape_link.txt").symlink_to(outside / "secret.txt")

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertNotIn("escape_link.txt", pack.scan_paths)
            reasons = {u["path"]: u["reason"] for u in pack.unknowns}
            self.assertEqual(reasons.get("escape_link.txt"), "symlink_file_escape_refused")

    def test_untracked_symlinked_directory_is_not_followed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub" / "c.py").write_text("X = 1\n", encoding="utf-8")
            _init_repo(root)
            (root / "linked_dir").symlink_to(root / "sub")

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertFalse(any(p.startswith("linked_dir/") for p in pack.scan_paths))
            reasons = {u["path"]: u["reason"] for u in pack.unknowns}
            self.assertEqual(reasons.get("linked_dir"), "symlink_dir_not_followed")

    def test_untracked_symlinked_directory_escaping_root_is_refused(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_repo(root)
            outside = Path(outside_td)
            (outside / "outdir").mkdir()
            (outside / "outdir" / "x.py").write_text("Y = 1\n", encoding="utf-8")
            (root / "escape_dir").symlink_to(outside / "outdir")

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertFalse(any(p.startswith("escape_dir") for p in pack.scan_paths))
            reasons = {u["path"]: u["reason"] for u in pack.unknowns}
            self.assertEqual(reasons.get("escape_dir"), "symlink_dir_escape_refused")

    def test_tracked_file_swapped_for_symlink_without_restaging_is_caught(self):
        """Git's index still records this path as a tracked regular file -
        the fast path must never trust that mode and must catch the real,
        current on-disk symlink."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside_td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_repo(root)
            outside = Path(outside_td)
            (outside / "secret.txt").write_text("nope\n", encoding="utf-8")
            (root / "a.py").unlink()
            (root / "a.py").symlink_to(outside / "secret.txt")

            pack = acquire_repo_evidence(root, _AUTH)
            reasons = {u["path"]: u["reason"] for u in pack.unknowns}
            self.assertEqual(reasons.get("a.py"), "symlink_file_escape_refused")


class GeneratedDirsViaGitFastPathTest(unittest.TestCase):
    def test_accidentally_tracked_generated_dir_is_still_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "a.cpython.pyc").write_text("junk\n", encoding="utf-8")
            _git(["init", "-q"], root)
            _git(["add", "-A", "-f"], root)
            _git(["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"], root)

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertFalse(any(p.startswith("__pycache__/") for p in pack.scan_paths))


class NonGitFallbackTest(unittest.TestCase):
    def test_non_git_repo_uses_walk_fallback_and_has_no_missing_tracked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub" / "b.py").write_text("VALUE = 2\n", encoding="utf-8")

            vcs, _, _ = git_identity(root)
            self.assertEqual(vcs, "none")

            pack = acquire_repo_evidence(root, _AUTH)
            self.assertEqual(sorted(pack.scan_paths), ["a.py", "sub/b.py"])
            self.assertEqual(pack.missing_tracked_files, [])
            self.assertTrue(is_evidence_current(pack, root))


class DeterminismTest(unittest.TestCase):
    def test_repeated_acquisition_of_unchanged_repo_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "b.py").write_text("import a\n", encoding="utf-8")
            _init_repo(root)

            first = acquire_repo_evidence(root, _AUTH)
            second = acquire_repo_evidence(root, _AUTH)
            self.assertEqual(first.pack_id, second.pack_id)
            self.assertEqual(first.scan_scope_digest, second.scan_scope_digest)


class MissingTrackedSentinelShapeTest(unittest.TestCase):
    def test_sentinel_is_not_a_valid_sha256_hex_digest(self):
        self.assertNotEqual(len(MISSING_TRACKED_SENTINEL), 64)
        with self.assertRaises(ValueError):
            int(MISSING_TRACKED_SENTINEL, 16)


if __name__ == "__main__":
    unittest.main()
