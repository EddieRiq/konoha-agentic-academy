"""Focused contract tests for tools/konoha_v4/required_sources.py (v4.2.0
Gate B) - exercises the real, currently-written resolver and the real
agents/families/*.json files, never a mock or a re-derived copy.

No network, no model invocation, no writes outside tempfile.TemporaryDirectory,
no private/ignored-path inspection, no sleeps, no background processes, no
dependency installation.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tools.konoha_v4.models import AgentAssignment, EvidenceRecord
from tools.konoha_v4.required_sources import (
    ResolutionContext,
    SOURCE_VOCABULARY,
    SourceAvailability,
    SourceKind,
    UnknownSourceError,
    evaluate_produced_source_material,
    extract_produced_source_ids,
    find_undeclared_produced_sources,
    resolve_required_sources,
)
from tools.repo_evidence.acquire_repo_evidence import (
    Authorization,
    acquire_repo_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FAMILIES_DIR = REPO_ROOT / "agents" / "families"

EXPECTED_FAMILY_NAMES = {
    "instruction-architect", "integration-review", "jounin-review",
    "mission-conductor", "python-implementation", "python-review",
    "python-static-review", "scientific-writing-review",
    "source-extraction", "source-synthesis",
}

PRODUCIBLE_SOURCES = ("implementation_diff", "test_evidence", "review_evidence", "source_fact_cards")


# ---------------------------------------------------------------------------
# Shared helpers - small, local, no external test-support framework.
# ---------------------------------------------------------------------------

def _load_family(name: str) -> dict:
    return json.loads((FAMILIES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _task(task_id: str = "t1", family: str = "python-review",
          dependencies: tuple[str, ...] = (), inputs: tuple[str, ...] = ()) -> AgentAssignment:
    return AgentAssignment(
        task_id=task_id, family=family, provider="codex", model="provider_default",
        objective="obj", inputs=list(inputs), expected_output="out",
        dependencies=list(dependencies),
    )


def _evidence(task_id: str, rows: list[dict[str, str]], status: str = "completed") -> EvidenceRecord:
    output = json.dumps({
        "outcome": "completed" if status == "completed" else "failed",
        "objective_satisfied": status == "completed",
        "summary": "ok", "diagnostic": None, "evidence": rows, "review_outcome": None,
    })
    return EvidenceRecord.build(
        mission_id="m1", task_id=task_id, provider="codex", model="provider_default",
        status=status, output=output, token_usage={}, command=[],
        started_at=time.time(), finished_at=time.time(),
    )


def _marker_row(source_id: str) -> dict[str, str]:
    return {"source": "produced_source", "observation": f"source_id={source_id}"}


def _material_row(source_id: str, **kv: str) -> dict[str, str]:
    observation = " | ".join(f"{k}={v}" for k, v in kv.items())
    return {"source": f"material:{source_id}", "observation": observation}


def _ctx(**overrides) -> ResolutionContext:
    base = dict(
        plan_approval_status="approved", plan_acceptance_criteria=(), user_mission_request=None,
        repo_root=None, repo_evidence_pack=None, family_contracts={}, task_family_by_id={},
        evidence_by_task_id={}, failure_log_dir=None,
    )
    base.update(overrides)
    return ResolutionContext(**base)


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init"],
        cwd=root, check=True,
    )


# ---------------------------------------------------------------------------
# 1. Canonical vocabulary
# ---------------------------------------------------------------------------

class CanonicalVocabularyTest(unittest.TestCase):
    def test_every_vocabulary_id_resolves_by_its_declared_kind(self):
        """Every SOURCE_VOCABULARY entry must be resolvable through
        resolve_required_sources without raising, using minimal inputs
        appropriate to its own declared SourceKind - proves the dispatcher
        in resolve_required_sources actually routes every registered ID."""
        for canonical_id, spec in SOURCE_VOCABULARY.items():
            with self.subTest(canonical_id=canonical_id):
                if spec.kind is SourceKind.PLAN_SCOPE:
                    res = resolve_required_sources(canonical_id, _task(), _ctx(), enforcing=False)
                elif spec.kind is SourceKind.STRUCTURAL_DEPENDENCY:
                    res = resolve_required_sources(
                        canonical_id, _task(dependencies=("dep-1",)), _ctx(), enforcing=False,
                    )
                elif spec.kind is SourceKind.ASSIGNMENT_PRODUCED:
                    res = resolve_required_sources(
                        canonical_id, _task(dependencies=("dep-1",)), _ctx(), enforcing=False,
                    )
                else:  # pragma: no cover - guards against a future SourceKind with no branch here
                    self.fail(f"unhandled SourceKind for {canonical_id}: {spec.kind}")
                self.assertIsInstance(res.availability, SourceAvailability)

    def test_original_locators_is_absent(self):
        """Regression guard: original_locators must never reappear as an
        independent canonical ID - its locator requirement now lives inside
        source_fact_cards' own material validator (see SourceFactCard
        LocatorContractTest below)."""
        self.assertNotIn("original_locators", SOURCE_VOCABULARY)

    def test_unknown_canonical_id_raises_not_silently_resolves(self):
        with self.assertRaises(UnknownSourceError):
            resolve_required_sources("totally_unregistered_id", _task(), _ctx(), enforcing=False)


# ---------------------------------------------------------------------------
# 2. Family contract migration - loads the REAL agents/families/*.json files
# ---------------------------------------------------------------------------

class FamilyContractMigrationTest(unittest.TestCase):
    def test_all_ten_expected_families_are_present(self):
        actual = {p.stem for p in FAMILIES_DIR.glob("*.json")}
        self.assertEqual(EXPECTED_FAMILY_NAMES, actual)

    def test_every_required_source_id_is_canonical(self):
        """Membership in SOURCE_VOCABULARY is the stronger contract than a
        regex/legacy-text check: it proves the ID is not just
        shaped like a canonical ID but is an actually-registered,
        resolvable source."""
        for name in sorted(EXPECTED_FAMILY_NAMES):
            data = _load_family(name)
            for sid in data.get("required_sources") or []:
                with self.subTest(family=name, source_id=sid):
                    self.assertIn(sid, SOURCE_VOCABULARY)

    def test_every_produces_source_id_is_canonical(self):
        for name in sorted(EXPECTED_FAMILY_NAMES):
            data = _load_family(name)
            for sid in data.get("produces_sources") or []:
                with self.subTest(family=name, source_id=sid):
                    self.assertIn(sid, SOURCE_VOCABULARY)

    def test_zero_legacy_free_text_required_sources_remain(self):
        for name in sorted(EXPECTED_FAMILY_NAMES):
            data = _load_family(name)
            for key in ("required_sources", "produces_sources"):
                for sid in data.get(key) or []:
                    with self.subTest(family=name, field=key, source_id=sid):
                        self.assertNotIn(" ", sid)
                        self.assertEqual(sid, sid.lower())

    def test_no_dead_canonical_ids_remain_in_vocabulary(self):
        used: set[str] = set()
        for name in sorted(EXPECTED_FAMILY_NAMES):
            data = _load_family(name)
            used.update(data.get("required_sources") or [])
            used.update(data.get("produces_sources") or [])
        dead = set(SOURCE_VOCABULARY) - used
        self.assertEqual(set(), dead, f"unreferenced canonical IDs: {dead}")

    def test_expected_produces_sources_by_family(self):
        expected = {
            "jounin-review": {"review_evidence"},
            "python-implementation": {"implementation_diff", "test_evidence"},
            "python-review": {"review_evidence"},
            "source-extraction": {"source_fact_cards"},
        }
        for name in sorted(EXPECTED_FAMILY_NAMES):
            with self.subTest(family=name):
                actual = set(_load_family(name).get("produces_sources") or [])
                self.assertEqual(expected.get(name, set()), actual)


# ---------------------------------------------------------------------------
# 3. Plan-scope sources
# ---------------------------------------------------------------------------

class PlanScopeSourceTest(unittest.TestCase):
    def test_acceptance_criteria_present_is_available(self):
        res = resolve_required_sources(
            "acceptance_criteria", _task(), _ctx(plan_acceptance_criteria=("must pass tests",)),
            enforcing=False,
        )
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)

    def test_acceptance_criteria_absent_is_missing(self):
        res = resolve_required_sources(
            "acceptance_criteria", _task(), _ctx(plan_acceptance_criteria=()), enforcing=False,
        )
        self.assertEqual(SourceAvailability.MISSING, res.availability)

    def test_task_input_source_authorized_and_present_is_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs").mkdir()
            (root / "docs" / "style.md").write_text("rules", encoding="utf-8")
            res = resolve_required_sources(
                "python_coding_rules", _task(inputs=("docs/style.md",)),
                _ctx(repo_root=root), enforcing=False,
            )
            self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
            self.assertIn("docs/style.md", res.materialization["input_locators"])

    def test_task_input_source_missing_on_disk_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            res = resolve_required_sources(
                "python_coding_rules", _task(inputs=("docs/does_not_exist.md",)),
                _ctx(repo_root=root), enforcing=False,
            )
            self.assertEqual(SourceAvailability.MISSING, res.availability)

    def test_task_input_source_private_path_is_unauthorized(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "private-library").mkdir()
            (root / "private-library" / "secret.md").write_text("nope", encoding="utf-8")
            res = resolve_required_sources(
                "python_coding_rules", _task(inputs=("private-library/secret.md",)),
                _ctx(repo_root=root), enforcing=False,
            )
            self.assertEqual(SourceAvailability.UNAUTHORIZED, res.availability)

    def test_task_input_source_path_traversal_outside_root_is_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            res = resolve_required_sources(
                "python_coding_rules", _task(inputs=("../escape.md",)),
                _ctx(repo_root=root), enforcing=False,
            )
            self.assertNotEqual(SourceAvailability.AVAILABLE, res.availability)

    def test_repository_state_current_is_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_git_repo(root)
            pack = acquire_repo_evidence(root, Authorization(authorized_by="t", authorization_note="t"))
            res = resolve_required_sources(
                "repository_state", _task(), _ctx(repo_root=root, repo_evidence_pack=pack), enforcing=False,
            )
            self.assertEqual(SourceAvailability.AVAILABLE, res.availability)

    def test_repository_state_stale_is_not_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.py").write_text("VALUE = 1\n", encoding="utf-8")
            _init_git_repo(root)
            pack = acquire_repo_evidence(root, Authorization(authorized_by="t", authorization_note="t"))
            (root / "a.py").write_text("VALUE = 2\n", encoding="utf-8")  # dirty, no new commit
            res = resolve_required_sources(
                "repository_state", _task(), _ctx(repo_root=root, repo_evidence_pack=pack), enforcing=False,
            )
            self.assertEqual(SourceAvailability.MISSING, res.availability)
            self.assertEqual("repository_evidence_stale", res.reason)

    def test_failure_logs_gitkeep_only_is_missing(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".gitkeep").write_text("", encoding="utf-8")
            res = resolve_required_sources("failure_logs", _task(), _ctx(failure_log_dir=root), enforcing=False)
            self.assertEqual(SourceAvailability.MISSING, res.availability)

    def test_failure_logs_with_real_entry_is_available(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "incident-001.md").write_text("failure notes", encoding="utf-8")
            res = resolve_required_sources("failure_logs", _task(), _ctx(failure_log_dir=root), enforcing=False)
            self.assertEqual(SourceAvailability.AVAILABLE, res.availability)


# ---------------------------------------------------------------------------
# 4. PENDING_PRODUCER lifecycle (structural_dependency and assignment_produced)
# ---------------------------------------------------------------------------

class PendingProducerLifecycleTest(unittest.TestCase):
    def test_scheduled_producer_not_yet_run_is_pending_at_planning(self):
        contracts = {"python-implementation": {"produces_sources": ["implementation_diff"]}}
        ctx = _ctx(family_contracts=contracts, task_family_by_id={"impl-1": "python-implementation"})
        res = resolve_required_sources(
            "implementation_diff", _task(dependencies=("impl-1",)), ctx, enforcing=False,
        )
        self.assertEqual(SourceAvailability.PENDING_PRODUCER, res.availability)
        self.assertEqual(("impl-1",), res.producer_task_ids)

    def test_same_scheduled_producer_is_missing_not_pending_at_enforcement(self):
        """PENDING_PRODUCER must never reach the executor's pre-invocation
        gate - enforcing collapses the same unresolved state to MISSING so
        the provider is not invoked."""
        contracts = {"python-implementation": {"produces_sources": ["implementation_diff"]}}
        ctx = _ctx(family_contracts=contracts, task_family_by_id={"impl-1": "python-implementation"})
        res = resolve_required_sources(
            "implementation_diff", _task(dependencies=("impl-1",)), ctx, enforcing=True,
        )
        self.assertEqual(SourceAvailability.MISSING, res.availability)
        self.assertNotEqual(SourceAvailability.PENDING_PRODUCER, res.availability)

    def test_structural_dependency_pending_then_missing_at_enforcement(self):
        ctx = _ctx(task_family_by_id={"impl-1": "python-implementation"})
        planning = resolve_required_sources(
            "dependency_evidence_bundle", _task(dependencies=("impl-1",)), ctx, enforcing=False,
        )
        enforcing = resolve_required_sources(
            "dependency_evidence_bundle", _task(dependencies=("impl-1",)), ctx, enforcing=True,
        )
        self.assertEqual(SourceAvailability.PENDING_PRODUCER, planning.availability)
        self.assertEqual(("impl-1",), planning.producer_task_ids)
        self.assertEqual(SourceAvailability.MISSING, enforcing.availability)


# ---------------------------------------------------------------------------
# 5. Produced-source material contract
# ---------------------------------------------------------------------------

_MATERIAL_FOR = {
    "implementation_diff": {"locator": "src/app.py:10-42"},
    "test_evidence": {"command": "pytest tests/test_x.py", "result": "pass"},
    "review_evidence": {"verdict": "approved"},
    "source_fact_cards": {"fact": "Config defaults documented", "locator": "README.md:12"},
}

_PRODUCER_FAMILY = {
    "implementation_diff": "python-implementation",
    "test_evidence": "python-implementation",
    "review_evidence": "python-review",
    "source_fact_cards": "source-extraction",
}

_FULL_CONTRACTS = {
    "python-implementation": {"produces_sources": ["implementation_diff", "test_evidence"]},
    "python-review": {"produces_sources": ["review_evidence"]},
    "source-extraction": {"produces_sources": ["source_fact_cards"]},
}


class ProducedSourceMaterialTest(unittest.TestCase):
    def test_marker_only_is_missing_for_every_producible_source(self):
        for source_id in PRODUCIBLE_SOURCES:
            with self.subTest(source_id=source_id):
                family = _PRODUCER_FAMILY[source_id]
                record = _evidence("prod-1", [_marker_row(source_id)])
                ctx = _ctx(family_contracts={family: _FULL_CONTRACTS[family]},
                           task_family_by_id={"prod-1": family},
                           evidence_by_task_id={"prod-1": record})
                res = resolve_required_sources(source_id, _task(dependencies=("prod-1",)), ctx, enforcing=True)
                self.assertEqual(SourceAvailability.MISSING, res.availability)
                self.assertEqual("produced_source_evidence_missing", res.reason)

    def test_marker_plus_concrete_material_is_available_for_every_producible_source(self):
        for source_id in PRODUCIBLE_SOURCES:
            with self.subTest(source_id=source_id):
                family = _PRODUCER_FAMILY[source_id]
                rows = [_marker_row(source_id), _material_row(source_id, **_MATERIAL_FOR[source_id])]
                record = _evidence("prod-1", rows)
                ctx = _ctx(family_contracts={family: _FULL_CONTRACTS[family]},
                           task_family_by_id={"prod-1": family},
                           evidence_by_task_id={"prod-1": record})
                res = resolve_required_sources(source_id, _task(dependencies=("prod-1",)), ctx, enforcing=True)
                self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
                self.assertTrue(res.materialization.get("material"), "materialization must carry concrete rows")

    def test_material_for_undeclared_source_is_rejected(self):
        """The producer's family did not declare test_evidence, even though
        its output carries a full marker+material pair for it - the
        consumer-side resolver must still see MISSING, and the dedicated
        producer-side integrity check must flag it explicitly."""
        undeclared_contract = {"produces_sources": []}
        rows = [_marker_row("test_evidence"), _material_row("test_evidence", command="pytest", result="pass")]
        record = _evidence("prod-1", rows)

        ctx = _ctx(family_contracts={"python-implementation": undeclared_contract},
                   task_family_by_id={"prod-1": "python-implementation"},
                   evidence_by_task_id={"prod-1": record})
        res = resolve_required_sources("test_evidence", _task(dependencies=("prod-1",)), ctx, enforcing=True)
        self.assertEqual(SourceAvailability.MISSING, res.availability)
        self.assertEqual("no_declared_producer_in_dependencies", res.reason)

        undeclared = find_undeclared_produced_sources(record, undeclared_contract["produces_sources"])
        self.assertEqual(frozenset({"test_evidence"}), undeclared)

        declared = find_undeclared_produced_sources(record, _FULL_CONTRACTS["python-implementation"]["produces_sources"])
        self.assertEqual(frozenset(), declared)


# ---------------------------------------------------------------------------
# 6. source_fact_cards locator contract (replaces the old original_locators ID)
# ---------------------------------------------------------------------------

class SourceFactCardLocatorContractTest(unittest.TestCase):
    def _resolve(self, rows: list[dict[str, str]]) -> SourceAvailability:
        record = _evidence("extract-1", rows)
        ctx = _ctx(family_contracts=_FULL_CONTRACTS, task_family_by_id={"extract-1": "source-extraction"},
                   evidence_by_task_id={"extract-1": record})
        return resolve_required_sources(
            "source_fact_cards", _task(dependencies=("extract-1",)), ctx, enforcing=True,
        ).availability

    def test_fact_card_without_locator_is_missing(self):
        rows = [_marker_row("source_fact_cards"), _material_row("source_fact_cards", fact="Some fact")]
        self.assertEqual(SourceAvailability.MISSING, self._resolve(rows))

    def test_fact_card_with_locator_is_available(self):
        rows = [
            _marker_row("source_fact_cards"),
            _material_row("source_fact_cards", fact="Some fact", locator="README.md:1"),
        ]
        self.assertEqual(SourceAvailability.AVAILABLE, self._resolve(rows))


# ---------------------------------------------------------------------------
# 7. No heuristic fallback
# ---------------------------------------------------------------------------

class NoHeuristicFallbackTest(unittest.TestCase):
    def test_family_name_alone_never_grants_availability(self):
        """A completed record with NO evidence rows at all from a family
        that legitimately produces implementation_diff must still be
        MISSING - the family name/eligibility is necessary but never
        sufficient."""
        family = "python-implementation"
        record = _evidence("impl-1", [])
        ctx = _ctx(family_contracts={family: _FULL_CONTRACTS[family]},
                   task_family_by_id={"impl-1": family}, evidence_by_task_id={"impl-1": record})
        res = resolve_required_sources("implementation_diff", _task(dependencies=("impl-1",)), ctx, enforcing=True)
        self.assertEqual(SourceAvailability.MISSING, res.availability)

    def test_output_schema_prose_never_counts_as_material(self):
        """Even a completed record whose (irrelevant) prose happens to
        mention the source id must not be treated as material - only the
        exact material:<id> row shape counts."""
        rows = [{"source": "task_prompt", "observation": "This produced test_evidence for the reviewer."}]
        record = _evidence("impl-1", rows)
        self.assertFalse(evaluate_produced_source_material("test_evidence", record))
        self.assertEqual(frozenset(), extract_produced_source_ids(record))

    def test_summary_text_never_counts_as_material(self):
        record = EvidenceRecord.build(
            mission_id="m1", task_id="impl-1", provider="codex", model="provider_default",
            status="completed",
            output=json.dumps({
                "outcome": "completed", "objective_satisfied": True,
                "summary": "Implemented the feature and produced test_evidence with full coverage.",
                "diagnostic": None, "evidence": [], "review_outcome": None,
            }),
            token_usage={}, command=[], started_at=time.time(), finished_at=time.time(),
        )
        self.assertFalse(evaluate_produced_source_material("test_evidence", record))


if __name__ == "__main__":
    unittest.main()
