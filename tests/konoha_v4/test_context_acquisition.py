import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.konoha_v4.context_acquisition import (
    ProviderReadiness,
    acquire_context,
    normalize_missing_context,
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

if __name__ == "__main__":
    unittest.main()
