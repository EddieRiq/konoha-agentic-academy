"""Focused contract tests for tools/konoha_v4/required_sources.py (v4.2.0
Gate B) - exercises the real, currently-written resolver and the real
agents/families/*.json files, never a mock or a re-derived copy.

No network, no model invocation, no writes outside tempfile.TemporaryDirectory,
no private/ignored-path inspection, no sleeps, no background processes, no
dependency installation.

The failure_logs tests (Gate C2A) use mock.patch only as a spy/hook around the
real filesystem calls (os.open/os.read/os.listdir and the module's own
_bounded_file_text) to observe or interleave a concurrent change; every read
still goes through the real code and real temporary files. They are
POSIX/Linux-oriented (dir_fd, O_NOFOLLOW, FIFOs).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from tools.konoha_v4 import required_sources as rs
from tools.konoha_v4.models import AgentAssignment, EvidenceRecord
from tools.konoha_v4.required_sources import (
    MAX_MATERIAL_FILE_BYTES,
    MAX_MATERIAL_LIST_ITEMS,
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

    # failure_logs is covered exhaustively by the FailureLogs* classes below
    # (Gate C2A): it now requires repo_root plus the canonical
    # repo_root/memory/failures directory and delivers bounded text.


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


# ---------------------------------------------------------------------------
# 8. failure_logs (Gate C2A) - bounded material, canonical location,
#    descriptor-relative reads, selected-set atomicity
# ---------------------------------------------------------------------------

class _FailureLogsTestBase(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.base = Path(td.name).resolve()
        self.root = self.base / "repo"
        self.failures = self.root / "memory" / "failures"
        self.failures.mkdir(parents=True)

    def write(self, name: str, data="log line\n", directory: Path | None = None) -> Path:
        target = (directory or self.failures) / name
        target.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
        return target

    def resolve(self, **overrides):
        base = dict(repo_root=self.root, failure_log_dir=self.failures)
        base.update(overrides)
        return resolve_required_sources("failure_logs", _task(), _ctx(**base), enforcing=True)

    def collection(self, res) -> dict:
        return res.materialization["failure_logs"]

    def paths(self, res) -> list[str]:
        return [item["path"] for item in self.collection(res)["items"]]

    def assertMissing(self, res, reason: str) -> None:
        self.assertEqual(SourceAvailability.MISSING, res.availability)
        self.assertEqual(reason, res.reason)
        self.assertIsNone(res.materialization)

    def before_each_read(self, action):
        """Patch the module's _bounded_file_text so action(call_number, name)
        runs immediately before each real read - deterministically
        interleaves a concurrent filesystem change after selection."""
        real = rs._bounded_file_text
        calls: list[str] = []

        def wrapper(path, **kwargs):
            calls.append(path)
            action(len(calls), path)
            return real(path, **kwargs)

        return mock.patch.object(rs, "_bounded_file_text", wrapper), calls


class FailureLogsDirectoryBoundaryTest(_FailureLogsTestBase):
    def test_missing_repo_root(self):
        self.write("real.log")
        self.assertMissing(self.resolve(repo_root=None), "repo_root_unavailable_for_failure_log_check")

    def test_missing_failure_log_dir(self):
        self.write("real.log")
        self.assertMissing(self.resolve(failure_log_dir=None), "failure_log_directory_absent")

    def test_nonexistent_directory(self):
        self.assertMissing(
            self.resolve(failure_log_dir=self.root / "memory" / "nope"), "failure_log_directory_absent",
        )

    def test_failure_log_dir_is_a_file(self):
        afile = self.write("afile", directory=self.base)
        self.assertMissing(self.resolve(failure_log_dir=afile), "failure_log_directory_absent")

    def _assert_not_canonical(self, res) -> None:
        self.assertEqual(SourceAvailability.UNAUTHORIZED, res.availability)
        self.assertEqual("failure_log_directory_not_canonical", res.reason)
        self.assertIsNone(res.materialization)

    def test_outside_repo_directory_refused(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.write("real.log", "OUTSIDE", directory=outside)
        self._assert_not_canonical(self.resolve(failure_log_dir=outside))

    def test_repo_root_itself_refused(self):
        self.write("real.log", "ROOT", directory=self.root)
        self._assert_not_canonical(self.resolve(failure_log_dir=self.root))

    def test_interior_noncanonical_directory_refused(self):
        for parts in (("other", "failures"), ("memory", "other"), ("failures",), ("memory",)):
            with self.subTest(parts=parts):
                directory = self.root.joinpath(*parts)
                directory.mkdir(parents=True, exist_ok=True)
                self.write("real.log", "INTERIOR", directory=directory)
                self._assert_not_canonical(self.resolve(failure_log_dir=directory))

    def test_canonical_directory_accepted(self):
        self.write("real.log", "hello\n")
        res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        self.assertEqual(["memory/failures/real.log"], self.paths(res))

    def test_canonical_directory_that_is_symlink_to_other_interior_directory_refused(self):
        self.failures.rmdir()
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.write("real.log", "ELSEWHERE", directory=elsewhere)
        self.failures.symlink_to(elsewhere, target_is_directory=True)
        self._assert_not_canonical(self.resolve())

    def test_symlink_alias_pointing_at_canonical_directory_refused(self):
        self.write("real.log")
        alias = self.root / "alias"
        alias.symlink_to(self.failures, target_is_directory=True)
        self._assert_not_canonical(self.resolve(failure_log_dir=alias))

    def test_symlinked_memory_parent_refused(self):
        real_memory = self.root / "real_memory"
        os.rename(self.root / "memory", real_memory)
        self.write("real.log", "VIA_SYMLINK", directory=real_memory / "failures")
        (self.root / "memory").symlink_to(real_memory, target_is_directory=True)
        self._assert_not_canonical(self.resolve())


class FailureLogsSelectionTest(_FailureLogsTestBase):
    def test_empty_directory_is_missing(self):
        self.assertMissing(self.resolve(), "failure_log_directory_empty")

    def test_dotfiles_and_gitkeep_only_is_missing(self):
        self.write(".gitkeep", "")
        self.write(".hidden", "not evidence")
        self.assertMissing(self.resolve(), "failure_log_directory_empty")

    def test_normal_nonempty_log_is_available_with_bounded_concrete_text(self):
        self.write("incident-001.log", "disk full\n")
        res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        collection = self.collection(res)
        self.assertEqual(1, collection["total"])
        self.assertEqual(1, collection["included"])
        self.assertFalse(collection["truncated"])
        item = collection["items"][0]
        self.assertEqual("memory/failures/incident-001.log", item["path"])
        self.assertTrue(item["available"])
        self.assertEqual(10, item["total_bytes"])
        self.assertEqual(10, item["included_bytes"])
        self.assertFalse(item["truncated"])
        self.assertEqual("disk full\n", item["text"])

    def test_whitespace_only_nonzero_file_counts(self):
        self.write("blank.log", "\n")
        res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        self.assertEqual(1, self.collection(res)["items"][0]["included_bytes"])

    def test_zero_byte_only_directory_is_missing_empty(self):
        self.write("empty.log", "")
        self.assertMissing(self.resolve(), "failure_log_directory_empty")

    def test_zero_byte_file_does_not_count_next_to_valid_file(self):
        self.write("a-empty.log", "")
        self.write("b-real.log", "real")
        res = self.resolve()
        collection = self.collection(res)
        self.assertEqual(1, collection["total"])
        self.assertEqual(1, collection["included"])
        self.assertEqual(["memory/failures/b-real.log"], self.paths(res))

    def test_zero_byte_files_do_not_consume_list_slots(self):
        for i in range(MAX_MATERIAL_LIST_ITEMS):
            self.write(f"a-empty-{i:02d}.log", "")
        self.write("z-real.log", "real")
        res = self.resolve()
        self.assertEqual(["memory/failures/z-real.log"], self.paths(res))
        self.assertEqual(1, self.collection(res)["total"])

    def test_oversized_file_truncates_at_limit(self):
        self.write("big.log", "a" * (MAX_MATERIAL_FILE_BYTES + 1000))
        item = self.collection(self.resolve())["items"][0]
        self.assertTrue(item["truncated"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES + 1000, item["total_bytes"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, item["included_bytes"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, len(item["text"]))

    def test_one_byte_over_limit_is_truncated(self):
        self.write("big.log", "a" * (MAX_MATERIAL_FILE_BYTES + 1))
        item = self.collection(self.resolve())["items"][0]
        self.assertTrue(item["truncated"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, item["included_bytes"])

    def test_exactly_at_limit_is_not_truncated(self):
        self.write("edge.log", "a" * MAX_MATERIAL_FILE_BYTES)
        item = self.collection(self.resolve())["items"][0]
        self.assertFalse(item["truncated"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, item["total_bytes"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, item["included_bytes"])
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, len(item["text"]))

    def test_more_than_max_items_truncates_collection_deterministically(self):
        names = [f"incident-{i:02d}.log" for i in range(MAX_MATERIAL_LIST_ITEMS + 2)]
        for name in reversed(names):
            self.write(name, f"content of {name}")
        res = self.resolve()
        collection = self.collection(res)
        self.assertEqual(MAX_MATERIAL_LIST_ITEMS + 2, collection["total"])
        self.assertEqual(MAX_MATERIAL_LIST_ITEMS, collection["included"])
        self.assertTrue(collection["truncated"])
        self.assertEqual(
            [f"memory/failures/{n}" for n in names[:MAX_MATERIAL_LIST_ITEMS]], self.paths(res),
        )

    def test_files_outside_selected_slice_are_never_opened(self):
        names = [f"incident-{i:02d}.log" for i in range(MAX_MATERIAL_LIST_ITEMS + 2)]
        for name in names:
            self.write(name, f"content of {name}")
        real_open = os.open
        opened: list[str] = []

        def spy(path, flags, *args, **kwargs):
            if kwargs.get("dir_fd") is not None:
                opened.append(path)
            return real_open(path, flags, *args, **kwargs)

        with mock.patch.object(os, "open", spy):
            res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        opened_files = [n for n in opened if n not in ("memory", "failures")]
        self.assertEqual(names[:MAX_MATERIAL_LIST_ITEMS], opened_files)

    def test_private_marker_paths_never_surface(self):
        self.write("secret-notes.log", "PRIVATE")
        self.write("token-dump.log", "PRIVATE")
        self.write("real.log", "public")
        res = self.resolve()
        self.assertEqual(["memory/failures/real.log"], self.paths(res))
        self.assertNotIn("PRIVATE", json.dumps(res.materialization))

    def test_only_private_marker_paths_is_missing(self):
        self.write("secret-notes.log", "PRIVATE")
        self.assertMissing(self.resolve(), "failure_log_directory_empty")

    def test_configured_excluded_file_never_surfaces(self):
        self.write("skip.log", "EXCLUDED")
        self.write("real.log", "public")
        res = self.resolve(excluded_paths=("memory/failures/skip.log",))
        self.assertEqual(["memory/failures/real.log"], self.paths(res))
        self.assertNotIn("EXCLUDED", json.dumps(res.materialization))

    def test_configured_excluded_directory_prefix_never_surfaces(self):
        self.write("real.log", "EXCLUDED")
        for prefix in ("memory/failures", "memory/failures/", "memory", "memory/"):
            with self.subTest(prefix=prefix):
                self.assertMissing(self.resolve(excluded_paths=(prefix,)), "failure_log_directory_empty")

    def test_similar_but_non_matching_excluded_prefix_does_not_exclude(self):
        self.write("real.log", "public")
        res = self.resolve(excluded_paths=("memory/fail", "memory/failures/real.lo"))
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)

    def test_non_basename_listing_entry_is_never_statted_or_read(self):
        self.write("outside.log", "OUTSIDE", directory=self.root / "memory")
        with mock.patch.object(os, "listdir", return_value=["../outside.log", "sub/x.log"]):
            res = self.resolve()
        self.assertMissing(res, "failure_log_directory_empty")


class FailureLogsCandidateClassificationTest(_FailureLogsTestBase):
    """Each non-regular entry must be refused as evidence: with a real
    sibling log only the real one surfaces; alone it yields MISSING."""

    def _assert_refused_entry(self) -> None:
        self.write("real.log", "REAL")
        res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        self.assertEqual(["memory/failures/real.log"], self.paths(res))
        self.assertEqual(1, self.collection(res)["total"])
        self.assertNotIn("OUTSIDE", json.dumps(res.materialization))
        (self.failures / "real.log").unlink()
        self.assertMissing(self.resolve(), "failure_log_directory_empty")

    def test_symlink_outside_repo_never_surfaced(self):
        target = self.write("outside.log", "OUTSIDE", directory=self.base)
        (self.failures / "link.log").symlink_to(target)
        self._assert_refused_entry()

    def test_symlink_to_repo_file_outside_failure_root_never_surfaced(self):
        target = self.write("other.log", "OUTSIDE", directory=self.root)
        (self.failures / "link.log").symlink_to(target)
        self._assert_refused_entry()

    def test_broken_symlink_never_surfaced(self):
        (self.failures / "link.log").symlink_to(self.root / "does-not-exist")
        self._assert_refused_entry()

    def test_sibling_symlink_alias_inside_failure_root_refused(self):
        self.write("real.log", "REAL")
        (self.failures / "alias.log").symlink_to(self.failures / "real.log")
        res = self.resolve()
        self.assertEqual(["memory/failures/real.log"], self.paths(res))
        self.assertEqual(1, self.collection(res)["total"])

    def test_symlink_to_directory_refused(self):
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        self.write("inner.log", "OUTSIDE", directory=elsewhere)
        (self.failures / "dirlink").symlink_to(elsewhere, target_is_directory=True)
        self._assert_refused_entry()

    def test_subdirectory_refused(self):
        sub = self.failures / "sub"
        sub.mkdir()
        self.write("nested.log", "OUTSIDE", directory=sub)
        self._assert_refused_entry()

    def test_fifo_refused_without_blocking(self):
        os.mkfifo(self.failures / "pipe.log")
        self._assert_refused_entry()


class FailureLogsSelectedSetAtomicityTest(_FailureLogsTestBase):
    def test_selected_file_truncated_to_zero_before_read_fails_closed(self):
        target = self.write("a.log", "had content")

        def action(call_number, name):
            target.write_bytes(b"")  # same inode, now zero bytes

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_selected_file_disappears_fails_closed(self):
        target = self.write("a.log")
        patcher, _ = self.before_each_read(lambda n, name: target.unlink())
        with patcher:
            res = self.resolve()
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_one_readable_and_one_selected_unreadable_fails_whole_source(self):
        self.write("a.log", "readable")
        second = self.write("b.log", "vanishes")

        def action(call_number, name):
            if call_number == 1:
                second.unlink()

        patcher, calls = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertEqual(["a.log", "b.log"], calls)
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_selected_file_replaced_by_symlink_fails_closed(self):
        target = self.write("a.log", "original")
        decoy = self.write("decoy.txt", "OUTSIDE", directory=self.base)

        def action(call_number, name):
            target.unlink()
            target.symlink_to(decoy)

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_selected_file_replaced_by_another_regular_inode_fails_closed(self):
        target = self.write("a.log", "original")

        def action(call_number, name):
            # Create the replacement while the original still exists so the
            # two inode numbers cannot coincide, then swap it in atomically.
            replacement = self.write("a.log.new", "replacement")
            os.replace(replacement, target)

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_selected_file_replaced_by_fifo_fails_closed(self):
        target = self.write("a.log", "original")

        def action(call_number, name):
            target.unlink()
            os.mkfifo(target)

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertMissing(res, "failure_log_files_unreadable")

    def test_swapping_failures_directory_for_symlink_after_selection_cannot_redirect_reads(self):
        self.write("a.log", "ORIGINAL-A")
        self.write("b.log", "ORIGINAL-B")
        decoy = self.root / "decoy"
        decoy.mkdir()
        self.write("a.log", "DECOY", directory=decoy)
        self.write("b.log", "DECOY", directory=decoy)

        def action(call_number, name):
            if call_number == 1:
                os.rename(self.failures, self.root / "memory" / "failures_moved")
                self.failures.symlink_to(decoy, target_is_directory=True)

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        self.assertEqual(["ORIGINAL-A", "ORIGINAL-B"], [i["text"] for i in self.collection(res)["items"]])
        self.assertNotIn("DECOY", json.dumps(res.materialization))

    def test_swapping_memory_parent_for_symlink_after_selection_cannot_redirect_reads(self):
        self.write("a.log", "ORIGINAL-A")
        self.write("b.log", "ORIGINAL-B")
        decoy_memory = self.root / "decoy_memory"
        (decoy_memory / "failures").mkdir(parents=True)
        self.write("a.log", "DECOY", directory=decoy_memory / "failures")
        self.write("b.log", "DECOY", directory=decoy_memory / "failures")

        def action(call_number, name):
            if call_number == 1:
                os.rename(self.root / "memory", self.root / "memory_moved")
                (self.root / "memory").symlink_to(decoy_memory, target_is_directory=True)

        patcher, _ = self.before_each_read(action)
        with patcher:
            res = self.resolve()
        self.assertEqual(SourceAvailability.AVAILABLE, res.availability)
        self.assertEqual(["ORIGINAL-A", "ORIGINAL-B"], [i["text"] for i in self.collection(res)["items"]])
        self.assertNotIn("DECOY", json.dumps(res.materialization))


class BoundedFileTextHelperTest(unittest.TestCase):
    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.base = Path(td.name).resolve()

    def _dir_fd(self, directory: Path) -> int:
        fd = os.open(str(directory), os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        return fd

    def test_reads_at_most_limit_plus_one_bytes_of_oversized_file(self):
        big = self.base / "big.log"
        big.write_bytes(b"x" * 10_000)
        real_read = os.read
        reads: list[tuple[int, int]] = []

        def spy(fd, n):
            data = real_read(fd, n)
            reads.append((n, len(data)))
            return data

        with mock.patch.object(os, "read", spy):
            info = rs._bounded_file_text(str(big), limit=100)
        self.assertLessEqual(sum(got for _, got in reads), 101)
        self.assertTrue(all(requested <= 101 for requested, _ in reads))
        self.assertTrue(info["available"])
        self.assertEqual(10_000, info["total_bytes"])
        self.assertEqual(100, info["included_bytes"])
        self.assertTrue(info["truncated"])
        self.assertEqual("x" * 100, info["text"])

    def test_exactly_at_limit_is_not_truncated(self):
        edge = self.base / "edge.log"
        edge.write_bytes(b"y" * 100)
        info = rs._bounded_file_text(str(edge), limit=100)
        self.assertFalse(info["truncated"])
        self.assertEqual(100, info["included_bytes"])
        self.assertEqual(100, info["total_bytes"])

    def test_default_limit_is_max_material_file_bytes(self):
        big = self.base / "big.log"
        big.write_bytes(b"z" * (MAX_MATERIAL_FILE_BYTES + 5))
        info = rs._bounded_file_text(str(big))
        self.assertEqual(MAX_MATERIAL_FILE_BYTES, info["included_bytes"])
        self.assertTrue(info["truncated"])

    def test_io_failure_is_unavailable_not_an_empty_valid_file(self):
        info = rs._bounded_file_text(str(self.base / "does-not-exist.log"))
        self.assertEqual(
            {"available": False, "total_bytes": None, "included_bytes": 0, "truncated": False, "text": ""},
            info,
        )

    def test_read_error_after_open_is_unavailable(self):
        target = self.base / "a.log"
        target.write_bytes(b"content")
        with mock.patch.object(os, "read", side_effect=OSError(5, "I/O error")):
            info = rs._bounded_file_text(str(target))
        self.assertFalse(info["available"])
        self.assertIsNone(info["total_bytes"])

    def test_directory_is_refused(self):
        self.assertFalse(rs._bounded_file_text(str(self.base))["available"])

    def test_leaf_symlink_is_refused(self):
        target = self.base / "target.log"
        target.write_bytes(b"content")
        link = self.base / "link.log"
        link.symlink_to(target)
        self.assertFalse(rs._bounded_file_text(str(link))["available"])

    def test_fifo_is_refused_without_blocking(self):
        fifo = self.base / "pipe.log"
        os.mkfifo(fifo)
        self.assertFalse(rs._bounded_file_text(str(fifo))["available"])

    def test_dir_fd_accepts_plain_basename_and_validates_expected_identity(self):
        directory = self.base / "failures"
        directory.mkdir()
        target = directory / "real.log"
        target.write_bytes(b"hello")
        st = os.stat(target)
        fd = self._dir_fd(directory)

        info = rs._bounded_file_text("real.log", dir_fd=fd, expected_identity=(st.st_dev, st.st_ino))
        self.assertTrue(info["available"])
        self.assertEqual("hello", info["text"])
        self.assertEqual(5, info["total_bytes"])
        self.assertEqual(5, info["included_bytes"])
        self.assertFalse(info["truncated"])

        wrong = rs._bounded_file_text("real.log", dir_fd=fd, expected_identity=(st.st_dev, st.st_ino + 1))
        self.assertFalse(wrong["available"])

    def test_dir_fd_rejects_non_basename_before_opening(self):
        directory = self.base / "failures"
        (directory / "subdir").mkdir(parents=True)
        real = directory / "real.log"
        real.write_bytes(b"hello")
        (directory / "subdir" / "real.log").write_bytes(b"nested")
        fd = self._dir_fd(directory)

        real_open = os.open
        for bad in ("", ".", "..", "../failures/real.log", "subdir/real.log", str(real)):
            with self.subTest(path=bad):
                opened: list[str] = []

                def spy(path, flags, *args, **kwargs):
                    opened.append(path)
                    return real_open(path, flags, *args, **kwargs)

                with mock.patch.object(os, "open", spy):
                    info = rs._bounded_file_text(bad, dir_fd=fd)
                self.assertFalse(info["available"])
                self.assertEqual([], opened, "a rejected path must never reach os.open")


if __name__ == "__main__":
    unittest.main()
