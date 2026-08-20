from __future__ import annotations
import hashlib, json, math, os, re, secrets, subprocess, time
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from .continuity import utc_now
from .models import (
    ASSIGNMENT_RESULT_OUTCOMES,
    ASSIGNMENT_REVIEW_OUTCOMES,
    EXECUTION_GATES,
    EXECUTION_STATE_SCHEMA_VERSION,
    EXECUTION_STATUSES,
    AgentAssignment,
    AssignmentApproval,
    AssignmentResult,
    EvidenceRecord,
    ExecutionState,
    MissionPlan,
)
from .provider_adapters import invoke
from .registry import CapabilityRegistry, RegistryError

def _gate_satisfied(plan: MissionPlan, task) -> bool:
    gate = task.execution_gate
    if gate not in EXECUTION_GATES:
        return False
    if gate == "plan_approval":
        return plan.approval.get("status") == "approved"
    return False  # separate_human_approval: siempre bloqueado en este Patch A.

def _blocked_evidence(plan: MissionPlan, task) -> EvidenceRecord:
    now = time.time()
    return EvidenceRecord.build(
        mission_id=plan.mission_id, task_id=task.task_id,
        provider=task.provider, model=task.model, status="blocked",
        output=(
            "Assignment execution gate bloqueado. "
            f"task_id={task.task_id} execution_gate={task.execution_gate!r}."
        ),
        token_usage={}, command=[],
        started_at=now, finished_at=now,
    )

def _mutation_blocked_evidence(plan: MissionPlan, task) -> EvidenceRecord:
    now = time.time()
    return EvidenceRecord.build(
        mission_id=plan.mission_id, task_id=task.task_id,
        provider=task.provider, model=task.model, status="blocked",
        output=(
            "mutation_runtime_not_supported: el runtime de worktree aislado "
            f"para mutación todavía no existe. task_id={task.task_id}."
        ),
        token_usage={}, command=[],
        started_at=now, finished_at=now,
    )

class GitStatusError(RuntimeError):
    """Git status could not be trusted: non-zero exit or timeout.

    Never lets a caller read a stdout string in either case - the function
    either returns real output or raises, so a timeout can never be
    misread as an empty (clean) working tree.
    """

    def __init__(self, diagnostic: str, *, detail: str = "") -> None:
        super().__init__(diagnostic if not detail else f"{diagnostic}: {detail}")
        self.diagnostic = diagnostic


def _git_status(repo: Path, timeout: int = 120) -> str:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        cp = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "status", "--short", "--untracked-files=all"],
            cwd=repo, text=True, capture_output=True, check=False,
            timeout=timeout, env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise GitStatusError("git_status_timeout") from exc
    if cp.returncode != 0:
        raise GitStatusError("git_status_failed", detail=cp.stderr.strip())
    return cp.stdout

KONOHA_ROOT = Path(__file__).resolve().parents[2]
# The assignment-result schema belongs to Konoha's own installation, not to
# the target workspace being audited: `repo` is the caller-supplied
# workspace under inspection (often a public/external repository) and has
# no reason to carry schemas/runtime/*.schema.json of its own.
ASSIGNMENT_RESULT_SCHEMA_PATH = (
    KONOHA_ROOT / "schemas" / "runtime" / "konoha_v4_assignment_result.schema.json"
)

_ASSIGNMENT_RESULT_REQUIRED_KEYS = {
    "outcome", "objective_satisfied", "summary", "diagnostic", "evidence", "review_outcome",
}

_ASSIGNMENT_OUTCOME_MAPPING = {
    "completed": ("completed", "completed"),
    "blocked": ("blocked", "blocked"),
    "changes_requested": ("blocked", "changes_requested"),
    "failed": ("failed", "assignment_failed"),
}


def _validate_assignment_result_payload(payload: object) -> str | None:
    """Structural check mirroring konoha_v4_assignment_result.schema.json.

    Returns "invalid_result_schema" on any structural mismatch, else None.
    Never inspects free text (summary/diagnostic) for content - only field
    presence, types, and enum membership. isinstance(str) is always checked
    before any `in <set>` membership test on an enum-constrained field -
    payload comes from untrusted json.loads() output, so an unhashable
    value (a list or dict) must never reach `in` on a set, which would
    raise TypeError instead of failing closed.
    """
    if not isinstance(payload, dict) or set(payload) != _ASSIGNMENT_RESULT_REQUIRED_KEYS:
        return "invalid_result_schema"
    outcome = payload["outcome"]
    if not isinstance(outcome, str) or outcome not in ASSIGNMENT_RESULT_OUTCOMES:
        return "invalid_result_schema"
    if not isinstance(payload["objective_satisfied"], bool):
        return "invalid_result_schema"
    if not isinstance(payload["summary"], str) or not payload["summary"].strip():
        return "invalid_result_schema"
    diagnostic = payload["diagnostic"]
    if diagnostic is not None and not isinstance(diagnostic, str):
        return "invalid_result_schema"
    evidence = payload["evidence"]
    if not isinstance(evidence, list):
        return "invalid_result_schema"
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"source", "observation"}:
            return "invalid_result_schema"
        if not isinstance(item["source"], str) or not item["source"].strip():
            return "invalid_result_schema"
        if not isinstance(item["observation"], str) or not item["observation"].strip():
            return "invalid_result_schema"
    review_outcome = payload["review_outcome"]
    if review_outcome is not None and (
        not isinstance(review_outcome, str)
        or review_outcome not in ASSIGNMENT_REVIEW_OUTCOMES
    ):
        return "invalid_result_schema"
    return None


def _validate_assignment_result_rules(payload: dict, family: str) -> str | None:
    """Deterministic business rules - never scans free text for content.

    outcome/objective_satisfied must correlate; family=="jounin-review"
    tasks must carry a review_outcome that itself correlates exactly with
    outcome/objective_satisfied; every other family must carry
    review_outcome=None. Returns "contradictory_result_fields" on any
    violation, else None. Only called after _validate_assignment_result_payload
    has already confirmed outcome/review_outcome are well-typed.
    """
    outcome = payload["outcome"]
    objective_satisfied = payload["objective_satisfied"]
    review_outcome = payload["review_outcome"]

    if outcome == "completed":
        if objective_satisfied is not True:
            return "contradictory_result_fields"
    elif objective_satisfied is not False:
        return "contradictory_result_fields"

    if family == "jounin-review":
        if review_outcome is None:
            return "contradictory_result_fields"
        if review_outcome in {"approved", "approved_with_notes"}:
            if outcome != "completed" or objective_satisfied is not True:
                return "contradictory_result_fields"
        elif review_outcome == "blocked":
            if outcome != "blocked" or objective_satisfied is not False:
                return "contradictory_result_fields"
        elif review_outcome == "changes_requested":
            if outcome != "changes_requested" or objective_satisfied is not False:
                return "contradictory_result_fields"
    elif review_outcome is not None:
        return "contradictory_result_fields"

    return None


_FENCE_HEADER_PATTERN = re.compile(r"^```(json)?\r?\n")
# Language marker is optional-empty or exactly "json" - no other format is
# inferred (Markdown, YAML fences, etc. are never recognized as JSON).


def _extract_single_fenced_block(stripped: str) -> str:
    """stripped already starts with an opening ``` - validate it is exactly
    one complete code fence (empty or `json` language marker) spanning the
    whole (already-whitespace-trimmed) string, and return its inner body
    verbatim. Raises ValueError on any deviation: unknown language marker or
    an unterminated fence. Does not itself reject a second fence marker
    inside the body (that would also reject a JSON string field that
    legitimately contains a literal "```" substring) - a concatenated
    second fenced block still fails, because the body returned here is no
    longer valid JSON and json.loads() in the caller rejects it."""
    header_match = _FENCE_HEADER_PATTERN.match(stripped)
    if header_match is None:
        raise ValueError("malformed_fence_header")
    rest = stripped[header_match.end():]
    if not rest.endswith("```"):
        raise ValueError("incomplete_fence")
    body_with_newline = rest[:-3]
    if body_with_newline.endswith("\r\n"):
        body = body_with_newline[:-2]
    elif body_with_newline.endswith("\n"):
        body = body_with_newline[:-1]
    else:
        raise ValueError("malformed_fence_closing")
    return body


