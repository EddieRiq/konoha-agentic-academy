import json, tempfile, unittest
from pathlib import Path
from tools.konoha_v4.models import AgentAssignment, MissionPlan
from tools.konoha_v4.hokage import validate_plan
from tools.konoha_v4.registry import CapabilityRegistry

class ContractsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]
        self.registry = CapabilityRegistry(self.repo)

    def test_unknown_family_is_rejected(self):
        p = MissionPlan("mission-x","audit",[],[],[],"low",[
            AgentAssignment("t","universal-agent","codex","provider_default","x",[],"x")
        ],["done"],["read_only"],10,"low","r").seal()
        self.assertTrue(any("No existe" in x for x in validate_plan(p,self.registry)))

    def test_unauthorized_model_is_rejected(self):
        p = MissionPlan("mission-x","audit",[],[],[],"low",[
            AgentAssignment("t","python-review","ollama","qwen2.5-coder:7b","x",[],"x")
        ],["done"],["read_only"],10,"low","r").seal()
        self.assertTrue(any("Modelo no autorizado" in x for x in validate_plan(p,self.registry)))

    def test_missing_context_stops_plan(self):
        p = MissionPlan("mission-x","write",[],["journal statute"],[],"low",[
            AgentAssignment("t","scientific-writing-review","claude","provider_default","x",[],"x")
        ],["done"],["read_only"],10,"low","r").seal()
        self.assertTrue(any("Falta contexto" in x for x in validate_plan(p,self.registry)))


class ProviderReadinessGateTests(unittest.TestCase):
    """BLOCK_4 FINDING #16: validate_plan(..., provider_readiness=...) must
    fail closed when a plan's provider lacks affirmative
    provider_readiness[provider]["available"] is True evidence - separate
    from, and in addition to, registry.model_allowed()'s static
    eligibility check."""

    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]
        self.registry = CapabilityRegistry(self.repo)

    def _plan(self):
        # codex/provider_default/mission-conductor is a real, statically
        # eligible combination per config/konoha_v4_capabilities.json - so
        # any provider_not_ready problem below is proven to come from the
        # readiness gate, not from registry.model_allowed() rejecting it.
        return MissionPlan("mission-x", "audit", [], [], [], "low", [
            AgentAssignment("t", "mission-conductor", "codex", "provider_default", "x", [], "x")
        ], ["done"], ["read_only"], 10, "low", "r").seal()

    def test_available_provider_is_accepted(self):
        # Test A
        problems = validate_plan(
            self._plan(), self.registry, provider_readiness={"codex": {"available": True}},
        )
        self.assertFalse(any("provider_not_ready" in x for x in problems))

    def test_available_false_is_rejected(self):
        # Test B
        problems = validate_plan(
            self._plan(), self.registry, provider_readiness={"codex": {"available": False}},
        )
        matches = [x for x in problems if "provider_not_ready" in x]
        self.assertEqual(len(matches), 1)
        self.assertIn("codex", matches[0])
        self.assertIn("t", matches[0])
        self.assertEqual(matches[0], "t: provider_not_ready: codex")

    def test_missing_provider_entry_is_rejected(self):
        # Test C
        problems = validate_plan(self._plan(), self.registry, provider_readiness={})
        self.assertTrue(any("provider_not_ready: codex" in x for x in problems))

    def test_malformed_or_non_affirmative_availability_is_rejected(self):
        # Test D
        for bad_entry in ({}, {"available": None}, {"available": "true"}):
            with self.subTest(bad_entry=bad_entry):
                problems = validate_plan(
                    self._plan(), self.registry,
                    provider_readiness={"codex": bad_entry},
                )
                self.assertTrue(any("provider_not_ready: codex" in x for x in problems))

    def test_legacy_call_without_readiness_invents_no_failure(self):
        # Test E
        problems = validate_plan(self._plan(), self.registry)
        self.assertFalse(any("provider_not_ready" in x for x in problems))


if __name__ == "__main__":
    unittest.main()
