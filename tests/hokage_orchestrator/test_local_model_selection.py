from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator.bootstrap_runtime import (
    HokageBootstrapRuntime,
)


def snapshot():
    return {
        "providers": [
            {
                "provider": "ollama",
                "models": [
                    {"name": "qwen2.5-coder:3b"},
                    {"name": "llama3.2:3b"},
                ],
            }
        ],
        "local_model_recommendation": {
            "profile": "light",
            "recommendation": "Use 1.5B-class local models.",
        },
    }


class LocalModelSelectionTests(unittest.TestCase):
    def test_selection_starts_pending(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = HokageBootstrapRuntime(
                state_root=Path(temp),
                actor="Eduardo",
            )
            result = runtime.local_model_configuration(snapshot())
            self.assertEqual(
                result["selection_status"],
                "pending_human_selection",
            )
            self.assertIsNone(result["selected_model"])
            self.assertFalse(result["approved_by_user"])

    def test_select_installed_model_persists(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = HokageBootstrapRuntime(
                state_root=Path(temp),
                actor="Eduardo",
            )
            result = runtime.select_local_model(
                "qwen2.5-coder:3b",
                snapshot(),
            )
            self.assertEqual(
                result["selected_model"],
                "qwen2.5-coder:3b",
            )
            self.assertEqual(result["selection_status"], "selected")
            self.assertTrue(result["approved_by_user"])

            loaded = runtime.local_model_configuration(snapshot())
            self.assertEqual(
                loaded["selected_model"],
                "qwen2.5-coder:3b",
            )

    def test_unknown_model_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = HokageBootstrapRuntime(
                state_root=Path(temp),
                actor="Eduardo",
            )
            with self.assertRaises(ValueError):
                runtime.select_local_model(
                    "not-installed:latest",
                    snapshot(),
                )

    def test_clear_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            runtime = HokageBootstrapRuntime(
                state_root=Path(temp),
                actor="Eduardo",
            )
            runtime.select_local_model(
                "llama3.2:3b",
                snapshot(),
            )
            cleared = runtime.select_local_model(
                "clear",
                snapshot(),
            )
            self.assertIsNone(cleared["selected_model"])
            self.assertEqual(
                cleared["selection_status"],
                "disabled_by_user",
            )


if __name__ == "__main__":
    unittest.main()