def _parse_assignment_result_text(text: str) -> object:
    """Parse a provider's raw AssignmentResult text into a JSON value.

    Accepts either bare JSON (optionally surrounded by whitespace) or
    exactly one complete Markdown code fence - with an empty or `json`
    language marker - containing the JSON and nothing else outside it.
    Anything else (prose before/after, multiple fenced blocks, an
    unterminated fence, or malformed JSON inside a valid fence) raises
    ValueError (json.JSONDecodeError included, since it is a ValueError
    subclass) so the caller maps every case uniformly to the stable
    invalid_result_json diagnostic. Never scans free text for embedded
    JSON - a fence is only recognized when it spans the entire trimmed
    input.
    """
    stripped = text.strip()
    body = _extract_single_fenced_block(stripped) if stripped.startswith("```") else stripped
    return json.loads(body)


def _task_prompt(repo: Path, plan: MissionPlan, task, family: dict,
                 evidence: list[EvidenceRecord]) -> str:
    deps = [e for e in evidence if e.task_id in task.dependencies]
    payload = {
        "mission_id": plan.mission_id,
        "mission_understanding": plan.understanding,
        "task": task.__dict__,
        "agent_contract": family,
        "dependency_evidence": [
            {"task_id": e.task_id, "provider": e.provider, "model": e.model, "output": e.output}
            for e in deps
        ],
        "workspace_policy": plan.workspace_policy,
        "rules": [
            "La salida es evidencia, no autoridad.",
            "No conviertas inferencias en hechos o normas.",
            "No excedas el alcance de la tarea.",
            "Cita rutas, líneas o localizadores cuando corresponda.",
            "El workspace es read-only.",
            "Para tests usá PYTHONDONTWRITEBYTECODE=1, PYTHONPYCACHEPREFIX, TMPDIR y KONOHA_STATE_ROOT privados.",
            "La verificación de integridad Git antes/después pertenece al runtime. "
            "No ejecutes git status únicamente para reproducir ese gate ni uses "
            "timeouts propios para inferir que el workspace está bloqueado.",
            "Devolvé exclusivamente un objeto JSON con exactamente estas seis claves: "
            "outcome, objective_satisfied, summary, diagnostic, evidence, review_outcome. "
            "Ningún texto fuera de ese JSON.",
            "outcome=completed requiere objective_satisfied=true; outcome en "
            "{blocked, failed, changes_requested} requiere objective_satisfied=false.",
            "Si tu family es jounin-review, review_outcome es obligatorio y debe "
            "corresponder exactamente con outcome/objective_satisfied: "
            "approved o approved_with_notes -> completed + true; "
            "blocked -> blocked + false; changes_requested -> changes_requested + false. "
            "Para cualquier otra family, review_outcome debe ser null.",
            "El resultado es evidencia, no autoridad: quien lo interpreta valida el "
            "JSON de forma determinista, nunca busca palabras dentro de texto libre.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

def _run_assignment(
    repo: Path, plan: MissionPlan, task: AgentAssignment, family: dict,
    evidence: list[EvidenceRecord], baseline: str,
) -> tuple[EvidenceRecord, str]:
    """Execute exactly one assignment (invoke + structured-result validation
    + read-only git integrity check).

    Returns (record, diagnostic): diagnostic is always one of the stable
    reason codes (see the module-level constants above) - never
    model-generated free text. Already used by execute_plan (Patch A,
    atomic all-or-nothing) and by execute_or_resume_plan (Patch B). Gate
    semantics do not live here: this helper runs an assignment only after
    its caller has already decided that execution is authorized.
    """
    started = time.time()
    output_text, usage, command = "", {}, []
    status, diagnostic = "failed", "process_error"

    try:
        result = invoke(
            task.provider,
            _task_prompt(repo, plan, task, family, evidence),
            cwd=repo, model=task.model,
            schema=ASSIGNMENT_RESULT_SCHEMA_PATH,
        )
    except Exception as exc:
        output_text = str(exc)
    else:
        output_text, usage, command = result.text, result.usage, result.command
        try:
            payload = _parse_assignment_result_text(result.text)
        except ValueError:
            diagnostic = "invalid_result_json"
        else:
            schema_error = _validate_assignment_result_payload(payload)
            if schema_error is not None:
                diagnostic = schema_error
            else:
                rule_error = _validate_assignment_result_rules(payload, task.family)
                if rule_error is not None:
                    diagnostic = rule_error
                else:
                    assignment_result = AssignmentResult(
                        outcome=payload["outcome"],
                        objective_satisfied=payload["objective_satisfied"],
                        summary=payload["summary"],
                        diagnostic=payload["diagnostic"],
                        evidence=tuple(payload["evidence"]),
                        review_outcome=payload["review_outcome"],
                    )
                    status, diagnostic = _ASSIGNMENT_OUTCOME_MAPPING[assignment_result.outcome]

    try:
        after = _git_status(repo)
    except GitStatusError as exc:
        status, diagnostic = "failed", exc.diagnostic
        output_text = f"{exc.diagnostic}: la verificación Git posterior a la ejecución falló."
    else:
        if after != baseline:
            status, diagnostic = "failed", "workspace_mutation_detected"
            output_text = (
                "El estado Git cambió durante una tarea read-only. "
                "La ejecución fue detenida.\n\nANTES:\n" + baseline + "\nDESPUÉS:\n" + after
            )

    record = EvidenceRecord.build(
        mission_id=plan.mission_id, task_id=task.task_id,
        provider=task.provider, model=task.model, status=status,
        output=output_text, token_usage=usage, command=command,
        started_at=started, finished_at=time.time(),
    )
    return record, diagnostic


def execute_plan(repo: Path, plan: MissionPlan, registry: CapabilityRegistry,
                 state_dir: Path) -> list[EvidenceRecord]:
    mutating_task = next((task for task in plan.assignments if task.mutation), None)
    if mutating_task is not None:
        record = _mutation_blocked_evidence(plan, mutating_task)
        _persist(state_dir, record)
        return [record]

    offenders = [task for task in plan.assignments if not _gate_satisfied(plan, task)]
    if offenders:
        evidence: list[EvidenceRecord] = []
        for task in offenders:
            record = _blocked_evidence(plan, task)
            evidence.append(record)
            _persist(state_dir, record)
        return evidence

    first_task = plan.assignments[0]
    try:
        baseline = _git_status(repo)
    except GitStatusError as exc:
        now = time.time()
        record = EvidenceRecord.build(
            mission_id=plan.mission_id, task_id=first_task.task_id,
            provider=first_task.provider, model=first_task.model, status="failed",
            output=f"{exc.diagnostic}: no se pudo capturar el estado Git base antes de ejecutar.",
            token_usage={}, command=[], started_at=now, finished_at=now,
        )
        _persist(state_dir, record)
        return [record]

    evidence: list[EvidenceRecord] = []
    for task in plan.assignments:
        family = registry.agent_family(task.family)
        record, _diagnostic = _run_assignment(repo, plan, task, family, evidence, baseline)
        evidence.append(record)
        _persist(state_dir, record)
        if record.status != "completed":
            break
    return evidence

def _persist(state_dir: Path, record: EvidenceRecord) -> None:
    out = state_dir / "missions" / record.mission_id / "evidence"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{record.evidence_id}.json").write_text(
        json.dumps(record.__dict__, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Patch B - Assignment Pause / Persist / Resume
#
# Everything above this line is Patch A and is unchanged in behavior.
# execute_plan keeps its atomic all-or-nothing preflight contract. The code
# below adds persisted-state foundations, approval validation, invariant
# checks, mission locking, and pure E1 transitions - all built for a future
# execute_or_resume_plan integration in E5. E5 is not implemented in this
# checkpoint.
# ---------------------------------------------------------------------------

MISSION_ID_PATTERN = re.compile(r"^mission-[a-z0-9-]+$")
# Identical to the pattern declared for mission_id in
# schemas/runtime/konoha_v4_mission_plan.schema.json (that file is not
# modified here, only its contract is reused). Already rejects "/", "\\",
# "..", empty strings and control characters: only [a-z0-9-] is allowed
# after the "mission-" prefix. Confirmed compatible with the real
# mission_ids used across planner/conversation/tests (e.g. "mission-1",
# "mission-x", "mission-gate-test").


class MissionLookupError(RuntimeError):
    """A mission_id could not be resolved to a safe, existing mission directory."""


class ExecutionStateError(RuntimeError):
    """Persisted execution_state.json is missing, corrupt, or structurally incompatible."""


def plan_identity(plan: MissionPlan) -> str:
    """Deterministic identity of a plan's operative content.

    Excludes only `approval` and `plan_hash`: approval status legitimately
    changes (pending -> approved) without invalidating a paused execution,
    but everything else - assignments, order, budget, providers, objectives,
    acceptance criteria, boundaries - participates, so any of it changing
    after a pause is treated as plan drift. Does not modify or reuse
    MissionPlan.seal()/plan_hash. Compact separators make the canonical form
    unambiguous (no incidental whitespace differences between equal dicts).
    """
    raw = asdict(plan)
    raw.pop("approval", None)
    raw.pop("plan_hash", None)
    canonical = json.dumps(
        raw,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_mission_id(mission_id: str) -> None:
    if not isinstance(mission_id, str) or not MISSION_ID_PATTERN.fullmatch(mission_id):
        raise MissionLookupError(f"mission_id inválido: {mission_id!r}")


def _mission_dir(state_dir: Path, mission_id: str) -> Path:
    """Resolve mission_id to a directory strictly confined to state_dir/missions.

    _validate_mission_id already forbids "/", "\\", "..", empty strings and
    control characters via MISSION_ID_PATTERN; the parent-equality check
    below is defense in depth against any future relaxation of that pattern.
    """
    _validate_mission_id(mission_id)
    root = (state_dir / "missions").resolve()
    candidate = (root / mission_id).resolve()
    if candidate.parent != root:
        raise MissionLookupError(f"mission_id fuera de state_dir/missions: {mission_id!r}")
    return candidate


def load_persisted_plan(state_dir: Path, mission_id: str) -> MissionPlan:
    """Strictly reconstruct a MissionPlan previously written by conversation._persist_plan.

    Rejects an unknown mission_id, a mission_id shaped as path traversal, a
    missing plan.json, unreadable/corrupt content, or a structure whose
    field set doesn't match MissionPlan/AgentAssignment exactly - so a
    missing execution_gate (or any other field) can never be silently
    papered over by a dataclass default.
    """
    mission_dir = _mission_dir(state_dir, mission_id)
    plan_path = mission_dir / "plan.json"
    if not plan_path.is_file():
        raise MissionLookupError(f"No existe plan persistido para {mission_id!r}")
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MissionLookupError(f"plan.json ilegible o corrupto para {mission_id!r}") from exc
    if not isinstance(raw, dict):
        raise MissionLookupError(f"plan.json no es un objeto para {mission_id!r}")

    plan_fields = {f.name for f in fields(MissionPlan)}
    if set(raw) != plan_fields:
        raise MissionLookupError(
            f"plan.json con campos incompatibles con MissionPlan para {mission_id!r}: "
            f"faltantes={sorted(plan_fields - set(raw))} "
            f"desconocidos={sorted(set(raw) - plan_fields)}"
        )

    items = raw.get("assignments")
    if not isinstance(items, list):
        raise MissionLookupError(f"plan.json 'assignments' no es una lista para {mission_id!r}")

    assignment_fields = {f.name for f in fields(AgentAssignment)}
    for item in items:
        if not isinstance(item, dict) or set(item) != assignment_fields:
            raise MissionLookupError(
                f"plan.json con assignment incompatible con AgentAssignment para {mission_id!r}"
            )

    try:
        assignments = [AgentAssignment(**item) for item in items]
        kwargs = dict(raw)
        kwargs["assignments"] = assignments
        plan = MissionPlan(**kwargs)
    except TypeError as exc:
        raise MissionLookupError(
            f"plan.json con estructura incompatible para {mission_id!r}"
        ) from exc

    if plan.mission_id != mission_id:
        raise MissionLookupError(
            f"plan.json mission_id={plan.mission_id!r} no coincide con {mission_id!r}"
        )
    return plan


def _execution_state_path(state_dir: Path, mission_id: str) -> Path:
    # Reuses _mission_dir so every read/write of execution_state.json goes
    # through the same mission_id validation and containment check as
    # load_persisted_plan and evidence lookups - no path is ever built from
    # an unvalidated mission_id.
    return _mission_dir(state_dir, mission_id) / "execution_state.json"


def _save_execution_state(state_dir: Path, state: ExecutionState) -> None:
    path = _execution_state_path(state_dir, state.mission_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(state), ensure_ascii=False, indent=2)
    tmp_path = path.with_name(path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    os.replace(tmp_path, path)


EVIDENCE_ID_PATTERN = re.compile(r"^evidence-[0-9a-f]{12}$")
# Matches EvidenceRecord.build()'s real format in models.py:
# "evidence-" + uuid.uuid4().hex[:12].

SHA256_HEX_PATTERN = re.compile(r"^[0-9a-f]{64}$")
# Used for plan_identity() output and for consumed_approval_ids /
# active_approval_id elements (all are deterministic SHA-256 hex digests -
# see plan_identity and _approval_id).


def _non_empty_str(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


_EXECUTION_STATE_FIELD_TYPES = {
    "schema_version": str,
    "mission_id": str,
    "plan_identity": str,
    "status": str,
    "next_assignment_index": int,
    "completed_task_ids": list,
    "pending_task_id": (str, type(None)),
    "pending_execution_gate": (str, type(None)),
    "approval_nonce": (str, type(None)),
    "active_approval_id": (str, type(None)),
    "consumed_approval_ids": list,
    "evidence_ids_by_task": dict,
    "executing_task_id": (str, type(None)),
    "pause_reason": (str, type(None)),
    "diagnostic": (str, type(None)),
    "updated_at": str,
}


def _load_execution_state(state_dir: Path, mission_id: str) -> ExecutionState | None:
    """Load and strictly validate execution_state.json, or None if absent.

    Fails closed (raises ExecutionStateError) on anything that isn't an
    exact match for the current schema - unreadable/invalid JSON, unknown
    schema version, missing/extra/mistyped fields, an unknown status, a
    malformed plan_identity, or empty/malformed/duplicate ids where none are
    allowed. Never repairs or defaults a broken file.
    """
    path = _execution_state_path(state_dir, mission_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExecutionStateError("execution_state.json ilegible o con JSON inválido") from exc
    if not isinstance(raw, dict):
        raise ExecutionStateError("execution_state.json no es un objeto JSON")
    if raw.get("schema_version") != EXECUTION_STATE_SCHEMA_VERSION:
        raise ExecutionStateError(
            f"execution_state.json schema_version desconocida: {raw.get('schema_version')!r}"
        )
    required = {f.name for f in fields(ExecutionState)}
    if set(raw) != required:
        raise ExecutionStateError(
            "execution_state.json con campos incompatibles: "
            f"faltantes={sorted(required - set(raw))} "
            f"desconocidos={sorted(set(raw) - required)}"
        )
    for key, expected_type in _EXECUTION_STATE_FIELD_TYPES.items():
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, expected_type):
            raise ExecutionStateError(f"execution_state.json campo con tipo incorrecto: {key}")
    if raw["status"] not in EXECUTION_STATUSES:
        raise ExecutionStateError(f"execution_state.json con status desconocido: {raw['status']!r}")
    if raw["next_assignment_index"] < 0:
        raise ExecutionStateError("execution_state.json next_assignment_index negativo")
    if not SHA256_HEX_PATTERN.fullmatch(raw["plan_identity"]):
        raise ExecutionStateError("execution_state.json plan_identity con formato inválido")

    completed = raw["completed_task_ids"]
    if not all(_non_empty_str(x) for x in completed):
        raise ExecutionStateError(
            "execution_state.json completed_task_ids con elementos inválidos"
        )
    # Duplicate-freedom of completed_task_ids is verified by _verify_prefix,
    # which also needs the plan to check prefix order - not checked here.

    consumed = raw["consumed_approval_ids"]
    if not all(
        isinstance(x, str) and SHA256_HEX_PATTERN.fullmatch(x)
        for x in consumed
    ):
        raise ExecutionStateError(
            "execution_state.json consumed_approval_ids con formato inválido"
        )
    if len(set(consumed)) != len(consumed):
        raise ExecutionStateError("execution_state.json consumed_approval_ids con duplicados")

    evidence_map = raw["evidence_ids_by_task"]
    if not all(
        isinstance(k, str) and isinstance(v, str)
        and _non_empty_str(k) and EVIDENCE_ID_PATTERN.fullmatch(v)
        for k, v in evidence_map.items()
    ):
        raise ExecutionStateError("execution_state.json evidence_ids_by_task inválido")

    for key in (
        "pending_task_id",
        "pending_execution_gate",
        "approval_nonce",
        "active_approval_id",
        "executing_task_id",
        "pause_reason",
        "diagnostic",
    ):
        value = raw[key]
        if value is not None and not _non_empty_str(value):
            raise ExecutionStateError(
                f"execution_state.json campo vacío o inválido: {key}"
            )
    if not _non_empty_str(raw["updated_at"]):
        raise ExecutionStateError("execution_state.json updated_at vacío o inválido")
    if (
        raw["active_approval_id"] is not None
        and not SHA256_HEX_PATTERN.fullmatch(raw["active_approval_id"])
    ):
        raise ExecutionStateError(
            "execution_state.json active_approval_id con formato inválido"
        )
    # El nonce y las combinaciones válidas de campos por status se validan
    # en el bloque de invariantes de ejecución, no aquí.

    if raw["mission_id"] != mission_id:
        raise ExecutionStateError(
            f"execution_state.json mission_id={raw['mission_id']!r} no coincide con {mission_id!r}"
        )
    return ExecutionState(**raw)


def _verify_prefix(plan: MissionPlan, state: ExecutionState) -> str | None:
    """completed_task_ids must be an exact, duplicate-free prefix of the
    plan's current assignment order, with a matching cursor."""
    if len(set(state.completed_task_ids)) != len(state.completed_task_ids):
        return "completed_task_ids_duplicated"
    plan_task_ids = [a.task_id for a in plan.assignments]
    n = len(state.completed_task_ids)
    if plan_task_ids[:n] != state.completed_task_ids:
        return "completed_task_ids_not_a_prefix"
    if state.next_assignment_index != n:
        return "cursor_index_mismatch"
    return None


_EVIDENCE_REQUIRED_KEYS = {
    "evidence_id", "mission_id", "task_id", "provider", "model", "status",
    "output", "token_usage", "command", "started_at", "finished_at", "output_hash",
}


def _verify_completed_evidence(
    state_dir: Path, plan: MissionPlan, state: ExecutionState,
) -> tuple[str | None, list[EvidenceRecord]]:
    """Re-read and verify every completed task's evidence from disk.

    diagnostic is None only if every completed_task_id has a matching,
    parseable, hash-verified, status=completed EvidenceRecord for the right
    mission_id/task_id, confined to the mission's own evidence directory,
    with every field at the strict type/shape EvidenceRecord declares.
    Never reconstructs, repairs, or coerces a corrupt field (no str(...) on
    output) - any mismatch is reported and the caller must refuse to resume.
    """
    records: list[EvidenceRecord] = []
    mission_dir = _mission_dir(state_dir, plan.mission_id)
    evidence_dir = (mission_dir / "evidence").resolve()
    if evidence_dir.parent != mission_dir:
        return "missing_or_corrupt_completed_evidence", []
    for task_id in state.completed_task_ids:
        evidence_id = state.evidence_ids_by_task.get(task_id)
        if (
            not isinstance(evidence_id, str)
            or not EVIDENCE_ID_PATTERN.fullmatch(evidence_id)
        ):
            return "missing_or_corrupt_completed_evidence", []
        path = (evidence_dir / f"{evidence_id}.json").resolve()
        if path.parent != evidence_dir:
            return "missing_or_corrupt_completed_evidence", []
        if not path.is_file():
            return "missing_or_corrupt_completed_evidence", []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return "missing_or_corrupt_completed_evidence", []
        if not isinstance(payload, dict) or set(payload) != _EVIDENCE_REQUIRED_KEYS:
            return "missing_or_corrupt_completed_evidence", []

        if not _non_empty_str(payload["evidence_id"]) or payload["evidence_id"] != evidence_id:
            return "missing_or_corrupt_completed_evidence", []
        if not EVIDENCE_ID_PATTERN.fullmatch(payload["evidence_id"]):
            return "missing_or_corrupt_completed_evidence", []
        if not _non_empty_str(payload["mission_id"]) or payload["mission_id"] != plan.mission_id:
            return "missing_or_corrupt_completed_evidence", []
        if not _non_empty_str(payload["task_id"]) or payload["task_id"] != task_id:
            return "missing_or_corrupt_completed_evidence", []
        if not _non_empty_str(payload["provider"]):
            return "missing_or_corrupt_completed_evidence", []
        if not isinstance(payload["model"], str):
            return "missing_or_corrupt_completed_evidence", []
        if not _non_empty_str(payload["status"]) or payload["status"] != "completed":
            return "missing_or_corrupt_completed_evidence", []
        if not isinstance(payload["output"], str):
            return "missing_or_corrupt_completed_evidence", []
        if not _non_empty_str(payload["output_hash"]):
            return "missing_or_corrupt_completed_evidence", []

        # token_usage: dict[str, int] per EvidenceRecord's own annotation.
        token_usage = payload["token_usage"]
        if not isinstance(token_usage, dict) or not all(
            isinstance(k, str) and isinstance(v, int) and not isinstance(v, bool) and v >= 0
            for k, v in token_usage.items()
        ):
            return "missing_or_corrupt_completed_evidence", []

        # command: list[str] per EvidenceRecord's own annotation.
        command = payload["command"]
        if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
            return "missing_or_corrupt_completed_evidence", []

        started_at = payload["started_at"]
        finished_at = payload["finished_at"]
        if isinstance(started_at, bool) or not isinstance(started_at, (int, float)):
            return "missing_or_corrupt_completed_evidence", []
        if isinstance(finished_at, bool) or not isinstance(finished_at, (int, float)):
            return "missing_or_corrupt_completed_evidence", []
        try:
            timestamps_are_finite = (
                math.isfinite(started_at) and math.isfinite(finished_at)
            )
        except (OverflowError, TypeError):
            return "missing_or_corrupt_completed_evidence", []
        if not timestamps_are_finite:
            return "missing_or_corrupt_completed_evidence", []
        if started_at > finished_at:
            return "missing_or_corrupt_completed_evidence", []

        expected_hash = hashlib.sha256(payload["output"].encode("utf-8")).hexdigest()
        if payload["output_hash"] != expected_hash:
            return "missing_or_corrupt_completed_evidence", []

        records.append(EvidenceRecord(**payload))
    return None, records


def _approval_id(approval: AssignmentApproval) -> str:
    """Deterministic identity of one approval's authorizing content.

    Explicit payload (not asdict()) so a future AssignmentApproval field
    never silently enters the hash. Excludes approved_at: changing only the
    timestamp must never mint a new semantic authority. Mirrors
    plan_identity()'s canonical-JSON + SHA-256 approach.
    """
    payload = {
        "mission_id": approval.mission_id,
        "task_id": approval.task_id,
        "execution_gate": approval.execution_gate,
        "plan_identity": approval.plan_identity,
        "approval_nonce": approval.approval_nonce,
        "approval_text": approval.approval_text,
        "approval_source": approval.approval_source,
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def expected_approval_command(
    mission_id: str,
    task_id: str,
    plan_identity_value: str,
    approval_nonce: str,
) -> str:
    # execution_gate is intentionally not a parameter: the gate is a fixed
    # contract constant, never caller-controlled input.
    return (
        f":aprobar-assignment {mission_id} {task_id} separate_human_approval "
        f"{plan_identity_value} {approval_nonce}"
    )


def _validate_assignment_approval(
    approval: AssignmentApproval | None,
    plan: MissionPlan,
    state: ExecutionState,
    task: AgentAssignment,
) -> tuple[bool, str | None, str | None]:
    """Fail-closed validation of a single-use assignment approval.

    Returns (valid, approval_id, reason). approval_id is populated only
    when valid, or when the sole rejection reason is replay
    (approval_already_consumed) - never for any other rejection. Pure:
    never touches disk, git, or the provider, and never mutates state,
    plan, or approval.
    """
    if not isinstance(approval, AssignmentApproval):
        return False, None, "no_approval_provided"

    if not all(_non_empty_str(v) for v in asdict(approval).values()):
        return False, None, "approval_missing_fields"

    if approval.approval_source != "interactive_terminal":
        return False, None, "approval_source_mismatch"

    if approval.mission_id != plan.mission_id or approval.mission_id != state.mission_id:
        return False, None, "mission_id_mismatch"

    if approval.task_id != task.task_id or approval.task_id != state.pending_task_id:
        return False, None, "task_id_mismatch"

    if state.status != "waiting_for_approval":
        return False, None, "no_pending_approval"

    if (
        approval.execution_gate != "separate_human_approval"
        or task.execution_gate != "separate_human_approval"
        or state.pending_execution_gate != "separate_human_approval"
    ):
        return False, None, "gate_mismatch"

    current_identity = plan_identity(plan)
    if approval.plan_identity != current_identity or state.plan_identity != current_identity:
        return False, None, "plan_identity_mismatch"

    if approval.approval_nonce != state.approval_nonce:
        return False, None, "nonce_mismatch"

    expected_text = expected_approval_command(
        approval.mission_id, approval.task_id,
        approval.plan_identity, approval.approval_nonce,
    )
    if approval.approval_text != expected_text:
        return False, None, "unexpected_command_text"

    approval_id = _approval_id(approval)
    if approval_id in state.consumed_approval_ids:
        return False, approval_id, "approval_already_consumed"

    return True, approval_id, None


# ---------------------------------------------------------------------------
# Patch B - Bloque D: Execution-State Invariants + Mission Lock
# ---------------------------------------------------------------------------

APPROVAL_NONCE_PATTERN = re.compile(r"^[0-9a-f]{32}$")
# Matches secrets.token_hex(16)'s output format exactly (32 lowercase hex chars).

NON_RESUMABLE_EXECUTION_STATUSES = {
    "completed",
    "failed",
    "blocked",
    "recovery_required",
}
# Contract for a future resumable executor: these statuses never resume
# automatically. No execution branch is implemented for them in Patch B.


def _validate_execution_state_invariants(
    plan: MissionPlan,
    state: ExecutionState,
) -> str | None:
    """Pure structural/consistency check of a persisted ExecutionState against its plan.

    Returns None only if state is internally consistent with plan and with
    its own declared status; otherwise a stable diagnostic string. Never
    touches disk, git, or the provider, and never mutates plan or state.

    Plans with zero assignments are rejected upstream by the mission-plan
    schema (assignments has minItems: 1), but this function fails closed on
    its own regardless: it never treats an empty plan as valid, even if
    called with a plan that bypassed schema validation.
    """
    if state.mission_id != plan.mission_id:
        return "mission_id_mismatch"
    if state.plan_identity != plan_identity(plan):
        return "plan_drift"

    if not plan.assignments:
        return "empty_plan_assignments"

    total = len(plan.assignments)
    if not (0 <= state.next_assignment_index <= total):
        return "cursor_out_of_range"

    prefix_error = _verify_prefix(plan, state)
    if prefix_error is not None:
        return prefix_error

    plan_task_ids = {a.task_id for a in plan.assignments}
    referenced_task_ids = (
        state.pending_task_id,
        state.executing_task_id,
        *state.evidence_ids_by_task.keys(),
    )
    if any(
        task_id is not None and task_id not in plan_task_ids
        for task_id in referenced_task_ids
    ):
        return "unknown_referenced_task"

    if state.approval_nonce is not None and not APPROVAL_NONCE_PATTERN.fullmatch(state.approval_nonce):
        return "invalid_approval_nonce"

    if state.active_approval_id is not None:
        if not SHA256_HEX_PATTERN.fullmatch(state.active_approval_id):
            return "invalid_active_approval_id_format"
        if state.active_approval_id in state.consumed_approval_ids:
            return "active_approval_id_already_consumed"

    current_task = (
        plan.assignments[state.next_assignment_index]
        if state.next_assignment_index < total else None
    )

    if state.status == "in_progress":
        if (
            state.pending_task_id is not None
            or state.pending_execution_gate is not None
            or state.approval_nonce is not None
            or state.active_approval_id is not None
            or state.executing_task_id is not None
        ):
            return "invalid_state_for_in_progress"
        return None

    if state.status == "waiting_for_approval":
        if (
            current_task is None
            or current_task.execution_gate != "separate_human_approval"
            or state.pending_task_id != current_task.task_id
            or state.pending_execution_gate != "separate_human_approval"
            or state.approval_nonce is None
            or state.active_approval_id is not None
            or state.executing_task_id is not None
            or not _non_empty_str(state.pause_reason)
        ):
            return "invalid_state_for_waiting_for_approval"
        return None

    if state.status == "executing":
        if (
            current_task is None
            or state.executing_task_id != current_task.task_id
            or state.pending_task_id != current_task.task_id
            or state.pending_execution_gate != current_task.execution_gate
        ):
            return "invalid_state_for_executing"
        if current_task.execution_gate == "separate_human_approval":
            if (
                state.approval_nonce is None
                or state.active_approval_id is None
                or state.active_approval_id in state.consumed_approval_ids
            ):
                return "invalid_state_for_executing"
        elif current_task.execution_gate == "plan_approval":
            if state.approval_nonce is not None or state.active_approval_id is not None:
                return "invalid_state_for_executing"
        else:
            return "invalid_state_for_executing"
        return None

    if state.status == "completed":
        plan_task_ids_in_order = [a.task_id for a in plan.assignments]
        if (
            state.next_assignment_index != total
            or state.completed_task_ids != plan_task_ids_in_order
            or state.pending_task_id is not None
            or state.pending_execution_gate is not None
            or state.approval_nonce is not None
            or state.active_approval_id is not None
            or state.executing_task_id is not None
        ):
            return "invalid_state_for_completed"
        return None

    if state.status == "failed":
        if (
            current_task is None
            or state.pending_task_id != current_task.task_id
            or state.pending_execution_gate != current_task.execution_gate
            or state.executing_task_id is not None
            or state.active_approval_id is not None
            or state.approval_nonce is not None
            or not _non_empty_str(state.diagnostic)
        ):
            return "invalid_state_for_failed"
        return None

    if state.status == "blocked":
        if (
            current_task is None
            or state.pending_task_id != current_task.task_id
            or state.pending_execution_gate != current_task.execution_gate
            or state.approval_nonce is not None
            or state.active_approval_id is not None
            or state.executing_task_id is not None
            or not _non_empty_str(state.pause_reason)
        ):
            return "invalid_state_for_blocked"
        return None

    if state.status == "recovery_required":
        if not _non_empty_str(state.diagnostic):
            return "invalid_state_for_recovery_required"
        return None

    return "unknown_execution_status"


class _MissionLock:
    """A filesystem-backed inter-process lock for one mission's execution.

    Path: state_dir/missions/<mission_id>/execution.lock, resolved through
    _mission_dir() so the mission_id is validated and confined exactly like
    every other mission-scoped path.

    Known limitations (explicit, Patch B scope):
    - No stale-lock recovery: a lock left behind by a crashed process is
      never detected or reclaimed automatically.
    - Single active process per mission is assumed - no PID probing,
      daemon, or timeout.
    - A crash can leave execution.lock behind; manual recovery (deleting it
      by hand) remains outside Patch B.
    """

    def __init__(self, state_dir: Path, mission_id: str) -> None:
        self._path = _mission_dir(state_dir, mission_id) / "execution.lock"
        self._held = False

    def acquire(self) -> bool:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ExecutionStateError(
                f"No se pudo preparar el directorio de execution.lock: {exc}"
            ) from exc
        try:
            fd = os.open(str(self._path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            return False
        except OSError as exc:
            raise ExecutionStateError(f"No se pudo crear execution.lock: {exc}") from exc

        try:
            os.close(fd)
        except OSError as exc:
            # The file we just created via O_EXCL is necessarily our own -
            # no preexisting lock is touched here.
            try:
                os.unlink(self._path)
            except OSError:
                pass
            raise ExecutionStateError(f"No se pudo finalizar execution.lock: {exc}") from exc

        self._held = True
        return True

    def release(self) -> None:
        if not self._held:
            return

        try:
            os.unlink(self._path)
        except FileNotFoundError:
            self._held = False
            return
        except OSError as exc:
            raise ExecutionStateError(f"No se pudo liberar execution.lock: {exc}") from exc

        self._held = False


# ---------------------------------------------------------------------------
# Patch B - Bloque E1: ExecutionAttempt + pure transitions
#
# Everything below is pure: no disk, no git, no invoke, no utc_now(), no
# secrets.token_hex(). Every helper takes updated_at explicitly and returns a
# new ExecutionState via dataclasses.replace - it never mutates its inputs.
# The clock and randomness live exclusively in execute_or_resume_plan (E5).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExecutionAttempt:
    """The outer, per-call result of execute_or_resume_plan.

    Not a per-task record - EvidenceRecord already is that. Each call
    resolves at most one gate or runs at most one assignment; driving a
    mission to completion means calling execute_or_resume_plan repeatedly.

    state is the last ExecutionState the runtime considers coherent for
    this call - not a guarantee that it is durably persisted:
      - it is None only when no state could be established at all
        (diagnostic in {"unsafe_mission_id", "lock_acquire_error",
        "lock_busy", "plan_load_error", "state_load_error",
        "empty_plan_assignments"}, or "lock_release_error" layered on top
        of one of those).
      - a diagnostic ending in "_persist_failed" means a write was
        attempted and failed - the returned state was not (or not yet)
        made durable by this call.
      - "plan_approval_not_satisfied" never even attempts a write, by
        design (see execute_or_resume_plan) - for a brand-new mission this
        can return a state that has never touched disk at all, not just
        one whose last write failed.
      - "lock_release_error" always preserves state/evidence exactly as
        already computed by this same call, whichever of the above (or
        none of them) applies.
    invoke is never called before "executing" is durably persisted, and a
    persistence failure after invoke never triggers an automatic
    re-invocation - the next call always finds status=="executing" on disk
    and routes to recovery_required instead. diagnostic is never empty.
    """
    state: ExecutionState | None
    evidence: tuple[EvidenceRecord, ...]
    diagnostic: str


def _new_execution_state(plan: MissionPlan, updated_at: str) -> ExecutionState:
    """Fresh in_progress state for a mission with nothing persisted yet.

    Never itself persisted directly - execute_or_resume_plan validates it in
    memory and only writes whatever real transition the first task reaches.
    """
    return ExecutionState(
        schema_version=EXECUTION_STATE_SCHEMA_VERSION,
        mission_id=plan.mission_id,
        plan_identity=plan_identity(plan),
        status="in_progress",
        next_assignment_index=0,
        completed_task_ids=[],
        pending_task_id=None,
        pending_execution_gate=None,
        approval_nonce=None,
        active_approval_id=None,
        consumed_approval_ids=[],
        evidence_ids_by_task={},
        executing_task_id=None,
        pause_reason=None,
        diagnostic=None,
        updated_at=updated_at,
    )


def _state_with_timestamp(state: ExecutionState, updated_at: str, **changes) -> ExecutionState:
    """dataclasses.replace with updated_at always set - the one place every
    transition below stamps the caller-supplied timestamp."""
    return replace(state, updated_at=updated_at, **changes)


# Not called by execute_or_resume_plan: a plan_approval-gated task whose
# plan isn't approved yet stays in_progress unmutated instead (see
# execute_or_resume_plan's "plan_approval_not_satisfied" path), so that it
# stays resumable. Kept for a possible future explicit operator-pause
# capability.
def _transition_to_blocked(
    state: ExecutionState, task: AgentAssignment, reason: str, updated_at: str,
) -> ExecutionState:
    return _state_with_timestamp(
        state, updated_at,
        status="blocked",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        approval_nonce=None,
        active_approval_id=None,
        executing_task_id=None,
        pause_reason=reason,
        diagnostic=reason,
    )


def _transition_to_waiting(
    state: ExecutionState, task: AgentAssignment, nonce: str, pause_reason: str,
    updated_at: str,
) -> ExecutionState:
    return _state_with_timestamp(
        state, updated_at,
        status="waiting_for_approval",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        approval_nonce=nonce,
        active_approval_id=None,
        executing_task_id=None,
        pause_reason=pause_reason,
        diagnostic=None,
    )


def _transition_to_executing(
    state: ExecutionState,
    task: AgentAssignment,
    active_approval_id: str | None,
    updated_at: str,
) -> ExecutionState:
    """Enter executing without consuming the assignment approval.

    A separate-human-approval execution preserves its persisted nonce and
    activates the validated approval ID. A plan-approved execution carries
    neither field, regardless of values accidentally supplied by the caller.
    """
    is_separate_approval = (
        task.execution_gate == "separate_human_approval"
    )
    return _state_with_timestamp(
        state,
        updated_at,
        status="executing",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        executing_task_id=task.task_id,
        approval_nonce=(
            state.approval_nonce if is_separate_approval else None
        ),
        active_approval_id=(
            active_approval_id if is_separate_approval else None
        ),
        pause_reason=None,
        diagnostic=None,
    )


def _transition_after_completed_assignment(
    state: ExecutionState, plan: MissionPlan, task: AgentAssignment,
    evidence: EvidenceRecord, approval_id_to_consume: str | None, updated_at: str,
) -> ExecutionState:
    completed_task_ids = state.completed_task_ids + [task.task_id]
    evidence_ids_by_task = dict(state.evidence_ids_by_task)
    evidence_ids_by_task[task.task_id] = evidence.evidence_id
    consumed_approval_ids = list(state.consumed_approval_ids)
    if approval_id_to_consume is not None and approval_id_to_consume not in consumed_approval_ids:
        consumed_approval_ids.append(approval_id_to_consume)
    next_index = state.next_assignment_index + 1
    status = "completed" if next_index >= len(plan.assignments) else "in_progress"
    return _state_with_timestamp(
        state, updated_at,
        status=status,
        next_assignment_index=next_index,
        completed_task_ids=completed_task_ids,
        pending_task_id=None,
        pending_execution_gate=None,
        approval_nonce=None,
        active_approval_id=None,
        executing_task_id=None,
        pause_reason=None,
        diagnostic=None,
        evidence_ids_by_task=evidence_ids_by_task,
        consumed_approval_ids=consumed_approval_ids,
    )


def _transition_after_failed_assignment(
    state: ExecutionState, plan: MissionPlan, task: AgentAssignment,
    evidence: EvidenceRecord, approval_id_to_consume: str | None,
    diagnostic: str, updated_at: str,
) -> ExecutionState:
    """Cursor and completed_task_ids stay put - the failed task is never
    marked completed. evidence_ids_by_task is untouched: that map only ever
    tracks completed tasks' evidence, matching _verify_completed_evidence's
    own use of it. diagnostic is the caller-supplied stable reason code
    (EvidenceRecord.status is now uniformly "failed" for every failure
    sub-reason, so the precise reason can no longer be derived from it);
    pause_reason is cleared - failed carries no pause context."""
    consumed_approval_ids = list(state.consumed_approval_ids)
    if approval_id_to_consume is not None and approval_id_to_consume not in consumed_approval_ids:
        consumed_approval_ids.append(approval_id_to_consume)
    return _state_with_timestamp(
        state, updated_at,
        status="failed",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        executing_task_id=None,
        active_approval_id=None,
        approval_nonce=None,
        pause_reason=None,
        diagnostic=diagnostic,
        consumed_approval_ids=consumed_approval_ids,
    )


def _transition_after_blocked_assignment(
    state: ExecutionState, plan: MissionPlan, task: AgentAssignment,
    evidence: EvidenceRecord, approval_id_to_consume: str | None,
    diagnostic: str, updated_at: str,
) -> ExecutionState:
    """Same shape as _transition_after_failed_assignment but status="blocked".
    Reached only after invoke actually ran and the provider's own structured
    result declared outcome/review_outcome blocked or changes_requested -
    never from provider process failure or malformed output (those go
    through _transition_after_failed_assignment instead). diagnostic is the
    caller-supplied stable reason code ("blocked" or "changes_requested"),
    stored as both pause_reason and diagnostic."""
    consumed_approval_ids = list(state.consumed_approval_ids)
    if approval_id_to_consume is not None and approval_id_to_consume not in consumed_approval_ids:
        consumed_approval_ids.append(approval_id_to_consume)
    return _state_with_timestamp(
        state, updated_at,
        status="blocked",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        executing_task_id=None,
        active_approval_id=None,
        approval_nonce=None,
        pause_reason=diagnostic,
        diagnostic=diagnostic,
        consumed_approval_ids=consumed_approval_ids,
    )


def _transition_to_failed_before_execution(
    state: ExecutionState, task: AgentAssignment, diagnostic: str,
    approval_id_to_consume: str | None, updated_at: str,
) -> ExecutionState:
    """Same shape as _transition_after_failed_assignment but no EvidenceRecord
    exists - the task never actually ran (e.g. unknown_agent_family)."""
    consumed_approval_ids = list(state.consumed_approval_ids)
    if approval_id_to_consume is not None and approval_id_to_consume not in consumed_approval_ids:
        consumed_approval_ids.append(approval_id_to_consume)
    return _state_with_timestamp(
        state, updated_at,
        status="failed",
        pending_task_id=task.task_id,
        pending_execution_gate=task.execution_gate,
        executing_task_id=None,
        active_approval_id=None,
        approval_nonce=None,
        pause_reason=None,
        diagnostic=diagnostic,
        consumed_approval_ids=consumed_approval_ids,
    )


def _recovery_result(state: ExecutionState, diagnostic: str, updated_at: str) -> ExecutionState:
    """Changes only status/diagnostic/updated_at. Preserves executing_task_id,
    active_approval_id, approval_nonce, pending_task_id, pending_execution_gate,
    the cursor, completed_task_ids, consumed_approval_ids and
    evidence_ids_by_task - recovery must not erase where execution stopped."""
    return _state_with_timestamp(
        state, updated_at,
        status="recovery_required",
        diagnostic=diagnostic,
    )


# ---------------------------------------------------------------------------
# Patch B - Resumable Execution Runtime: execute_or_resume_plan
#
# The orchestrator. Every call does at most one gate resolution or one
# assignment run, persisting each intermediate transition (including
# "executing", written before invoke ever runs) so a crash between any two
# disk writes is always safely recoverable by the next call - see the
# persistence-failure diagnostics below and docs/guides/
# konoha_v4_resumable_execution_runtime.md.
# ---------------------------------------------------------------------------


def _try_save_execution_state(state_dir: Path, state: ExecutionState) -> bool:
    """_save_execution_state's real, unwrapped failure surface is OSError
    (mkdir/open/write/replace) - verified by reading its source, not
    assumed. Reports success/failure instead of propagating, so the caller
    can fail closed with a stable diagnostic instead of crashing."""
    try:
        _save_execution_state(state_dir, state)
        return True
    except OSError:
        return False


def _try_persist_evidence(state_dir: Path, record: EvidenceRecord) -> bool:
    """_persist's real, unwrapped failure surface is OSError (mkdir/
    write_text) - verified the same way."""
    try:
        _persist(state_dir, record)
        return True
    except OSError:
        return False


def _execute_or_resume_plan_locked(
    repo: Path,
    state_dir: Path,
    mission_id: str,
    registry: CapabilityRegistry,
    approval: AssignmentApproval | None,
) -> ExecutionAttempt:
    """One resumable step. Assumes the mission lock is already held by the
    caller - never acquires or releases it. See execute_or_resume_plan."""
    now = utc_now()

    try:
        plan = load_persisted_plan(state_dir, mission_id)
    except MissionLookupError:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="plan_load_error")

    if not plan.assignments:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="empty_plan_assignments")

    try:
        existing_state = _load_execution_state(state_dir, mission_id)
    except ExecutionStateError:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="state_load_error")

    # _new_execution_state can never itself fail invariants for a non-empty
    # plan (every field it sets is exactly what a fresh in_progress state
    # requires) - so an invariant failure below always has a real prior
    # persisted state behind it, and _recover always has something
    # meaningful to build a recovery_required state from.
    state = existing_state if existing_state is not None else _new_execution_state(plan, now)

    def _recover(diagnostic: str) -> ExecutionAttempt:
        new_state = _recovery_result(state, diagnostic, now)
        if not _try_save_execution_state(state_dir, new_state):
            return ExecutionAttempt(state=state, evidence=(), diagnostic="recovery_persist_failed")
        return ExecutionAttempt(state=new_state, evidence=(), diagnostic=diagnostic)

    invariant_error = _validate_execution_state_invariants(plan, state)
    if invariant_error is not None:
        return _recover(invariant_error)

    if state.status in NON_RESUMABLE_EXECUTION_STATUSES:
        return ExecutionAttempt(
            state=state, evidence=(), diagnostic=f"non_resumable_status:{state.status}",
        )

    if state.status == "executing":
        # The previous call persisted "executing" before invoking the
        # provider and never reached the next persisted transition - crash,
        # kill, or a persistence failure after invoke. Never re-invoke
        # blindly; a human must reconcile.
        return _recover("interrupted_while_executing")

    evidence_diagnostic, completed_records = _verify_completed_evidence(state_dir, plan, state)
    if evidence_diagnostic is not None:
        return _recover(evidence_diagnostic)

    if state.next_assignment_index >= len(plan.assignments):
        # Passed invariants but has nothing left to do without being
        # "completed" - only reachable via external tampering, never via our
        # own transitions. Fail closed instead of an IndexError.
        return _recover("cursor_exhausted_without_completed_status")

    current_task = plan.assignments[state.next_assignment_index]
    approval_id_to_consume: str | None = None

    def _fail_before_execution(diagnostic: str, consumed: str | None) -> ExecutionAttempt:
        new_state = _transition_to_failed_before_execution(
            state, current_task, diagnostic, consumed, now,
        )
        if not _try_save_execution_state(state_dir, new_state):
            return ExecutionAttempt(
                state=state, evidence=(), diagnostic="failed_before_execution_persist_failed",
            )
        return ExecutionAttempt(state=new_state, evidence=(), diagnostic=diagnostic)

    def _block_before_execution(diagnostic: str) -> ExecutionAttempt:
        new_state = _transition_to_blocked(state, current_task, diagnostic, now)
        if not _try_save_execution_state(state_dir, new_state):
            return ExecutionAttempt(
                state=state, evidence=(), diagnostic="blocked_before_execution_persist_failed",
            )
        return ExecutionAttempt(state=new_state, evidence=(), diagnostic=diagnostic)

    # Mutation is not supported until an isolated worktree runtime exists.
    # Checked before any gate/approval logic, before family resolution,
    # before the Git baseline, and before invoke - so a supplied
    # separate_human_approval is never even validated, let alone consumed,
    # and "waiting_for_approval" is never offered for a mutating task.
    if current_task.mutation:
        return _block_before_execution("mutation_runtime_not_supported")

    # Gate/approval validated PURELY here - no "executing" is persisted yet.
    if current_task.execution_gate == "plan_approval":
        if plan.approval.get("status") != "approved":
            # Never mutated, never persisted: plan.json is re-read fresh on
            # every call, so approving it through the normal approval path
            # and calling again is enough to make progress.
            return ExecutionAttempt(
                state=state, evidence=(), diagnostic="plan_approval_not_satisfied",
            )

    elif current_task.execution_gate == "separate_human_approval":
        if state.status != "waiting_for_approval":
            nonce = secrets.token_hex(16)
            new_state = _transition_to_waiting(
                state, current_task, nonce, "esperando aprobación humana", now,
            )
            if not _try_save_execution_state(state_dir, new_state):
                return ExecutionAttempt(state=state, evidence=(), diagnostic="waiting_persist_failed")
            return ExecutionAttempt(state=new_state, evidence=(), diagnostic="waiting_for_approval")

        if approval is None:
            return ExecutionAttempt(state=state, evidence=(), diagnostic="waiting_for_approval")

        valid, approval_id, reason = _validate_assignment_approval(approval, plan, state, current_task)
        if not valid:
            # _validate_assignment_approval is pure and never mutates state;
            # returning it unchanged keeps the mission waiting so the
            # operator can retry.
            return ExecutionAttempt(state=state, evidence=(), diagnostic=reason)

        approval_id_to_consume = approval_id

    else:
        # Unreachable given AgentAssignment.execution_gate is schema/
        # validator constrained to EXECUTION_GATES; defensive fail-closed
        # exit regardless.
        return _fail_before_execution("unknown_execution_gate", None)

    try:
        family = registry.agent_family(current_task.family)
    except RegistryError:
        return _fail_before_execution("unknown_agent_family", approval_id_to_consume)

    # Git baseline captured before "executing" is ever persisted: a failure
    # here (timeout or non-zero exit) resolves to a clean, direct "failed"
    # state via _fail_before_execution - never to "executing" limbo that
    # would only resolve via recovery_required on the next call. The
    # approval is deliberately NOT consumed on this path (consumed=None)
    # even if it was already validated above.
    try:
        baseline = _git_status(repo)
    except GitStatusError as exc:
        return _fail_before_execution(exc.diagnostic, None)

    # Only now: persist "executing". _transition_to_executing already
    # discriminates plan_approval vs separate_human_approval internally
    # (forces approval_nonce/active_approval_id to None for plan_approval
    # regardless of what's passed), so approval_id_to_consume (None for
    # plan_approval) can be passed unconditionally.
    new_state = _transition_to_executing(state, current_task, approval_id_to_consume, now)
    if not _try_save_execution_state(state_dir, new_state):
        return ExecutionAttempt(state=state, evidence=(), diagnostic="executing_persist_failed")
    state = new_state

    evidence, run_diagnostic = _run_assignment(repo, plan, current_task, family, completed_records, baseline)

    if not _try_persist_evidence(state_dir, evidence):
        # invoke already ran and state is still the persisted "executing"
        # snapshot - the next call will see status=="executing" and route to
        # interrupted_while_executing, never re-invoking.
        return ExecutionAttempt(state=state, evidence=(), diagnostic="evidence_persist_failed")

    finished_at = utc_now()
    if evidence.status == "completed":
        new_state = _transition_after_completed_assignment(
            state, plan, current_task, evidence, approval_id_to_consume, finished_at,
        )
    elif evidence.status == "blocked":
        new_state = _transition_after_blocked_assignment(
            state, plan, current_task, evidence, approval_id_to_consume, run_diagnostic, finished_at,
        )
    else:
        new_state = _transition_after_failed_assignment(
            state, plan, current_task, evidence, approval_id_to_consume, run_diagnostic, finished_at,
        )

    if not _try_save_execution_state(state_dir, new_state):
        # Evidence is safely on disk and state is still "executing" - same
        # recovery path as evidence_persist_failed on the next call, with
        # the evidence available for manual reconciliation.
        return ExecutionAttempt(
            state=state, evidence=(evidence,), diagnostic="final_transition_persist_failed",
        )

    return ExecutionAttempt(state=new_state, evidence=(evidence,), diagnostic=run_diagnostic)


def execute_or_resume_plan(
    repo: Path,
    state_dir: Path,
    mission_id: str,
    registry: CapabilityRegistry,
    approval: AssignmentApproval | None = None,
) -> ExecutionAttempt:
    """Resumable, crash-safe execution of one mission, one step per call.

    Call repeatedly (the same way for a brand-new mission or one resumed
    after a restart) until state.status is a terminal or paused status.

    Acquires the mission lock and always attempts to release it via
    try/finally-equivalent control flow, regardless of whether
    _execute_or_resume_plan_locked returns normally or raises anything -
    including KeyboardInterrupt/SystemExit, since this runtime is driven
    from an interactive terminal. An unexpected exception from it (or from
    _git_status/registry/invoke underneath it) is never converted into a
    fabricated success:
      - body returns normally, release fails: returns an ExecutionAttempt
        with diagnostic="lock_release_error", preserving state/evidence
        exactly as already computed;
      - body raises, release succeeds: the original exception propagates
        unchanged;
      - body raises, release also fails: the original exception still
        propagates (never replaced by a fabricated result), chained to the
        release failure via `raise ... from ...` so both are observable
        (release_exc is raised.__cause__). ExceptionGroup/except* (PEP 654)
        is not used - this repo supports Python >=3.10 and that syntax
        requires 3.11+.
    """
    try:
        _validate_mission_id(mission_id)
    except MissionLookupError:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="unsafe_mission_id")

    lock = _MissionLock(state_dir, mission_id)
    try:
        acquired = lock.acquire()
    except ExecutionStateError:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="lock_acquire_error")
    if not acquired:
        return ExecutionAttempt(state=None, evidence=(), diagnostic="lock_busy")

    try:
        attempt = _execute_or_resume_plan_locked(repo, state_dir, mission_id, registry, approval)
    except BaseException as body_exc:
        try:
            lock.release()
        except ExecutionStateError as release_exc:
            raise body_exc from release_exc
        raise
    else:
        try:
            lock.release()
        except ExecutionStateError:
            return ExecutionAttempt(
                state=attempt.state, evidence=attempt.evidence, diagnostic="lock_release_error",
            )
        return attempt
