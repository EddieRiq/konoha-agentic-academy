import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.git_readiness.inspect_git_readiness import (
    build_report,
    is_allowed_git_args,
    parse_status_porcelain,
    summarize_status,
    tracked_private_paths,
)


class GitReadOnlyGateTests(unittest.TestCase):
    def test_allowed_git_args_are_read_only(self):
        self.assertTrue(is_allowed_git_args(("status", "--porcelain=v1")))
        self.assertTrue(is_allowed_git_args(("diff", "--name-only")))
        self.assertTrue(is_allowed_git_args(("ls-files",)))
        self.assertTrue(is_allowed_git_args(("rev-parse", "--show-toplevel")))
        self.assertTrue(is_allowed_git_args(("check-ignore", "-v", "sandbox/tmp/example.txt")))

    def test_disallowed_git_args_are_rejected(self):
        self.assertFalse(is_allowed_git_args(()))
        self.assertFalse(is_allowed_git_args(("status",)))
        self.assertFalse(is_allowed_git_args(("diff",)))
        self.assertFalse(is_allowed_git_args(("check-ignore", "sandbox/tmp/example.txt")))
        self.assertFalse(is_allowed_git_args(("unknown",)))

    def test_parse_status_porcelain(self):
        parsed = parse_status_porcelain(" M README.md\n?? scratch.txt\nA  docs/new.md\n")

        self.assertEqual(parsed[0]["category"], "modified")
        self.assertEqual(parsed[0]["path"], "README.md")
        self.assertEqual(parsed[1]["category"], "untracked")
        self.assertEqual(parsed[1]["path"], "scratch.txt")
        self.assertEqual(parsed[2]["category"], "modified")
        self.assertEqual(parsed[2]["path"], "docs/new.md")

    def test_summarize_status_blocks_dirty_by_default(self):
        entries = parse_status_porcelain(" M README.md\n?? scratch.txt\n")
        blockers, warnings = summarize_status(entries, allow_dirty=False)

        self.assertEqual(len(blockers), 2)
        self.assertEqual(warnings, [])

    def test_summarize_status_can_warn_when_dirty_allowed(self):
        entries = parse_status_porcelain(" M README.md\n?? scratch.txt\n")
        blockers, warnings = summarize_status(entries, allow_dirty=True)

        self.assertEqual(blockers, [])
        self.assertEqual(len(warnings), 2)

    def test_tracked_private_paths_are_detected(self):
        findings = tracked_private_paths(
            [
                "README.md",
                "alliance/example/private-library/source.md",
                "memory/local/session.json",
                "docs/guides/example.md",
                ".env",
            ]
        )

        self.assertIn("alliance/example/private-library/source.md", findings)
        self.assertIn("memory/local/session.json", findings)
        self.assertIn(".env", findings)
        self.assertNotIn("README.md", findings)


if __name__ == "__main__":
    unittest.main()
