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
    invoke_claude,
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


class ClaudeStructuredOutputTransportTests(unittest.TestCase):
    """BLOCK_4 FINDING #12: schema-bound Claude assignments must run
    headless (dontAsk, never plan mode), expose only Read/Grep/Glob (no
    Bash, no MCP), and use Claude's native --json-schema structured output.
    Konoha's own deterministic AssignmentResult parsing/validation in
    executor.py stays authoritative over provider output regardless."""

    _SCHEMA = {"type": "object", "properties": {"outcome": {"type": "string"}}}

    def _write_schema(self, tmp: str) -> Path:
        schema_path = Path(tmp) / "result.schema.json"
        schema_path.write_text(json.dumps(self._SCHEMA), encoding="utf-8")
        return schema_path

    def _envelope_stdout(self, **overrides) -> str:
        envelope = {
            "result": "PROSE THAT MUST NOT BE USED",
            "structured_output": {
                "outcome": "completed",
                "objective_satisfied": True,
                "summary": "ok",
                "diagnostic": None,
                "evidence": [],
                "review_outcome": None,
            },
            "usage": {"input_tokens": 5, "output_tokens": 3},
        }
        envelope.update(overrides)
        return json.dumps(envelope)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_schema_bound_command_shape(self, run_mock, which_mock) -> None:
        # Test A
        which_mock.return_value = "/usr/bin/claude"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=self._envelope_stdout(), stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]

        for token in (
            "--print", "--output-format", "json",
            "--permission-mode", "dontAsk",
            "--tools", "Read,Grep,Glob",
            "--disallowedTools", "mcp__*",
            "--no-session-persistence",
            "--json-schema",
        ):
            self.assertIn(token, command)

        for forbidden in ("plan", "Bash", "bypassPermissions", "dangerously-skip-permissions"):
            self.assertNotIn(forbidden, command)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_json_schema_flag_carries_inline_schema_not_a_path(self, run_mock, which_mock) -> None:
        # Test B
        which_mock.return_value = "/usr/bin/claude"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=self._envelope_stdout(), stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]

        idx = command.index("--json-schema")
        inline_value = command[idx + 1]
        self.assertEqual(json.loads(inline_value), self._SCHEMA)
        self.assertNotEqual(inline_value, str(schema_path))

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_structured_output_is_authoritative_over_result_prose(self, run_mock, which_mock) -> None:
        # Test C
        which_mock.return_value = "/usr/bin/claude"
        stdout = self._envelope_stdout()
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stdout, stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            result = invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
        self.assertEqual(
            json.loads(result.text),
            json.loads(stdout)["structured_output"],
        )
        self.assertNotIn("PROSE THAT MUST NOT BE USED", result.text)
        self.assertEqual(result.raw, stdout)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_missing_structured_output_fails_closed(self, run_mock, which_mock) -> None:
        # Test D
        which_mock.return_value = "/usr/bin/claude"
        envelope = json.loads(self._envelope_stdout())
        del envelope["structured_output"]
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=json.dumps(envelope), stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            with self.assertRaises(ProviderError) as caught:
                invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
        exc = caught.exception
        self.assertEqual(exc.provider, "claude")
        self.assertEqual(exc.failure_type, "invalid_structured_output")

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_non_object_structured_output_fails_closed(self, run_mock, which_mock) -> None:
        # Test E
        which_mock.return_value = "/usr/bin/claude"
        for bad_value in (None, [], "json text"):
            with self.subTest(bad_value=bad_value):
                run_mock.return_value = subprocess.CompletedProcess(
                    args=["claude"],
                    returncode=0,
                    stdout=self._envelope_stdout(structured_output=bad_value),
                    stderr="",
                )
                with tempfile.TemporaryDirectory() as tmp:
                    schema_path = self._write_schema(tmp)
                    with self.assertRaises(ProviderError) as caught:
                        invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
                self.assertEqual(caught.exception.provider, "claude")
                self.assertEqual(caught.exception.failure_type, "invalid_structured_output")

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_invalid_claude_schema_fails_before_run(self, run_mock, which_mock) -> None:
        # Test F
        which_mock.return_value = "/usr/bin/claude"
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ProviderError) as caught:
                invoke_claude(
                    "prompt", cwd=Path(tmp), schema=Path(tmp) / "missing.schema.json",
                )
        exc = caught.exception
        self.assertEqual(exc.provider, "claude")
        self.assertEqual(exc.failure_type, "invalid_schema")
        run_mock.assert_not_called()

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_dispatcher_forwards_schema_to_claude(self, run_mock, which_mock) -> None:
        # Test G
        which_mock.return_value = "/usr/bin/claude"
        stdout = self._envelope_stdout()
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=stdout, stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = self._write_schema(tmp)
            result = invoke(
                "claude", "prompt", cwd=Path(tmp), model="provider_default", schema=schema_path,
            )
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertIn("--json-schema", command)
        self.assertEqual(
            json.loads(result.text),
            json.loads(stdout)["structured_output"],
        )

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_schema_less_invocation_preserves_prior_result_extraction(self, run_mock, which_mock) -> None:
        # Test H
        which_mock.return_value = "/usr/bin/claude"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout=json.dumps({"result": "hello world", "usage": {"input_tokens": 1, "output_tokens": 1}}),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = invoke_claude("prompt", cwd=Path(tmp))
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        self.assertNotIn("--json-schema", command)
        self.assertEqual(result.text, "hello world")


