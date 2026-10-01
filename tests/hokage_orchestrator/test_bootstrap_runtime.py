from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools.hokage_orchestrator import bootstrap_runtime
from tools.hokage_orchestrator.mission_decision import ProviderSelectionError

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/hokage_orchestrator/bootstrap_runtime.py"
HOKAGE_SCRIPT = ROOT / "tools/hokage_orchestrator/run_conversational_hokage.py"
BOOTSTRAP_FIXTURE = Path(__file__).resolve().with_name("bootstrap_fixture.py")

# Captured at import, before any test installs a patch.
REAL_COLLECT = bootstrap_runtime.HokageBootstrapRuntime.__dict__["collect"]


def load_module():
    spec = importlib.util.spec_from_file_location("bootstrap_runtime_test", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BootstrapRuntimeTests(unittest.TestCase):
    def test_complete_first_use_and_reentry(self):
        module = load_module()

        def runner(args, timeout=20):
            text = " ".join(args)
            if "ollama list" in text:
                return {
                    "exit_code": 0,
                    "stdout": "NAME ID SIZE MODIFIED\nqwen2.5-coder:1.5b x 986MB now\n",
                    "stderr": "",
                    "timed_out": False,
                }
            return {
                "exit_code": 0,
                "stdout": "ok\n",
                "stderr": "",
                "timed_out": False,
            }

        with tempfile.TemporaryDirectory() as temp:
            runtime = module.HokageBootstrapRuntime(
                state_root=Path(temp),
                actor="Eduardo",
                command_runner=runner,
            )
            first = runtime.collect()
            second = runtime.collect()
            self.assertTrue(first["state"]["first_use"])
            self.assertFalse(second["state"]["first_use"])
            self.assertEqual(second["state"]["session_count"], 2)
            self.assertEqual(len(first["snapshot"]["providers"]), 3)
            self.assertEqual(
                first["snapshot"]["budget"]["minimum_savings_percent"],
                30,
            )

    def test_recommendation_profiles(self):
        module = load_module()
        low = module.HokageBootstrapRuntime.recommend_profile({
            "memory_bytes": 7 * 1024**3,
            "gpu": {"detected": False},
        })
        balanced = module.HokageBootstrapRuntime.recommend_profile({
            "memory_bytes": 12 * 1024**3,
            "gpu": {"detected": False},
        })
        self.assertEqual(low["profile"], "light")
        self.assertEqual(balanced["profile"], "balanced")


class SyntheticBootstrapBoundaryTests(unittest.TestCase):
    """The conversational test fixture replaces only collect(); the real
    selector, capabilities and Charter path still decide on its evidence."""

    MISSION_TEXT = "Revisá este repositorio sin modificarlo."

    def setUp(self):
        self.hokage = load_path("run_conversational_hokage_bootstrap", HOKAGE_SCRIPT)
        self.fixture = load_path("hokage_bootstrap_fixture", BOOTSTRAP_FIXTURE)
        self.runtime_class = self.hokage.HokageBootstrapRuntime
        # No earlier test may leak its collect() patch into this one.
        self.assertIs(self.runtime_class.__dict__["collect"], REAL_COLLECT)
        for name in ("_provider_probe", "_ollama_probe", "hardware_snapshot"):
            patcher = mock.patch.object(
                self.runtime_class,
                name,
                side_effect=AssertionError(f"live discovery called: {name}"),
            )
            patcher.start()
            self.addCleanup(patcher.stop)

    def make_shell(self, root: Path):
        repo = root / "repo"
        repo.mkdir()
        return self.hokage.ConversationalHokage(
            repo_root=repo,
            workspace_root=root / "workspace",
            state_root=root / "runtime",
            memory_root=root / "obsidian",
            actor="Eduardo",
        )

    def test_ready_synthetic_ollama_proposes_charter_without_live_discovery(self):
        collect = self.fixture.install_synthetic_bootstrap(
            self,
            self.runtime_class,
        )
        with tempfile.TemporaryDirectory() as tmp:
            shell = self.make_shell(Path(tmp))
            result = shell.propose(self.MISSION_TEXT)
        collect.assert_called_once()
        self.assertEqual(result["status_code"], "CHARTER_PROPOSED")
        selection = shell.pending_decision["selection"]
        self.assertEqual(selection["provider"], "ollama")
        self.assertEqual(selection["model"], self.fixture.DEFAULT_TEST_MODEL)
        self.assertEqual(selection["selection_source"], "provider_skill_ollama_only")
        self.assertEqual(selection["provider_readiness"], ["ollama"])

    def test_unavailable_synthetic_ollama_fails_closed(self):
        for status in ("service_unavailable", "missing"):
            with self.subTest(ollama_status=status):
                scope = unittest.TestCase()
                self.addCleanup(scope.doCleanups)
                self.fixture.install_synthetic_bootstrap(
                    scope,
                    self.runtime_class,
                    ollama_status=status,
                )
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    shell = self.make_shell(root)
                    with self.assertRaises(ProviderSelectionError) as raised:
                        shell.propose(self.MISSION_TEXT)
                    self.assertIn("invoke_local_model_audit", str(raised.exception))
                    self.assertIsNone(shell.pending_charter)
                    self.assertFalse((root / "workspace" / "missions").exists())
                scope.doCleanups()

    def test_cleanup_restores_real_collect(self):
        scope = unittest.TestCase()
        self.fixture.install_synthetic_bootstrap(scope, self.runtime_class)
        self.assertIsNot(self.runtime_class.__dict__["collect"], REAL_COLLECT)
        scope.doCleanups()
        self.assertIs(self.runtime_class.__dict__["collect"], REAL_COLLECT)

    def test_synthetic_state_is_fresh_on_every_collect(self):
        collect = self.fixture.install_synthetic_bootstrap(
            self,
            self.runtime_class,
        )
        with tempfile.TemporaryDirectory() as tmp:
            runtime = self.runtime_class(state_root=Path(tmp), actor="Eduardo")
            first = runtime.collect()
            first["snapshot"]["providers"][2]["status"] = "missing"
            first["snapshot"]["providers"][2]["models"].clear()
            second = runtime.collect()
        self.assertEqual(collect.call_count, 2)
        ollama = second["snapshot"]["providers"][2]
        self.assertEqual(ollama["status"], "ready")
        self.assertEqual(
            ollama["models"],
            [{"name": self.fixture.DEFAULT_TEST_MODEL, "size": "synthetic"}],
        )


if __name__ == "__main__":
    unittest.main()
