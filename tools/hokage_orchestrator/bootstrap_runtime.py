from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


class HokageBootstrapRuntime:
    SCHEMA_VERSION = "1.0.0"

    def __init__(
        self,
        *,
        state_root: Path,
        actor: str,
        command_runner: Optional[Callable[..., Dict[str, Any]]] = None,
    ) -> None:
        self.state_root = state_root.resolve()
        self.actor = actor
        self.bootstrap_dir = self.state_root / "bootstrap"
        self.state_path = self.bootstrap_dir / "hokage_bootstrap_state.json"
        self.snapshot_path = self.bootstrap_dir / "provider_capacity_snapshot.json"
        self._run_command = command_runner or self._default_run_command

    @staticmethod
    def _default_run_command(args: List[str], *, timeout: int = 20) -> Dict[str, Any]:
        try:
            completed = subprocess.run(
                args,
                text=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                check=False,
                timeout=timeout,
            )
            return {
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "timed_out": False,
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "exit_code": 127 if isinstance(exc, OSError) else 124,
                "stdout": "",
                "stderr": f"{type(exc).__name__}: {exc}",
                "timed_out": isinstance(exc, subprocess.TimeoutExpired),
            }

    def _provider_probe(self, name: str, executable: str, auth_args: List[str]) -> Dict[str, Any]:
        path = shutil.which(executable)
        if path is None:
            return {
                "provider": name,
                "installed": False,
                "authenticated": False,
                "status": "missing",
                "usage_source": "unknown",
                "limit_source": "manual_required",
                "renewal_source": "manual_required",
            }
        version = self._run_command([path, "--version"])
        auth = self._run_command([path, *auth_args])
        return {
            "provider": name,
            "installed": True,
            "executable": path,
            "version": (version["stdout"] or version["stderr"]).strip(),
            "authenticated": auth["exit_code"] == 0,
            "status": "ready" if auth["exit_code"] == 0 else "authentication_required",
            "usage_source": "automatic_per_invocation",
            "limit_source": "manual_required",
            "renewal_source": "manual_required",
            "evidence": {
                "version_exit_code": version["exit_code"],
                "auth_exit_code": auth["exit_code"],
            },
        }

    def _ollama_probe(self) -> Dict[str, Any]:
        path = shutil.which("ollama")
        if path is None:
            return {
                "provider": "ollama",
                "installed": False,
                "authenticated": True,
                "status": "missing",
                "models": [],
                "usage_source": "automatic_local",
                "limit_source": "not_applicable",
                "renewal_source": "not_applicable",
            }
        version = self._run_command([path, "--version"])
        listing = self._run_command([path, "list"])
        models = []
        if listing["exit_code"] == 0:
            for line in listing["stdout"].splitlines()[1:]:
                parts = line.split()
                if parts:
                    models.append({
                        "name": parts[0],
                        "size": parts[2] if len(parts) > 2 else "unknown",
                    })
        return {
            "provider": "ollama",
            "installed": True,
            "authenticated": True,
            "status": "ready" if listing["exit_code"] == 0 else "service_unavailable",
            "version": (version["stdout"] or version["stderr"]).strip(),
            "models": models,
            "usage_source": "automatic_local",
            "limit_source": "not_applicable",
            "renewal_source": "not_applicable",
            "evidence": {
                "version_exit_code": version["exit_code"],
                "list_exit_code": listing["exit_code"],
            },
        }

    @staticmethod
    def _memory_bytes() -> int:
        path = Path("/proc/meminfo")
        if not path.exists():
            return 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
        return 0

    def hardware_snapshot(self) -> Dict[str, Any]:
        disk = shutil.disk_usage(self.state_root.parent)
        gpu = {"detected": False, "source": "none", "details": ""}
        nvidia = shutil.which("nvidia-smi")
        if nvidia:
            result = self._run_command([
                nvidia,
                "--query-gpu=name,memory.total",
                "--format=csv,noheader",
            ])
            if result["exit_code"] == 0 and result["stdout"].strip():
                gpu = {
                    "detected": True,
                    "source": "nvidia-smi",
                    "details": result["stdout"].strip(),
                }
        return {
            "cpu_count": os.cpu_count() or 0,
            "cpu_model": platform.processor() or platform.machine(),
            "memory_bytes": self._memory_bytes(),
            "disk_free_bytes": disk.free,
            "gpu": gpu,
            "source": "local_read_only",
        }

    @staticmethod
    def recommend_profile(hardware: Dict[str, Any]) -> Dict[str, Any]:
        gib = hardware["memory_bytes"] / (1024 ** 3)
        if gib < 8:
            profile = "light"
            recommendation = "Use 1.5B-class local models."
        elif gib < 16:
            profile = "balanced"
            recommendation = "Use 3B-class local models; test 7B cautiously."
        else:
            profile = "intensive"
            recommendation = "7B-class local models are viable; measure latency."
        return {
            "profile": profile,
            "recommendation": recommendation,
            "basis": {
                "memory_gib": round(gib, 2),
                "gpu_detected": hardware["gpu"]["detected"],
            },
            "decision_authority": "human_user",
        }

    def collect(self) -> Dict[str, Any]:
        now = utc_now()
        previous = {}
        if self.state_path.exists():
            previous = json.loads(self.state_path.read_text(encoding="utf-8"))

        providers = [
            self._provider_probe("codex", "codex", ["login", "status"]),
            self._provider_probe("claude", "claude", ["auth", "status"]),
            self._ollama_probe(),
        ]
        hardware = self.hardware_snapshot()
        snapshot = {
            "schema_version": self.SCHEMA_VERSION,
            "report_type": "provider_capacity_snapshot",
            "captured_at": now,
            "providers": providers,
            "hardware": hardware,
            "local_model_recommendation": self.recommend_profile(hardware),
            "budget": {
                "premium_baseline_tokens": None,
                "planned_tokens": None,
                "minimum_savings_percent": 30,
                "status": "manual_input_required",
                "rule": "planned cost must be at least 30 percent below premium baseline",
            },
            "authority": {
                "snapshot_is_evidence_only": True,
                "snapshot_does_not_authorize_execution": True,
                "provider_output_is_not_permission": True,
            },
        }
        state = {
            "schema_version": self.SCHEMA_VERSION,
            "report_type": "hokage_bootstrap_state",
            "status": "complete",
            "first_use": not bool(previous),
            "session_count": int(previous.get("session_count", 0)) + 1,
            "first_seen_at": previous.get("first_seen_at", now),
            "last_seen_at": now,
            "last_actor": self.actor,
            "provider_discovery": "complete",
            "hardware_discovery": "complete",
            "local_model_selection": "recommended",
            "budget_profile": "manual_input_required",
            "snapshot_path": str(self.snapshot_path),
            "authority": {
                "state_is_evidence_only": True,
                "state_does_not_authorize_execution": True,
                "private_state_only": True,
            },
        }
        write_json(self.snapshot_path, snapshot)
        write_json(self.state_path, state)
        return {"state": state, "snapshot": snapshot}
