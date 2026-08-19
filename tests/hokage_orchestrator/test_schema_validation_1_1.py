import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List

from tools.hokage_orchestrator import charter as charter_module
from tools.hokage_orchestrator import mission_decision
from tools.hokage_orchestrator import skill_runtime
from tools.hokage_orchestrator.skill_runtime import ActionQueue

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "runtime"

INTENT = {
    "schema_version": "1.0.0",
    "report_type": "conversational_intent",
    "intent_type": "implement_change",
    "objective": "fix the failing audit checks",
    "targets": ["/repo"],
    "constraints": [],
    "requested_outputs": ["patch_proposal", "test_evidence"],
    "missing_context": [],
    "risk_level": "medium",
    "requires_charter": True,
    "authority": {
        "intent_is_not_permission": True,
        "model_output_is_evidence_only": True,
        "explicit_approval_required": True,
    },
}

SNAPSHOT = {
    "providers": [
        {"provider": "codex", "status": "ready"},
        {"provider": "ollama", "status": "ready"},
    ]
}

HUMAN_CONSTRAINTS = {
    "mutation_forbidden": False,
    "network_blocked": False,
    "local_model_only": False,
    "private_context_restricted": True,
}


def _load_schema(name: str) -> Dict[str, Any]:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _check_type(instance: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(instance, dict)
    if schema_type == "array":
        return isinstance(instance, list)
    if schema_type == "string":
        return isinstance(instance, str)
    if schema_type == "boolean":
        return isinstance(instance, bool)
    if schema_type == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if schema_type == "integer":
        return isinstance(instance, int) and not isinstance(instance, bool)
    return True


def _validate(instance: Any, schema: Dict[str, Any], schema_dir: Path) -> List[str]:
    """Minimal, dependency-free JSON Schema subset validator. No
    jsonschema package is installed in this environment - the same
    situation tests/konoha_v4/test_assignment_execution_gate.py already
    documents and works around; this follows that established pattern.
    Supports exactly the keywords the 1.1 schemas in this block use: type,
    const, enum, required, properties, additionalProperties, items,
    minLength, maxLength, uniqueItems, and $ref - resolved as a local
    sibling file in schema_dir, fully offline, no network/registry."""

    if "$ref" in schema:
        ref_schema = json.loads((schema_dir / schema["$ref"]).read_text(encoding="utf-8"))
        return _validate(instance, ref_schema, schema_dir)

    errors: List[str] = []

    schema_type = schema.get("type")
    if schema_type is not None and not _check_type(instance, schema_type):
        errors.append(f"expected type {schema_type}, got {type(instance).__name__}")
        return errors

    if "const" in schema and instance != schema["const"]:
        errors.append(f"expected const {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{instance!r} not in enum {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"string shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"string longer than maxLength {schema['maxLength']}")

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"missing required key: {key}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            if key in properties:
                errors.extend(
                    f"{key}.{err}" for err in _validate(value, properties[key], schema_dir)
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"unexpected additional property: {key}")

    if isinstance(instance, list):
        if schema.get("uniqueItems") and len(instance) != len(set(instance)):
            errors.append("array items are not unique")
        items_schema = schema.get("items")
        if items_schema is not None:
            for index, item in enumerate(instance):
                errors.extend(
                    f"[{index}].{err}" for err in _validate(item, items_schema, schema_dir)
                )

    return errors


def _seed(root: Path):
    mission_dir = root / "missions" / "mission-1"
    mission_dir.mkdir(parents=True)
    decision = mission_decision.build_decision_1_1(
        mission_id="mission-1",
        intent=INTENT,
        bootstrap_snapshot=SNAPSHOT,
        local_model="qwen2.5-coder:7b",
        human_constraints=HUMAN_CONSTRAINTS,
        provider_skill_id="invoke_local_model_audit",
    )
    charter = charter_module.build_charter_1_1(
        INTENT, decision, actor="Eduardo", human_constraints=HUMAN_CONSTRAINTS
    )
    approved = charter_module.approve_charter_1_1(
        mission_dir,
        charter,
        decision,
        approval_phrase=charter["approval_phrase"],
        approved_by="Eduardo",
    )
    return mission_dir, decision, approved


class SchemaValidation1_1Tests(unittest.TestCase):
    def test_decision_1_1_matches_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, decision, _ = _seed(Path(tmp))
            schema = _load_schema("hokage_mission_decision.v2.schema.json")
            self.assertEqual(_validate(decision, schema, SCHEMA_DIR), [])

    def test_charter_1_1_matches_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, approved = _seed(Path(tmp))
            schema = _load_schema("conversational_mission_charter.v2.schema.json")
            self.assertEqual(_validate(approved, schema, SCHEMA_DIR), [])

    def test_action_queue_and_nested_actions_match_schema_via_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir, decision, approved = _seed(Path(tmp))
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            self.assertGreaterEqual(len(payload["actions"]), 1)

            schema = _load_schema("conversational_action_queue.schema.json")
            self.assertEqual(_validate(payload, schema, SCHEMA_DIR), [])

            # Confirm the $ref is actually load-bearing, not decorative:
            # each action also validates standalone against the schema it
            # points to.
            action_schema = _load_schema("conversational_action_proposal.v2.schema.json")
            for action in payload["actions"]:
                self.assertEqual(_validate(action, action_schema, SCHEMA_DIR), [])

    def test_action_queue_schema_ref_catches_invalid_nested_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir, decision, approved = _seed(Path(tmp))
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")

            tampered = json.loads(json.dumps(payload))
            tampered["actions"][0]["tier"] = "not-a-real-tier"

            schema = _load_schema("conversational_action_queue.schema.json")
            errors = _validate(tampered, schema, SCHEMA_DIR)
            self.assertTrue(any("tier" in error for error in errors), errors)

    def test_execution_claim_matches_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir, decision, approved = _seed(Path(tmp))
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]

            claim = skill_runtime._publish_execution_claim(
                mission_dir, action, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )

            schema = _load_schema("conversational_execution_claim.schema.json")
            self.assertEqual(_validate(claim, schema, SCHEMA_DIR), [])

    def test_execution_claim_schema_is_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission_dir, decision, approved = _seed(Path(tmp))
            queue = ActionQueue(mission_dir)
            payload = queue.initialize(mission_id="mission-1", plan_id="plan-1")
            action = payload["actions"][0]
            claim = skill_runtime._publish_execution_claim(
                mission_dir, action, approved_by="Eduardo", approved_at=skill_runtime.utc_now()
            )

            tampered = dict(claim)
            tampered["unexpected_extra_field"] = "should not be allowed"

            schema = _load_schema("conversational_execution_claim.schema.json")
            errors = _validate(tampered, schema, SCHEMA_DIR)
            self.assertTrue(any("unexpected_extra_field" in error for error in errors), errors)

    def test_legacy_1_0_decision_still_matches_its_own_untouched_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = mission_decision.MissionDecisionEngine(
                state_root=root / "runtime",
                bootstrap_snapshot=SNAPSHOT,
                local_model="qwen2.5-coder:7b",
            )
            payload = engine.decide(mission_id="mission-1", intent=INTENT)
            schema = _load_schema("hokage_mission_decision.schema.json")
            self.assertEqual(_validate(payload, schema, SCHEMA_DIR), [])


if __name__ == "__main__":
    unittest.main()