class ClaudeSchemaDialectTransportTests(unittest.TestCase):
    """BLOCK_4 FINDING #13: Claude Code 2.1.238 rejects the canonical
    AssignmentResult schema's top-level draft-2020-12 "$schema" meta-schema
    URI. Konoha strips only that one known top-level key from a separate
    in-memory transport copy built for --json-schema - the schema file on
    disk and any other schema content is never touched, and Konoha's own
    deterministic AssignmentResult validation downstream stays
    authoritative regardless of what the transport CLI accepted."""

    _DIALECT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

    _ENVELOPE_STDOUT = json.dumps(
        {
            "result": "PROSE THAT MUST NOT BE USED",
            "structured_output": {
                "outcome": "completed",
                "objective_satisfied": True,
                "summary": "ok",
                "diagnostic": None,
                "evidence": [],
                "review_outcome": None,
            },
            "usage": {"input_tokens": 5, "output_tokens": 3},
        }
    )

    def _write_schema(self, tmp: str, payload: dict) -> Path:
        schema_path = Path(tmp) / "result.schema.json"
        schema_path.write_text(json.dumps(payload), encoding="utf-8")
        return schema_path

    def _invoke_and_get_inline_schema(self, run_mock, which_mock, tmp: str, payload: dict):
        which_mock.return_value = "/usr/bin/claude"
        run_mock.return_value = subprocess.CompletedProcess(
            args=["claude"], returncode=0, stdout=self._ENVELOPE_STDOUT, stderr="",
        )
        schema_path = self._write_schema(tmp, payload)
        before = schema_path.read_bytes()
        invoke_claude("prompt", cwd=Path(tmp), schema=schema_path)
        args, kwargs = run_mock.call_args
        command = args[0] if args else kwargs["command"]
        idx = command.index("--json-schema")
        inline_schema = json.loads(command[idx + 1])
        return inline_schema, schema_path, before

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_known_2020_12_declaration_is_stripped_for_claude_transport(
        self, run_mock, which_mock,
    ) -> None:
        # Test A
        payload = {
            "$schema": self._DIALECT_2020_12,
            "type": "object",
            "properties": {"outcome": {"type": "string"}},
            "required": ["outcome"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            inline_schema, _, _ = self._invoke_and_get_inline_schema(
                run_mock, which_mock, tmp, payload,
            )
        self.assertNotIn("$schema", inline_schema)
        expected_rest = {k: v for k, v in payload.items() if k != "$schema"}
        self.assertEqual(inline_schema, expected_rest)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_canonical_file_content_is_unchanged(self, run_mock, which_mock) -> None:
        # Test B
        payload = {
            "$schema": self._DIALECT_2020_12,
            "type": "object",
            "properties": {"outcome": {"type": "string"}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            _, schema_path, before = self._invoke_and_get_inline_schema(
                run_mock, which_mock, tmp, payload,
            )
            after = schema_path.read_bytes()
            self.assertEqual(before, after)
            self.assertEqual(json.loads(after), payload)
            files_in_tmp = sorted(p.name for p in Path(tmp).iterdir())
            self.assertEqual(files_in_tmp, ["result.schema.json"])

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_no_other_transformation_occurs_on_nested_content(
        self, run_mock, which_mock,
    ) -> None:
        # Test C
        payload = {
            "$schema": self._DIALECT_2020_12,
            "title": "Konoha v4 Assignment Result",
            "type": "object",
            "additionalProperties": False,
            "required": ["outcome", "evidence"],
            "properties": {
                "outcome": {"type": "string", "enum": ["completed", "blocked"]},
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "observation": {"type": "string"},
                        },
                    },
                },
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            inline_schema, _, _ = self._invoke_and_get_inline_schema(
                run_mock, which_mock, tmp, payload,
            )
        expected = {k: v for k, v in payload.items() if k != "$schema"}
        self.assertEqual(inline_schema, expected)
        self.assertEqual(
            inline_schema["properties"]["evidence"], payload["properties"]["evidence"],
        )

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_schema_without_dollar_schema_passes_through_unchanged(
        self, run_mock, which_mock,
    ) -> None:
        # Test D
        payload = {"type": "object", "properties": {"outcome": {"type": "string"}}}
        with tempfile.TemporaryDirectory() as tmp:
            inline_schema, _, _ = self._invoke_and_get_inline_schema(
                run_mock, which_mock, tmp, payload,
            )
        self.assertEqual(inline_schema, payload)

    @patch("tools.konoha_v4.provider_adapters.shutil.which")
    @patch("tools.konoha_v4.provider_adapters._run")
    def test_unrecognized_dollar_schema_value_is_not_rewritten(
        self, run_mock, which_mock,
    ) -> None:
        # Test E: only the exact known draft-2020-12 URI is stripped - any
        # other "$schema" value is left exactly as-is, not converted to
        # another dialect and not treated as a reason to touch anything
        # else in the object.
        payload = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"outcome": {"type": "string"}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            inline_schema, _, _ = self._invoke_and_get_inline_schema(
                run_mock, which_mock, tmp, payload,
            )
        self.assertEqual(inline_schema, payload)
        self.assertIn("$schema", inline_schema)
        self.assertEqual(
            inline_schema["$schema"], "http://json-schema.org/draft-07/schema#",
        )


if __name__ == "__main__":
    unittest.main()
