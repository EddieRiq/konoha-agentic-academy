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
    invoke,
    invoke_codex,
    invoke_ollama,
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
    def test_missing_codex_schema_diagnostic_still_reports_codex(
        self,
        which_mock,
    ) -> None:
        # BLOCK_4 FINDING #11 Part D: the provider-aware _validate_schema()
        # must not regress Codex's own invalid-schema diagnostic.
        which_mock.return_value = "/usr/bin/codex"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ProviderError) as caught:
                invoke_codex(
                    "prompt",
                    cwd=root,
                    schema=root / "missing.schema.json",
                )
        exc = caught.exception
        self.assertEqual(exc.provider, "codex")
        self.assertEqual(exc.failure_type, "invalid_schema")

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


class OllamaMachineReadableTransportTests(unittest.TestCase):
    """BLOCK_4 FINDING #7: invoke_ollama must ask the Ollama CLI itself for
    machine-readable output (--nowordwrap), not reconstruct/repair stdout
    downstream. These tests only verify the command Konoha invokes - they
    never simulate --nowordwrap "cleaning" ANSI/newlines, since that is the
    real CLI's responsibility, not Konoha's."""

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_command_includes_nowordwrap_and_requested_model(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout='{"outcome":"completed"}',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            invoke_ollama("prompt", cwd=Path(tmp), model="qwen2.5-coder:7b")
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertIn("--nowordwrap", command)
        self.assertIn("qwen2.5-coder:7b", command)
        self.assertEqual(
            command,
            ["/usr/local/bin/ollama", "run", "--nowordwrap", "qwen2.5-coder:7b"],
        )

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_stdout_is_preserved_without_ansi_or_heuristic_cleanup(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/local/bin/ollama"
        fenced_stdout = "  \n```json\n{\"outcome\": \"completed\"}\n```\n  \n"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout=fenced_stdout,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = invoke_ollama("prompt", cwd=Path(tmp), model="qwen2.5-coder:7b")
        self.assertEqual(result.text, fenced_stdout.strip())
        self.assertEqual(result.raw, fenced_stdout)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_empty_output_still_raises_empty_output_diagnostic(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout="   \n",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProviderError) as caught:
                invoke_ollama("prompt", cwd=Path(tmp), model="qwen2.5-coder:7b")
        exc = caught.exception
        self.assertEqual(exc.provider, "ollama")
        self.assertEqual(exc.failure_type, "empty_output")

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_nonzero_exit_still_raises_process_failure(
        self,
        run_mock,
        which_mock,
    ) -> None:
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=1,
            stdout="",
            stderr="model not found",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProviderError) as caught:
                invoke_ollama("prompt", cwd=Path(tmp), model="qwen2.5-coder:7b")
        exc = caught.exception
        self.assertEqual(exc.provider, "ollama")
        self.assertEqual(exc.exit_code, 1)


class OllamaJsonModeTransportTests(unittest.TestCase):
    """BLOCK_4 FINDING #11: schema-bound Ollama invocations must request
    native Ollama JSON syntax mode (--format json) in addition to
    --nowordwrap. --format json is only a syntax nudge to the model - it is
    never treated here as exact JSON Schema enforcement, and Konoha's own
    deterministic AssignmentResult parsing/validation in executor.py stays
    authoritative over provider output regardless of this flag."""

    def _write_schema(self, tmp: str) -> Path:
        schema_path = Path(tmp) / "result.schema.json"
        schema_path.write_text(
            json.dumps({"type": "object", "properties": {}}), encoding="utf-8",
        )
        return schema_path

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_schema_bound_invocation_enables_json_mode(
        self,
        run_mock,
        which_mock,
    ) -> None:
        # Test A
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout='{"outcome":"completed"}',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            invoke_ollama(
                "prompt", cwd=Path(tmp), model="qwen2.5-coder:7b", schema=schema_path,
            )
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertEqual(
            command,
            [
                "/usr/local/bin/ollama",
                "run",
                "--nowordwrap",
                "--format",
                "json",
                "qwen2.5-coder:7b",
            ],
        )

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_schema_less_invocation_preserves_existing_behavior(
        self,
        run_mock,
        which_mock,
    ) -> None:
        # Test B
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout='{"outcome":"completed"}',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            invoke_ollama("prompt", cwd=Path(tmp), model="qwen2.5-coder:7b")
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertEqual(
            command,
            ["/usr/local/bin/ollama", "run", "--nowordwrap", "qwen2.5-coder:7b"],
        )

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_invalid_ollama_schema_fails_before_run(
        self,
        run_mock,
        which_mock,
    ) -> None:
        # Test C
        which_mock.return_value = "/usr/local/bin/ollama"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProviderError) as caught:
                invoke_ollama(
                    "prompt",
                    cwd=Path(tmp),
                    model="qwen2.5-coder:7b",
                    schema=Path(tmp) / "missing.schema.json",
                )
        exc = caught.exception
        self.assertEqual(exc.provider, "ollama")
        self.assertEqual(exc.failure_type, "invalid_schema")
        run_mock.assert_not_called()

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_dispatcher_forwards_schema_into_ollama_json_mode(
        self,
        run_mock,
        which_mock,
    ) -> None:
        # Test E
        which_mock.return_value = "/usr/local/bin/ollama"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout='{"outcome":"completed"}',
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            invoke(
                "ollama",
                "prompt",
                cwd=Path(tmp),
                model="qwen2.5-coder:7b",
                schema=schema_path,
            )
        run_mock.assert_called_once()
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertIn("--format", command)
        self.assertIn("json", command)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_raw_stdout_preservation_unchanged_with_schema_bound_json_mode(
        self,
        run_mock,
        which_mock,
    ) -> None:
        # Test F
        which_mock.return_value = "/usr/local/bin/ollama"
        fenced_stdout = "  \n```json\n{\"outcome\": \"completed\"}\n```\n  \n"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["ollama"],
            returncode=0,
            stdout=fenced_stdout,
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            result = invoke_ollama(
                "prompt", cwd=Path(tmp), model="qwen2.5-coder:7b", schema=schema_path,
            )
        self.assertEqual(result.text, fenced_stdout.strip())
        self.assertEqual(result.raw, fenced_stdout)


if __name__ == "__main__":
    unittest.main()
