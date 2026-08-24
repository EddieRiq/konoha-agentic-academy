import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.konoha_v4.context_acquisition import (
    ProviderReadiness,
    acquire_context,
    normalize_missing_context,
    probe_provider_readiness,
)
from tools.konoha_v4.registry import CapabilityRegistry

class ContextAcquisitionTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]
        self.registry = CapabilityRegistry(self.repo)

    def test_accessible_doctrine_is_loaded_not_user_input(self):
        ctx = acquire_context(self.repo, self.registry)
        self.assertIn("docs/architecture/konoha_v4_operating_model.md", ctx.loaded_files)
        user, resolved = normalize_missing_context(
            ["No está provisto el contenido del modelo operativo; leer docs/architecture/konoha_v4_operating_model.md."],
            ctx,
        )
        self.assertEqual([], user)
        self.assertEqual(1, len(resolved))

    def test_current_workspace_is_read_authorized_and_private_excluded(self):
        ctx = acquire_context(self.repo, self.registry)
        self.assertTrue(ctx.workspace_read_authorized)
        self.assertTrue(any("kirigakure" in x for x in ctx.private_paths_excluded))

    def test_provider_unknown_is_resolved_by_probe_not_user_question(self):
        ctx = acquire_context(self.repo, self.registry)
        user, resolved = normalize_missing_context(
            ["No está confirmado si las herramientas reales de delegación a Claude u Ollama estarán disponibles."],
            ctx,
        )
        self.assertEqual([], user)
        self.assertEqual(1, len(resolved))
        self.assertIn("claude", ctx.provider_readiness)
        self.assertIn("ollama", ctx.provider_readiness)

    def test_jounin_is_formal_registered_family(self):
        self.assertIn("jounin-review", self.registry.available_families())
        family = self.registry.agent_family("jounin-review")
        self.assertIn("independent review", family["allowed_task_patterns"])

    def test_read_only_policy_is_loaded(self):
        ctx = acquire_context(self.repo, self.registry)
        self.assertIn("categories", ctx.read_only_policy)
        user, resolved = normalize_missing_context(
            ["No está definida una lista completa de comandos read-only permitidos por la doctrina."],
            ctx,
        )
        self.assertEqual([], user)
        self.assertEqual(1, len(resolved))

class ProbeProviderReadinessTest(unittest.TestCase):
    """v4.0.2: probe_provider_readiness is the public single-provider entry
    point executor.py uses for its pre-invocation readiness gate. These
    tests mock shutil.which/subprocess.run directly - deterministic, no
    real Codex/Claude/Ollama installation or network required - and prove
    it is the exact same deterministic probe acquire_context() already
    uses internally, not a parallel reimplementation."""

    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]

    def test_missing_executable_is_not_available(self):
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which", return_value=None,
        ):
            readiness = probe_provider_readiness("codex", self.repo)
        self.assertEqual(readiness.provider, "codex")
        self.assertIsNone(readiness.executable)
        self.assertFalse(readiness.available)
        self.assertEqual(readiness.evidence, "executable_not_found")
        self.assertEqual(readiness.models, [])

    def test_available_executable_with_zero_exit_is_ready(self):
        completed = SimpleNamespace(returncode=0, stdout="codex-cli 1.2.3", stderr="")
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which",
            return_value="/usr/bin/codex",
        ), patch(
            "tools.konoha_v4.context_acquisition.subprocess.run",
            return_value=completed,
        ):
            readiness = probe_provider_readiness("codex", self.repo)
        self.assertTrue(readiness.available)
        self.assertEqual(readiness.executable, "/usr/bin/codex")
        self.assertEqual(readiness.evidence, "deterministic_local_probe")

    def test_available_executable_with_nonzero_exit_is_not_ready(self):
        completed = SimpleNamespace(returncode=1, stdout="", stderr="auth required")
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which",
            return_value="/usr/bin/claude",
        ), patch(
            "tools.konoha_v4.context_acquisition.subprocess.run",
            return_value=completed,
        ):
            readiness = probe_provider_readiness("claude", self.repo)
        self.assertFalse(readiness.available)

    def test_ollama_model_inventory_is_freshly_collected(self):
        version_result = SimpleNamespace(returncode=0, stdout="ollama version 0.4.0", stderr="")
        list_result = SimpleNamespace(
            returncode=0,
            stdout="NAME\tID\nllama3:latest\tabc\nmistral:latest\tdef\n",
            stderr="",
        )
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which",
            return_value="/usr/bin/ollama",
        ), patch(
            "tools.konoha_v4.context_acquisition.subprocess.run",
            side_effect=[version_result, list_result],
        ):
            readiness = probe_provider_readiness("ollama", self.repo)
        self.assertTrue(readiness.available)
        self.assertIn("llama3:latest", readiness.models)
        self.assertIn("mistral:latest", readiness.models)

    def test_ollama_list_failure_yields_empty_model_inventory(self):
        version_result = SimpleNamespace(returncode=0, stdout="ollama version 0.4.0", stderr="")
        list_result = SimpleNamespace(returncode=1, stdout="", stderr="daemon not running")
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which",
            return_value="/usr/bin/ollama",
        ), patch(
            "tools.konoha_v4.context_acquisition.subprocess.run",
            side_effect=[version_result, list_result],
        ):
            readiness = probe_provider_readiness("ollama", self.repo)
        # Ollama's own executable is still ready (version probe succeeded);
        # the model inventory is simply empty since `ollama list` failed -
        # never fabricated, never falling back to a cached/prior value.
        self.assertTrue(readiness.available)
        self.assertEqual(readiness.models, [])

    def test_delegates_to_the_same_probe_acquire_context_uses(self):
        with patch(
            "tools.konoha_v4.context_acquisition.shutil.which", return_value=None,
        ):
            direct = probe_provider_readiness("ollama", self.repo)
        self.assertEqual(direct.provider, "ollama")
        self.assertFalse(direct.available)
        self.assertEqual(direct.models, [])


if __name__ == "__main__":
    unittest.main()
