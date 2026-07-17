import unittest
from tools.konoha_v4.models import MissionPlan, AgentAssignment
from tools.konoha_v4.conversation import classify_approval

class ConversationContractTest(unittest.TestCase):
    def test_new_plan_defaults(self):
        plan = MissionPlan(
            mission_id="mission-test", understanding="A sufficiently explicit mission",
            explicit_facts=[], missing_context=[], assumptions_prohibited=[],
            complexity="low", assignments=[], acceptance_criteria=["safe"],
            approval_boundaries=["read_only"], estimated_tokens=0,
            estimated_cost_class="low", rationale="test",
        )
        self.assertEqual("pending", plan.approval["status"])
        self.assertEqual("disabled", plan.teachback_policy)
        self.assertFalse(plan.workspace_policy["workspace_mutation_allowed"])
        self.assertEqual("codex", plan.governance["conductor"])
        self.assertEqual("hokage", plan.governance["constitutional_authority"])

    def test_silence_is_not_consent_or_rejection(self):
        self.assertEqual("pending", classify_approval(""))
        self.assertNotEqual("approved", classify_approval(""))
        self.assertNotEqual("rejected", classify_approval(""))

if __name__ == "__main__":
    unittest.main()
