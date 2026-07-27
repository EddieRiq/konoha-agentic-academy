from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json, uuid

APPROVAL_STATES = {"pending", "approved", "rejected", "changes_requested"}
TEACHBACK_POLICIES = {"disabled", "optional", "required"}
EXECUTION_GATES = {"plan_approval", "separate_human_approval"}

EXECUTION_STATE_SCHEMA_VERSION = "1.0"
EXECUTION_STATUSES = {
    "in_progress",
    "waiting_for_approval",
    "executing",
    "completed",
    "failed",
    "blocked",
    "recovery_required",
}

@dataclass(frozen=True)
class AgentAssignment:
    task_id: str
    family: str
    provider: str
    model: str
    objective: str
    inputs: list[str]
    expected_output: str
    dependencies: list[str] = field(default_factory=list)
    private_context: bool = False
    network: bool = False
    mutation: bool = False
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_total_tokens: int = 0
    cost_class: str = "low"
    fallback: str = "stop"
    stop_condition: str = "boundary crossing or unavailable required evidence"
    execution_gate: str = ""

@dataclass
class MissionPlan:
    mission_id: str
    understanding: str
    explicit_facts: list[str]
    missing_context: list[str]
    assumptions_prohibited: list[str]
    complexity: str
    assignments: list[AgentAssignment]
    acceptance_criteria: list[str]
    approval_boundaries: list[str]
    estimated_tokens: int
    estimated_cost_class: str
    rationale: str
    approval: dict[str, Any] = field(default_factory=lambda: {
        "status": "pending", "approved_by": None, "approved_at": None, "feedback": None
    })
    teachback_policy: str = "disabled"
    workspace_policy: dict[str, Any] = field(default_factory=lambda: {
        "workspace_mutation_allowed": False,
        "private_runtime_state_allowed": True,
        "private_state_root": "alliance/kirigakure/state/konoha_v4",
    })
    budget: dict[str, Any] = field(default_factory=lambda: {
        "provider_totals": [],
        "family_totals": [],
        "replanning_reserve_tokens": 0,
        "maximum_total_tokens": 0,
    })
    governance: dict[str, str] = field(default_factory=lambda: {
        "conductor": "codex", "constitutional_authority": "hokage"
    })
    plan_hash: str = ""

    def seal(self) -> "MissionPlan":
        raw = asdict(self)
        raw["plan_hash"] = ""
        self.plan_hash = hashlib.sha256(
            json.dumps(raw, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()[:16]
        return self

@dataclass
class EvidenceRecord:
    evidence_id: str
    mission_id: str
    task_id: str
    provider: str
    model: str
    status: str
    output: str
    token_usage: dict[str, int]
    command: list[str]
    started_at: float
    finished_at: float
    output_hash: str

    @classmethod
    def build(cls, **kwargs: Any) -> "EvidenceRecord":
        output = str(kwargs["output"])
        return cls(
            evidence_id="evidence-" + uuid.uuid4().hex[:12],
            output_hash=hashlib.sha256(output.encode()).hexdigest(),
            **kwargs,
        )


@dataclass
class ExecutionState:
    """Persisted, resumable progress of a single mission's execution.

    Progress tracking only: by itself this never satisfies
    separate_human_approval - see executor.py.
    """
    schema_version: str
    mission_id: str
    plan_identity: str
    status: str
    next_assignment_index: int
    completed_task_ids: list[str] = field(default_factory=list)
    pending_task_id: str | None = None
    pending_execution_gate: str | None = None
    approval_nonce: str | None = None
    active_approval_id: str | None = None
    consumed_approval_ids: list[str] = field(default_factory=list)
    evidence_ids_by_task: dict[str, str] = field(default_factory=dict)
    executing_task_id: str | None = None
    pause_reason: str | None = None
    diagnostic: str | None = None
    updated_at: str = ""


@dataclass(frozen=True)
class AssignmentApproval:
    """A human's explicit, single-use authorization for one gated assignment.

    Carries no authenticated operator identity, only a descriptive
    approval_source. Validity is decided by
    executor._validate_assignment_approval against the persisted
    ExecutionState, never by this object alone.
    """
    mission_id: str
    task_id: str
    execution_gate: str
    plan_identity: str
    approval_nonce: str
    approval_text: str
    approval_source: str
    approved_at: str
