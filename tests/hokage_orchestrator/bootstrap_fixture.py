"""Deterministic bootstrap evidence for conversational Hokage tests.

ConversationalHokage.__init__ calls HokageBootstrapRuntime.collect(), which
probes the host for Codex, Claude, Ollama and hardware. Tests that verify
orchestration logic (approval phrases, gating, persistence, rejection,
lifecycle, resume) install fresh synthetic evidence at that collect boundary
so provider readiness never depends on the developer machine. Provider
selection, capabilities and authority still run for real on that evidence.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest import mock

DEFAULT_TEST_MODEL = "qwen2.5-coder:7b"
OLLAMA_STATUSES = ("ready", "service_unavailable", "missing")


def synthetic_bootstrap_evidence(
    *,
    actor: str,
    ollama_status: str = "ready",
    model: str = DEFAULT_TEST_MODEL,
) -> Dict[str, Any]:
    """Return newly built collect()-shaped evidence on every call.

    Codex and Claude are always missing; only Ollama's status varies, so
    readiness for invoke_local_model_audit is decided by ollama_status."""

    if ollama_status not in OLLAMA_STATUSES:
        raise ValueError(f"unsupported synthetic ollama_status: {ollama_status!r}")

    def missing(name: str) -> Dict[str, Any]:
        return {
            "provider": name,
            "installed": False,
            "authenticated": False,
            "status": "missing",
            "usage_source": "unknown",
            "limit_source": "manual_required",
            "renewal_source": "manual_required",
        }

    ollama = {
        "provider": "ollama",
        "installed": ollama_status != "missing",
        "authenticated": True,
        "status": ollama_status,
        "models": (
            [{"name": model, "size": "synthetic"}]
            if ollama_status == "ready"
            else []
        ),
        "usage_source": "automatic_local",
        "limit_source": "not_applicable",
        "renewal_source": "not_applicable",
    }
    snapshot = {
        "schema_version": "1.0.0",
        "report_type": "provider_capacity_snapshot",
        "captured_at": "synthetic",
        "providers": [missing("codex"), missing("claude"), ollama],
        "hardware": {
            "cpu_count": 0,
            "cpu_model": "synthetic",
            "memory_bytes": 0,
            "disk_free_bytes": 0,
            "gpu": {"detected": False, "source": "none", "details": ""},
            "source": "synthetic_test_fixture",
        },
        "local_model_recommendation": {
            "profile": "synthetic",
            "recommendation": "",
            "basis": {"memory_gib": 0, "gpu_detected": False},
            "decision_authority": "human_user",
        },
        "authority": {
            "snapshot_is_evidence_only": True,
            "snapshot_does_not_authorize_execution": True,
            "provider_output_is_not_permission": True,
        },
    }
    state = {
        "schema_version": "1.0.0",
        "report_type": "hokage_bootstrap_state",
        "status": "complete",
        "first_use": True,
        "session_count": 1,
        "last_actor": actor,
        "provider_discovery": "synthetic_test_fixture",
        "hardware_discovery": "synthetic_test_fixture",
        "authority": {
            "state_is_evidence_only": True,
            "state_does_not_authorize_execution": True,
            "private_state_only": True,
        },
    }
    return {"state": state, "snapshot": snapshot}


def install_synthetic_bootstrap(
    test_case,
    bootstrap_class,
    *,
    ollama_status: str = "ready",
) -> mock.MagicMock:
    """Replace bootstrap_class.collect for this test only.

    The patch is undone through test_case.addCleanup. Returns the collect
    mock so callers can assert how often the boundary was crossed."""

    def collect(runtime):
        return synthetic_bootstrap_evidence(
            actor=runtime.actor,
            ollama_status=ollama_status,
        )

    patcher = mock.patch.object(
        bootstrap_class,
        "collect",
        autospec=True,
        side_effect=collect,
    )
    collect_mock = patcher.start()
    test_case.addCleanup(patcher.stop)
    return collect_mock
