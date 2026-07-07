import json
import tempfile
import unittest
from pathlib import Path

from tools.runtime_registry.list_runtime_runs import build_report, inspect_run, list_runs, main


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


class RuntimeRunRegistryTests(unittest.TestCase):
    def test_empty_sandbox_returns_no_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = list_runs(Path(tmp))
            self.assertEqual(records, [])

    def test_passed_run_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "ok-run"
            run_dir.mkdir(parents=True)

            write_json(run_dir / "sandbox_run_manifest.json", {
                "mode": "dry_run",
                "execution": "blocked",
                "filesystem_mutation": "sandbox only",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "adapter_execution": "blocked",
                "network_access": "blocked",
            })
            write_json(run_dir / "runtime_package.json", {"package_id": "ok-run"})
            write_json(run_dir / "validation_report.json", {"status": "passed"})
            write_json(run_dir / "inspection_report.json", {"status": "passed"})
            write_json(run_dir / "runtime_run_summary.json", {
                "mode": "dry_run",
                "validation": {"passed": True},
                "inspection": {"passed": True},
                "safety_boundary": {
                    "execution": "blocked",
                    "filesystem_mutation": "sandbox only",
                    "git_operations": "blocked",
                    "private_context_access": "blocked",
                    "adapter_execution": "blocked",
                    "network_access": "blocked",
                },
            })

            record = inspect_run(run_dir, root)
            self.assertEqual(record.state, "passed")
            self.assertEqual(record.blockers, [])

    def test_missing_summary_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "missing-summary"
            run_dir.mkdir(parents=True)

            write_json(run_dir / "sandbox_run_manifest.json", {
                "mode": "dry_run",
                "execution": "blocked",
                "filesystem_mutation": "sandbox only",
                "git_operations": "blocked",
                "private_context_access": "blocked",
                "adapter_execution": "blocked",
                "network_access": "blocked",
            })

            record = inspect_run(run_dir, root)
            self.assertEqual(record.state, "incomplete_or_blocked")
            self.assertIn("missing_runtime_run_summary", record.blockers)
            self.assertIn("missing_runtime_package", record.blockers)

    def test_unsafe_execution_flag_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "unsafe"
            run_dir.mkdir(parents=True)

            write_json(run_dir / "runtime_run_summary.json", {
                "mode": "dry_run",
                "validation": {"passed": True},
                "inspection": {"passed": True},
                "safety_boundary": {
                    "execution": "enabled",
                    "filesystem_mutation": "sandbox only",
                    "git_operations": "blocked",
                    "private_context_access": "blocked",
                    "adapter_execution": "blocked",
                    "network_access": "blocked",
                },
            })

            record = inspect_run(run_dir, root)
            self.assertEqual(record.state, "incomplete_or_blocked")
            self.assertIn("execution_not_blocked", record.blockers)

    def test_build_report_counts_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "incomplete"
            run_dir.mkdir(parents=True)

            records = list_runs(root)
            report = build_report(root, records)

            self.assertEqual(report["run_count"], 1)
            self.assertEqual(report["state_counts"]["incomplete_or_blocked"], 1)
            self.assertEqual(report["safety"]["filesystem_mutation"], "read_only")

    def test_cli_returns_success_for_empty_sandbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = main(["--sandbox-root", tmp])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
