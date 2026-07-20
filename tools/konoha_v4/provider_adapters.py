from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .continuity import default_state_root


class ProviderError(RuntimeError):
    """Structured provider failure suitable for logs and user-facing summaries."""

    def __init__(
        self,
        message: str,
        *,
        provider: str,
        failure_type: str,
        exit_code: int | None = None,
        stdout_summary: str = "",
        stderr_summary: str = "",
        retryable: bool = False,
        command: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.failure_type = failure_type
        self.exit_code = exit_code
        self.stdout_summary = stdout_summary
        self.stderr_summary = stderr_summary
        self.retryable = retryable
        self.command = list(command or [])

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "failure_type": self.failure_type,
            "exit_code": self.exit_code,
            "stdout_summary": self.stdout_summary,
            "stderr_summary": self.stderr_summary,
            "retryable": self.retryable,
            "command": _sanitize_command(self.command),
        }

    def __str__(self) -> str:
        base = super().__str__()
        detail = self.stderr_summary or self.stdout_summary
        if detail and detail not in base:
            return f"{base}: {detail}"
        return base


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    usage: dict[str, int]
    command: list[str]
    raw: str


def _sanitize_command(command: list[str]) -> list[str]:
    """Return a safe command summary without prompts or credentials."""
    sanitized: list[str] = []
    redact_next = False
    sensitive_flags = {
        "--api-key",
        "--token",
        "--auth-token",
        "--remote-auth-token-env",
    }
    for value in command:
        if redact_next:
            sanitized.append("<redacted>")
            redact_next = False
            continue
        sanitized.append(value)
        if value in sensitive_flags:
            redact_next = True
    return sanitized


