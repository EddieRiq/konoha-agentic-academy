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

if __name__ == "__main__":
    unittest.main()
