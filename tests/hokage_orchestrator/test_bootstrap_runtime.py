from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools/hokage_orchestrator/bootstrap_runtime.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bootstrap_runtime_test", MODULE)
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


if __name__ == "__main__":
    unittest.main()
