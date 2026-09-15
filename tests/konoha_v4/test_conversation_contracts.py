import typing
import unittest
from tools.konoha_v4.models import MissionPlan, AgentAssignment
from tools.konoha_v4.conversation import _build_validated_plan, classify_approval

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

    def test_build_validated_plan_type_hints_resolve(self):
        # MissionPlan must be a real runtime import in conversation.py (not
        # TYPE_CHECKING-only), or get_type_hints() raises NameError since
        # `from __future__ import annotations` stores annotations as strings.
        hints = typing.get_type_hints(_build_validated_plan)
        self.assertIs(typing.get_args(hints["return"])[0], MissionPlan)

if __name__ == "__main__":
    unittest.main()
