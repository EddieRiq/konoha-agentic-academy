from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.konoha_v4.provider_adapters import (
    ProviderError,
    _extract_jsonl_error,
    _normalize_usage,
    invoke_codex,
)


class ProviderDiagnosticsTests(unittest.TestCase):
    def test_extracts_codex_jsonl_error(self) -> None:
        raw = "\n".join(
            [
                json.dumps({"type": "turn.started"}),
                json.dumps(
                    {
                        "type": "turn.failed",
                        "error": {"message": "schema rejected"},
                    }
                ),
            ]
        )
        self.assertEqual(_extract_jsonl_error(raw), "schema rejected")

    def test_normalizes_codex_usage(self) -> None:
        usage = _normalize_usage(
            {
                "input_tokens": 10,
                "cached_input_tokens": 3,
                "output_tokens": 4,
                "reasoning_output_tokens": 2,
            }
        )
        self.assertEqual(usage["input_tokens"], 10)
        self.assertEqual(usage["cached_input_tokens"], 3)
        self.assertEqual(usage["output_tokens"], 4)
        self.assertEqual(usage["reasoning_output_tokens"], 2)
        self.assertEqual(usage["total_tokens"], 14)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_nonzero_codex_exit_preserves_stdout_diagnostic(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/bin/codex"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=1,
            stdout=json.dumps(
                {
                    "type": "turn.failed",
                    "error": {"message": "output schema invalid"},
                }
            ),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProviderError) as caught:
                invoke_codex("prompt", cwd=Path(tmp))
        exc = caught.exception
        self.assertEqual(exc.provider, "codex")
        self.assertEqual(exc.failure_type, "process_error")
        self.assertEqual(exc.exit_code, 1)
        self.assertIn("output schema invalid", exc.stdout_summary)
        self.assertIn("output schema invalid", str(exc))

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    def test_missing_schema_fails_before_provider_execution(
        self,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/bin/codex"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ProviderError) as caught:
                invoke_codex(
                    "prompt",
                    cwd=root,
                    schema=root / "missing.schema.json",
                )
        self.assertEqual(caught.exception.failure_type, "invalid_schema")

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_successful_jsonl_returns_agent_message_and_usage(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/bin/codex"
        stdout = "\n".join(
            [
                json.dumps({"type": "thread.started"}),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "agent_message",
                            "text": '{"status":"ok"}',
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 20,
                            "cached_input_tokens": 5,
                            "output_tokens": 7,
                            "reasoning_output_tokens": 0,
                        },
                    }
                ),
            ]
        )
        run_mock.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout=stdout,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = invoke_codex("prompt", cwd=Path(tmp))
        self.assertEqual(result.text, '{"status":"ok"}')
        self.assertEqual(result.usage["input_tokens"], 20)
        self.assertEqual(result.usage["cached_input_tokens"], 5)
        self.assertEqual(result.usage["output_tokens"], 7)


if __name__ == "__main__":
    unittest.main()