def _truncate(value: str | None, limit: int = 3000) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _extract_jsonl_error(raw: str) -> str:
    """Extract useful diagnostics from Codex JSONL failure events."""
    messages: list[str] = []
    for line in (raw or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = str(event.get("type") or "")
        if event_type not in {
            "error",
            "turn.failed",
            "response.failed",
            "item.failed",
        }:
            continue

        candidates: list[Any] = [
            event.get("message"),
            event.get("error"),
            event.get("detail"),
            event.get("reason"),
        ]
        response = event.get("response")
        if isinstance(response, dict):
            candidates.extend(
                [
                    response.get("error"),
                    response.get("message"),
                    response.get("status_details"),
                ]
            )

        for candidate in candidates:
            if isinstance(candidate, dict):
                text = (
                    candidate.get("message")
                    or candidate.get("detail")
                    or candidate.get("code")
                    or json.dumps(candidate, ensure_ascii=False)
                )
            else:
                text = candidate
            if text:
                messages.append(str(text).strip())

    return _truncate(" | ".join(dict.fromkeys(messages)))


def _provider_failure(
    *,
    provider: str,
    command: list[str],
    cp: subprocess.CompletedProcess[str],
) -> ProviderError:
    stderr_summary = _truncate(cp.stderr)
    jsonl_error = _extract_jsonl_error(cp.stdout)
    stdout_summary = jsonl_error or _truncate(cp.stdout)
    detail = (
        stderr_summary
        or jsonl_error
        or stdout_summary
        or "El proceso terminó sin diagnóstico."
    )
    retryable = cp.returncode in {124, 137, 143}
    return ProviderError(
        f"{provider.capitalize()} falló",
        provider=provider,
        failure_type="process_error",
        exit_code=cp.returncode,
        stdout_summary=stdout_summary,
        stderr_summary=stderr_summary,
        retryable=retryable,
        command=command,
    )


def _run(
    command: list[str],
    *,
    stdin: str | None,
    cwd: Path,
    timeout: int,
    provider: str,
) -> subprocess.CompletedProcess[str]:
    state_root = default_state_root()
    temp_root = state_root / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(temp_root / "pycache"),
            "TMPDIR": str(temp_root),
            "TEMP": str(temp_root),
            "TMP": str(temp_root),
            "KONOHA_STATE_ROOT": str(state_root),
        }
    )

    try:
        return subprocess.run(
            command,
            input=stdin,
            text=True,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_summary = _truncate(
            exc.stdout.decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout
        )
        stderr_summary = _truncate(
            exc.stderr.decode(errors="replace")
            if isinstance(exc.stderr, bytes)
            else exc.stderr
        )
        raise ProviderError(
            f"{provider.capitalize()} excedió el timeout de {timeout}s",
            provider=provider,
            failure_type="timeout",
            exit_code=None,
            stdout_summary=stdout_summary,
            stderr_summary=stderr_summary,
            retryable=True,
            command=command,
        ) from exc
    except OSError as exc:
        raise ProviderError(
            f"No se pudo iniciar {provider}: {exc}",
            provider=provider,
            failure_type="unavailable",
            exit_code=None,
            retryable=False,
            command=command,
        ) from exc


def _validate_schema(schema: Path) -> Path:
    resolved = schema.resolve()
    if not resolved.is_file():
        raise ProviderError(
            f"El schema de salida no existe: {resolved}",
            provider="codex",
            failure_type="invalid_schema",
            retryable=False,
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProviderError(
            f"El schema de salida no es JSON válido: {resolved}: {exc}",
            provider="codex",
            failure_type="invalid_schema",
            retryable=False,
        ) from exc
    if not isinstance(payload, dict):
        raise ProviderError(
            f"El schema de salida debe ser un objeto JSON: {resolved}",
            provider="codex",
            failure_type="invalid_schema",
            retryable=False,
        )
    return resolved


def invoke_codex(
    prompt: str,
    *,
    cwd: Path,
    model: str = "provider_default",
    schema: Path | None = None,
    timeout: int = 600,
) -> ProviderResult:
    exe = shutil.which("codex")
    if not exe:
        raise ProviderError(
            "Codex CLI no está instalado o no está en PATH.",
            provider="codex",
            failure_type="unavailable",
            retryable=False,
        )

    command = [
        exe,
        "exec",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--json",
        "-C",
        str(cwd),
    ]
    if model != "provider_default":
        command += ["--model", model]
    if schema:
        command += ["--output-schema", str(_validate_schema(schema))]
    command += ["-"]

    cp = _run(
        command,
        stdin=prompt,
        cwd=cwd,
        timeout=timeout,
        provider="codex",
    )
    if cp.returncode != 0:
        raise _provider_failure(provider="codex", command=command, cp=cp)

    messages: list[str] = []
    usage: dict[str, Any] = {}
    failure_event = _extract_jsonl_error(cp.stdout)
    for line in cp.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            messages.append(str(item["text"]))
        if event.get("type") in {"turn.completed", "response.completed"}:
            usage = (
                event.get("usage")
                or event.get("response", {}).get("usage")
                or usage
            )

    if failure_event:
        raise ProviderError(
            "Codex reportó un evento de fallo",
            provider="codex",
            failure_type="provider_event_error",
            exit_code=cp.returncode,
            stdout_summary=failure_event,
            stderr_summary=_truncate(cp.stderr),
            retryable=False,
            command=command,
        )

    text = messages[-1] if messages else cp.stdout.strip()
    if not text:
        raise ProviderError(
            "Codex terminó sin producir un mensaje de agente",
            provider="codex",
            failure_type="empty_output",
            exit_code=cp.returncode,
            stdout_summary=_truncate(cp.stdout),
            stderr_summary=_truncate(cp.stderr),
            retryable=True,
            command=command,
        )

    return ProviderResult(
        "codex",
        model,
        text,
        _normalize_usage(usage),
        command,
        cp.stdout,
    )


def invoke_claude(
    prompt: str,
    *,
    cwd: Path,
    model: str = "provider_default",
    timeout: int = 600,
) -> ProviderResult:
    exe = shutil.which("claude")
    if not exe:
        raise ProviderError(
            "Claude Code no está instalado o no está en PATH.",
            provider="claude",
            failure_type="unavailable",
            retryable=False,
        )

    command = [
        exe,
        "--print",
        "--output-format",
        "json",
        "--permission-mode",
        "plan",
        "--tools",
        "Read,Grep,Glob,Bash",
        "--no-session-persistence",
    ]
    if model != "provider_default":
        command += ["--model", model]
    command += [prompt]

    cp = _run(
        command,
        stdin=None,
        cwd=cwd,
        timeout=timeout,
        provider="claude",
    )
    if cp.returncode != 0:
        raise _provider_failure(provider="claude", command=command, cp=cp)

    try:
        payload = json.loads(cp.stdout)
        text = payload.get("result") or payload.get("content") or cp.stdout.strip()
        usage = payload.get("usage") or {}
    except json.JSONDecodeError:
        text, usage = cp.stdout.strip(), {}

    if not text:
        raise ProviderError(
            "Claude terminó sin producir contenido",
            provider="claude",
            failure_type="empty_output",
            exit_code=cp.returncode,
            stdout_summary=_truncate(cp.stdout),
            stderr_summary=_truncate(cp.stderr),
            retryable=True,
            command=command,
        )

    return ProviderResult(
        "claude",
        model,
        str(text),
        _normalize_usage(usage),
        command,
        cp.stdout,
    )


def invoke_ollama(
    prompt: str,
    *,
    cwd: Path,
    model: str,
    timeout: int = 600,
) -> ProviderResult:
    exe = shutil.which("ollama")
    if not exe:
        raise ProviderError(
            "Ollama no está instalado o no está en PATH.",
            provider="ollama",
            failure_type="unavailable",
            retryable=False,
        )

    command = [exe, "run", model]
    cp = _run(
        command,
        stdin=prompt,
        cwd=cwd,
        timeout=timeout,
        provider="ollama",
    )
    if cp.returncode != 0:
        raise _provider_failure(provider="ollama", command=command, cp=cp)

    text = cp.stdout.strip()
    if not text:
        raise ProviderError(
            "Ollama terminó sin producir contenido",
            provider="ollama",
            failure_type="empty_output",
            exit_code=cp.returncode,
            stdout_summary=_truncate(cp.stdout),
            stderr_summary=_truncate(cp.stderr),
            retryable=True,
            command=command,
        )

    return ProviderResult("ollama", model, text, {}, command, cp.stdout)


def invoke(
    provider: str,
    prompt: str,
    *,
    cwd: Path,
    model: str,
    schema: Path | None = None,
    timeout: int = 600,
) -> ProviderResult:
    if provider == "codex":
        return invoke_codex(
            prompt,
            cwd=cwd,
            model=model,
            schema=schema,
            timeout=timeout,
        )
    if provider == "claude":
        return invoke_claude(
            prompt,
            cwd=cwd,
            model=model,
            timeout=timeout,
        )
    if provider == "ollama":
        if model == "provider_default":
            raise ProviderError(
                "Ollama requiere un modelo local explícito.",
                provider="ollama",
                failure_type="invalid_configuration",
                retryable=False,
            )
        return invoke_ollama(
            prompt,
            cwd=cwd,
            model=model,
            timeout=timeout,
        )
    raise ProviderError(
        f"Provider no soportado: {provider}",
        provider=provider,
        failure_type="unsupported_provider",
        retryable=False,
    )


def _normalize_usage(raw: dict[str, Any]) -> dict[str, int]:
    aliases = {
        "input_tokens": ("input_tokens", "input"),
        "cached_input_tokens": ("cached_input_tokens", "cached_input"),
        "output_tokens": ("output_tokens", "output"),
        "reasoning_output_tokens": (
            "reasoning_output_tokens",
            "reasoning_tokens",
        ),
        "total_tokens": ("total_tokens", "total"),
    }
    normalized: dict[str, int] = {}
    for target, candidates in aliases.items():
        for candidate in candidates:
            value = raw.get(candidate)
            if isinstance(value, int):
                normalized[target] = value
                break
    if "total_tokens" not in normalized:
        total = (
            normalized.get("input_tokens", 0)
            + normalized.get("output_tokens", 0)
        )
        if total:
            normalized["total_tokens"] = total
    return normalized
