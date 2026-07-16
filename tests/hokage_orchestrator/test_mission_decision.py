from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.hokage_orchestrator.mission_decision import (
    MissionDecisionEngine,
    classify_mission,
)


def snapshot():
    return {
        "snapshot": {
            "providers": [
                {"provider": "codex", "status": "ready"},
                {"provider": "claude", "status": "ready"},
                {"provider": "ollama", "status": "ready"},
            ]
        }
    }


class MissionDecisionEngineTests(unittest.TestCase):
    def test_software_mission_selects_codex(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = MissionDecisionEngine(
                state_root=Path(temp),
                bootstrap_snapshot=snapshot(),
                local_model="qwen2.5-coder:3b",
            )
            result = engine.decide(
                mission_id="mission-test",
                intent={
                    "objective": "Fix Python tests in the repository",
                    "targets": ["tests/"],
                    "requested_outputs": ["test_evidence"],
                    "risk_level": "medium",
                    "intent_type": "implement_change",
                },
            )
            self.assertEqual(result["classification"]["category"], "software_engineering")
            self.assertEqual(result["selection"]["provider"], "codex")
            self.assertTrue(result["economy"]["minimum_savings_met"])
            self.assertTrue(
                result["authority"]["decision_does_not_authorize_execution"]
            )

    def test_report_does_not_match_repo_token(self):
        classification = classify_mission({
            "objective": "Summarize this report",
            "targets": [],
            "requested_outputs": ["summary"],
            "risk_level": "low",
            "intent_type": "general",
        })
        self.assertNotEqual(
            classification["category"],
            "software_engineering",
        )

    def test_summary_prefers_local_provider(self):
        classification = classify_mission({
            "objective": "Summarize this report",
            "targets": [],
            "requested_outputs": ["summary"],
            "risk_level": "low",
            "intent_type": "general",
        })
        self.assertEqual(classification["category"], "knowledge_processing")

    def test_high_complexity_local_requires_review(self):
        local_only = {
            "snapshot": {
                "providers": [
                    {"provider": "codex", "status": "unavailable"},
                    {"provider": "claude", "status": "unavailable"},
                    {"provider": "ollama", "status": "ready"},
                ]
            }
        }
        with tempfile.TemporaryDirectory() as temp:
            result = MissionDecisionEngine(
                state_root=Path(temp),
                bootstrap_snapshot=local_only,
                local_model="qwen2.5-coder:3b",
            ).decide(
                mission_id="mission-architecture",
                intent={
                    "objective": "Audit architecture and security risk",
                    "targets": ["tools/"],
                    "requested_outputs": ["audit"],
                    "risk_level": "high",
                    "intent_type": "inspect_and_review",
                },
            )
            self.assertEqual(
                result["selection"]["strategy"],
                "hybrid_review_required",
            )
            self.assertEqual(
                result["supervision"]["maximum_worker_attempts"],
                1,
            )

    def test_no_ready_provider_blocks(self):
        blocked = {"snapshot": {"providers": []}}
        with tempfile.TemporaryDirectory() as temp:
            result = MissionDecisionEngine(
                state_root=Path(temp),
                bootstrap_snapshot=blocked,
                local_model="qwen",
            ).decide(
                mission_id="mission-blocked",
                intent={
                    "objective": "General task",
                    "targets": [],
                    "requested_outputs": [],
                    "risk_level": "medium",
                    "intent_type": "general",
                },
            )
            self.assertEqual(result["selection"]["strategy"], "blocked")
