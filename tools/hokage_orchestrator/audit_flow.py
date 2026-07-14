"""Real supervised repository audit and patch flow for v3.5.0-RC1."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


RC_README_MARKER = "## Conversational Hokage Release Candidate"
RC_README_BLOCK = """## Conversational Hokage Release Candidate

Konoha v3.5.0 introduces a conversational Hokage product flow for supervised
missions: natural-language intake, Mission Charter approval, bounded skills,
local-model evidence, deterministic validation, exact patch approval,
controlled apply, tests, human review, Teachback, closure and private memory.

Model output is evidence only. Memory does not authorize action. Git stage,
commit and push remain separate human approval gates.
"""

DETERMINISTIC_TESTS = (
    ("hokage_orchestrator", "tests/hokage_orchestrator"),
    ("local_model_audit", "tests/local_model_audit"),
    ("beta_runtime", "tests/beta_runtime"),
)

POST_PATCH_TESTS = (
    ("hokage_orchestrator", "tests/hokage_orchestrator"),
    ("local_model_audit", "tests/local_model_audit"),
    ("beta_runtime", "tests/beta_runtime"),
    ("konoha_cli", "tests/konoha_cli"),
    ("hokage_shell", "tests/hokage_shell"),
    ("product_experience", "tests/product_experience"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_ollama_host(value: str) -> str:
    """Normalize one explicit Ollama API origin."""

    host = value.strip().rstrip("/")
    if not host:
        host = "http://localhost:11434"
    if "://" not in host:
        host = "http://" + host
    if not host.startswith(("http://", "https://")):
        raise AuditFlowError(
            f"Unsupported Ollama host scheme: {host}"
        )
    return host


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def relative_to_mission(mission_dir: Path, path: Path) -> str:
    return path.resolve().relative_to(
        mission_dir.resolve()
    ).as_posix()


class AuditFlowError(RuntimeError):
    pass


class RealSupervisedAuditFlow:
    """Orchestrate deterministic checks, Ollama audit and approved patching."""

    def __init__(
        self,
        *,
        repo_root: Path,
        workspace_root: Path,
        mission_dir: Path,
        memory_root: Path,
        mission_id: str,
        actor: str,
        model: str,
        ollama_host: Optional[str] = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.workspace_root = workspace_root.resolve()
        self.mission_dir = mission_dir.resolve()
        self.memory_root = memory_root.resolve()
        self.mission_id = mission_id
        self.actor = actor
        self.model = model
        self.ollama_host = normalize_ollama_host(
            ollama_host
            or os.environ.get("OLLAMA_HOST", "")
            or "http://localhost:11434"
        )

        self.root = self.mission_dir / "conversation" / "audit_flow"
        self.audit_dir = self.mission_dir / "audit"
        self.deterministic_report_path = (
            self.root / "deterministic_checks.json"
        )
        self.model_grant_path = (
            self.root / "session_model_grant.json"
        )
        self.normalized_audit_path = (
            self.root / "normalized_audit.json"
        )
        self.patch_plan_path = (
            self.root / "validated_patch_plan.json"
        )
        self.patch_proposal_path = (
            self.root / "patch_proposal.json"
        )
        self.patch_apply_path = (
            self.root / "patch_apply_report.json"
        )
        self.post_patch_tests_path = (
            self.root / "post_patch_tests.json"
        )

        self.audit_tool = (
            self.repo_root
            / "tools"
            / "local_model_audit"
            / "manage_local_model_audit.py"
        )

    def _require_audit_tool(self) -> Path:
        """Validate the real audit dependency only at execution time."""

        if not self.audit_tool.is_file():
            raise AuditFlowError(
                "Local model audit tool is unavailable: "
                f"{self.audit_tool}"
            )
        return self.audit_tool

    def _preflight_ollama_model(self) -> Dict[str, Any]:
        """Verify the selected model on the exact API host used by audit."""

        url = self.ollama_host + "/api/show"
        body = json.dumps(
            {"model": self.model}
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:
                payload = json.loads(
                    response.read().decode(
                        "utf-8",
                        errors="replace",
                    )
                )
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(
                "utf-8",
                errors="replace",
            )
            raise AuditFlowError(
                "Ollama model preflight failed "
                f"at {url}: HTTP {exc.code}: {detail}"
            ) from exc
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            OSError,
        ) as exc:
            raise AuditFlowError(
                "Ollama model preflight failed "
                f"at {url}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise AuditFlowError(
                "Ollama /api/show returned an invalid payload."
            )
        return payload

    def _run(
        self,
        arguments: List[str],
        *,
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            arguments,
            cwd=str(self.repo_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=timeout,
        )

    def _run_test_suites(
        self,
        suites: Iterable[tuple[str, str]],
        *,
        report_type: str,
        output: Path,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        started = utc_now()

        for name, directory in suites:
            path = self.repo_root / directory
            if not path.is_dir():
                results.append(
                    {
                        "name": name,
                        "directory": directory,
                        "status": "skipped",
                        "reason": "suite directory does not exist",
                    }
                )
                continue

            command = [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                directory,
                "-p",
                "test_*.py",
            ]
            completed = self._run(command, timeout=600)
            results.append(
                {
                    "name": name,
                    "directory": directory,
                    "command": command,
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout[-20000:],
                    "stderr": completed.stderr[-20000:],
                    "status": (
                        "passed"
                        if completed.returncode == 0
                        else "failed"
                    ),
                }
            )

        failures = [
            item for item in results
            if item.get("status") == "failed"
        ]
        payload = {
            "schema_version": "1.0.0",
            "report_type": report_type,
            "mission_id": self.mission_id,
            "started_at": started,
            "completed_at": utc_now(),
            "status": "passed" if not failures else "failed",
            "results": results,
            "failure_count": len(failures),
            "authority": {
                "test_results_are_evidence_only": True,
                "passing_tests_do_not_authorize_model_or_patch": True,
            },
        }
        write_json(output, payload)

        if failures:
            names = ", ".join(
                item["name"] for item in failures
            )
            raise AuditFlowError(
                f"Deterministic test suites failed: {names}"
            )
        return payload

    def run_deterministic_checks(self) -> Dict[str, Any]:
        return self._run_test_suites(
            DETERMINISTIC_TESTS,
            report_type="conversational_deterministic_audit_checks",
            output=self.deterministic_report_path,
        )

    def _grant_material(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "action_id": action["action_id"],
            "arguments_hash": action["arguments_hash"],
            "provider": "ollama",
            "model": self.model,
            "host": self.ollama_host,
            "scope": "one_repo_audit_invocation",
        }

    def build_model_grant(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        existing = (
            read_json(self.model_grant_path)
            if self.model_grant_path.exists()
            else None
        )
        material = self._grant_material(action)
        digest = sha256_text(canonical_json(material))[:10]
        grant_id = f"session-model-{digest}"

        if existing is not None:
            if existing.get("material_sha256") != sha256_text(
                canonical_json(material)
            ):
                raise AuditFlowError(
                    "Existing model grant does not match the pending action."
                )
            return existing

        grant = {
            "schema_version": "1.0.0",
            "report_type": "conversational_session_model_grant",
            "grant_id": grant_id,
            "mission_id": self.mission_id,
            "created_at": utc_now(),
            "provider": "ollama",
            "model": self.model,
            "host": self.ollama_host,
            "scope": "one_repo_audit_invocation",
            "action_id": action["action_id"],
            "arguments_hash": action["arguments_hash"],
            "material_sha256": sha256_text(canonical_json(material)),
            "status": "proposed",
            "approval_phrase": (
                f"APROBAR SESION-MODELO-{digest.upper()}"
            ),
            "authority": {
                "grant_is_not_permission_until_exact_approval": True,
                "grant_is_single_use": True,
                "grant_does_not_authorize_download": True,
                "grant_does_not_authorize_external_network": True,
                "model_output_is_evidence_only": True,
            },
        }
        write_json(self.model_grant_path, grant)
        return grant

    def approve_model_grant(
        self,
        *,
        action: Dict[str, Any],
        phrase: str,
    ) -> Dict[str, Any]:
        grant = self.build_model_grant(action)
        if phrase.strip() != grant["approval_phrase"]:
            raise AuditFlowError(
                "Model session approval phrase mismatch."
            )
        if grant["status"] not in {"proposed", "approved"}:
            raise AuditFlowError(
                f"Model grant status is {grant['status']}."
            )
        if action["arguments_hash"] != grant["arguments_hash"]:
            raise AuditFlowError(
                "Model grant was invalidated by changed arguments."
            )

        grant["status"] = "approved"
        grant["approved_at"] = utc_now()
        grant["approved_by"] = self.actor
        write_json(self.model_grant_path, grant)
        return grant

    def _invoke_audit_tool(
        self,
        *,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        self._require_audit_tool()
        self._preflight_ollama_model()
        grant = read_json(self.model_grant_path)
        if grant.get("status") != "approved":
            raise AuditFlowError(
                "Approved single-use model grant is required."
            )
        if grant.get("action_id") != action["action_id"]:
            raise AuditFlowError(
                "Model grant action_id mismatch."
            )

        audit_id = f"{self.mission_id}-ollama-audit"
        command = [
            sys.executable,
            str(self.audit_tool),
            "audit-repo",
            "--repo-root",
            str(self.repo_root),
            "--audit-id",
            audit_id,
            "--model",
            self.model,
            "--output-dir",
            str(self.audit_dir),
            "--use-ollama",
            "--allow-localhost",
            "--ollama-host",
            self.ollama_host,
            "--timeout-seconds",
            "600",
            "--file-limit",
            "500",
            "--confirm-audit",
            "--approval-token",
            "RUN_LOCAL_MODEL_AUDIT",
            "--force",
            "--json",
        ]
        completed = self._run(command, timeout=720)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AuditFlowError(
                "Local model audit returned non-JSON output: "
                + completed.stdout[-3000:]
                + " stderr="
                + completed.stderr[-3000:]
            ) from exc

        if completed.returncode != 0:
            raise AuditFlowError(
                "Local model audit failed: "
                + "; ".join(result.get("blockers", []))
            )
        if result.get("status") != "passed":
            raise AuditFlowError(
                f"Local model audit status={result.get('status')}"
            )

        grant["status"] = "consumed"
        grant["consumed_at"] = utc_now()
        grant["audit_id"] = audit_id
        write_json(self.model_grant_path, grant)
        return result

    def _underlying_outputs(
        self,
        result: Dict[str, Any],
    ) -> tuple[Path, Path]:
        paths = [Path(item) for item in result.get("output_paths", [])]
        audit_paths = [
            path for path in paths
            if path.name.endswith("_repo_consistency_audit.json")
        ]
        plan_paths = [
            path for path in paths
            if path.name.endswith("_repo_patch_plan.json")
        ]
        if len(audit_paths) != 1 or len(plan_paths) != 1:
            raise AuditFlowError(
                "Expected one audit JSON and one patch-plan JSON."
            )
        return audit_paths[0], plan_paths[0]

    def _rc_issue_and_operation(
        self,
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        readme = self.repo_root / "README.md"
        text = readme.read_text(encoding="utf-8")
        if RC_README_MARKER in text:
            return None, None

        issue = {
            "id": "readme_missing_conversational_rc",
            "severity": "medium",
            "source": "deterministic_rc_guard",
            "evidence": (
                "README.md does not contain the v3.5.0 conversational "
                "release-candidate marker."
            ),
            "suggested_change": (
                "Append the bounded Conversational Hokage RC section."
            ),
            "validation_status": "validated_by_exact_marker_absence",
            "deterministic_marker": RC_README_MARKER,
        }
        operation = {
            "operation": "append_once",
            "path": "README.md",
            "marker": RC_README_MARKER,
            "content": RC_README_BLOCK,
        }
        return issue, operation

    def _dedupe_issues(
        self,
        issues: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        seen = set()
        for issue in issues:
            identifier = str(
                issue.get("id")
                or issue.get("evidence")
                or canonical_json(issue)
            )
            if identifier in seen:
                continue
            seen.add(identifier)
            result.append(dict(issue))
        return result

    def _dedupe_operations(
        self,
        operations: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        seen = set()
        for operation in operations:
            key = (
                operation.get("operation"),
                operation.get("path"),
                operation.get("marker"),
            )
            if key in seen:
                continue
            seen.add(key)
            result.append(dict(operation))
        return result

    def _patch_preview(
        self,
        operations: List[Dict[str, Any]],
    ) -> str:
        previews: List[str] = []
        by_path: Dict[str, List[Dict[str, Any]]] = {}
        for operation in operations:
            by_path.setdefault(
                str(operation["path"]),
                [],
            ).append(operation)

        for relative, path_operations in sorted(by_path.items()):
            path = self.repo_root / relative
            before = (
                path.read_text(encoding="utf-8")
                if path.exists()
                else ""
            )
            after = before
            for operation in path_operations:
                if operation.get("operation") != "append_once":
                    continue
                marker = str(operation["marker"])
                if marker in after:
                    continue
                if after and not after.endswith("\n"):
                    after += "\n"
                after += "\n" + str(operation["content"]).strip() + "\n"

            diff = difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
            )
            previews.extend(diff)

        return "".join(previews)

    def run_model_audit(
        self,
        *,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not self.deterministic_report_path.exists():
            raise AuditFlowError(
                "Deterministic checks must run before Ollama."
            )
        deterministic = read_json(
            self.deterministic_report_path
        )
        if deterministic.get("status") != "passed":
            raise AuditFlowError(
                "Deterministic checks did not pass."
            )

        result = self._invoke_audit_tool(action=action)
        audit_path, underlying_plan_path = self._underlying_outputs(
            result
        )
        audit = read_json(audit_path)
        underlying_plan = read_json(underlying_plan_path)

        model_suggested = [
            dict(item)
            for item in audit.get("model_suggested_issues", [])
            if isinstance(item, dict)
        ]
        validated = [
            dict(item)
            for item in audit.get("validated_issues", [])
            if isinstance(item, dict)
        ]
        suppressed = [
            dict(item)
            for item in audit.get("suppressed_issues", [])
            if isinstance(item, dict)
        ]

        rc_issue, rc_operation = self._rc_issue_and_operation()
        if rc_issue is not None:
            validated.append(rc_issue)

        operations = [
            dict(item)
            for item in underlying_plan.get("operations", [])
            if isinstance(item, dict)
        ]
        if rc_operation is not None:
            operations.append(rc_operation)

        validated = self._dedupe_issues(validated)
        suppressed = self._dedupe_issues(suppressed)
        operations = self._dedupe_operations(operations)

        normalized = {
            "schema_version": "1.0.0",
            "report_type": "conversational_real_repo_audit",
            "mission_id": self.mission_id,
            "generated_at": utc_now(),
            "status": "passed",
            "status_code": "REAL_LOCAL_MODEL_AUDIT_COMPLETED",
            "provider": audit.get("provider"),
            "model": audit.get("model"),
            "usage": audit.get("usage", {}),
            "deterministic_checks": relative_to_mission(
                self.mission_dir,
                self.deterministic_report_path,
            ),
            "underlying_audit": relative_to_mission(
                self.mission_dir,
                audit_path,
            ),
            "model_suggested_issues": model_suggested,
            "validated_issues": validated,
            "suppressed_issues": suppressed,
            "operation_count": len(operations),
            "authority": {
                "model_output_is_evidence_only": True,
                "validated_issues_require_deterministic_evidence": True,
                "suppressed_issues_are_not_actionable": True,
                "audit_does_not_authorize_patch": True,
            },
        }
        write_json(self.normalized_audit_path, normalized)

        patch_plan = {
            "schema_version": "1.0.0",
            "report_type": "local_repo_patch_plan",
            "generated_at": utc_now(),
            "mission_id": self.mission_id,
            "authority": {
                "patch_plan_is_not_permission": True,
                "apply_requires_separate_approval": True,
                "patch_plan_uses_validated_issues_only": True,
                "git_operations_are_not_authorized": True,
            },
            "summary": (
                "Validated documentation patch generated from deterministic "
                "evidence plus local-model audit evidence."
            ),
            "issues_considered": validated,
            "operations": operations,
            "recommended_commit_message": (
                "Document Conversational Hokage release candidate"
            ),
            "requires_approval_token": "APPLY_LOCAL_MODEL_DOC_PATCH",
        }
        write_json(self.patch_plan_path, patch_plan)

        preview = self._patch_preview(operations)
        material = {
            "mission_id": self.mission_id,
            "operations": operations,
            "preview": preview,
        }
        digest = sha256_text(canonical_json(material))
        proposal = {
            "schema_version": "1.0.0",
            "report_type": "conversational_patch_proposal",
            "patch_id": f"patch-{digest[:10]}",
            "mission_id": self.mission_id,
            "created_at": utc_now(),
            "status": "proposed" if operations else "not_required",
            "operation_count": len(operations),
            "changed_paths": sorted(
                {
                    str(item["path"])
                    for item in operations
                }
            ),
            "patch_plan": relative_to_mission(
                self.mission_dir,
                self.patch_plan_path,
            ),
            "patch_preview": preview,
            "patch_sha256": digest,
            "approval_phrase": (
                f"APROBAR PATCH-{digest[:10].upper()}"
                if operations
                else None
            ),
            "rejection_phrase": (
                f"RECHAZAR PATCH-{digest[:10].upper()}"
                if operations
                else None
            ),
            "authority": {
                "proposal_is_not_permission": True,
                "approval_is_bound_to_patch_sha256": True,
                "arguments_change_invalidates_approval": True,
                "git_operations_are_not_authorized": True,
            },
        }
        write_json(self.patch_proposal_path, proposal)

        return {
            "status": "passed",
            "status_code": "AUDIT_AND_PATCH_PROPOSAL_READY",
            "audit": normalized,
            "patch_proposal": proposal,
            "output_paths": [
                str(self.normalized_audit_path),
                str(self.patch_proposal_path),
            ],
        }

    def load_patch_proposal(self) -> Optional[Dict[str, Any]]:
        if not self.patch_proposal_path.exists():
            return None
        return read_json(self.patch_proposal_path)

    def apply_patch(
        self,
        *,
        phrase: str,
    ) -> Dict[str, Any]:
        self._require_audit_tool()
        proposal = self.load_patch_proposal()
        if proposal is None:
            raise AuditFlowError("Patch proposal is missing.")
        if proposal.get("status") != "proposed":
            raise AuditFlowError(
                f"Patch proposal status={proposal.get('status')}"
            )
        if phrase.strip() != proposal["approval_phrase"]:
            raise AuditFlowError(
                "Patch approval phrase mismatch."
            )

        plan = read_json(self.patch_plan_path)
        preview = self._patch_preview(plan.get("operations", []))
        material = {
            "mission_id": self.mission_id,
            "operations": plan.get("operations", []),
            "preview": preview,
        }
        current_hash = sha256_text(canonical_json(material))
        if current_hash != proposal["patch_sha256"]:
            raise AuditFlowError(
                "Patch changed after approval proposal."
            )

        command = [
            sys.executable,
            str(self.audit_tool),
            "apply-doc-patch",
            "--repo-root",
            str(self.repo_root),
            "--patch-plan",
            str(self.patch_plan_path),
            "--output",
            str(self.patch_apply_path),
            "--confirm-apply",
            "--approval-token",
            "APPLY_LOCAL_MODEL_DOC_PATCH",
            "--force",
            "--json",
        ]
        completed = self._run(command, timeout=180)
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise AuditFlowError(
                "Patch tool returned non-JSON output: "
                + completed.stdout[-3000:]
            ) from exc

        if completed.returncode != 0:
            raise AuditFlowError(
                "Patch apply failed: "
                + "; ".join(result.get("blockers", []))
            )
        if result.get("status") != "passed":
            raise AuditFlowError(
                f"Patch apply status={result.get('status')}"
            )

        report = read_json(self.patch_apply_path)
        allowed = {
            str(item)
            for item in proposal.get("changed_paths", [])
        }
        changed = {
            str(item)
            for item in report.get("changed_paths", [])
        }
        if not changed.issubset(allowed):
            raise AuditFlowError(
                "Patch changed paths outside the approved proposal."
            )

        proposal["status"] = "applied"
        proposal["applied_at"] = utc_now()
        proposal["applied_by"] = self.actor
        proposal["apply_report"] = relative_to_mission(
            self.mission_dir,
            self.patch_apply_path,
        )
        write_json(self.patch_proposal_path, proposal)

        return {
            "status": "passed",
            "status_code": "VALIDATED_PATCH_APPLIED",
            "changed_paths": sorted(changed),
            "output_paths": [str(self.patch_apply_path)],
            "authority": {
                "patch_result_is_evidence_only": True,
                "patch_does_not_authorize_git": True,
                "tests_are_required_after_apply": True,
            },
        }

    def reject_patch(
        self,
        *,
        phrase: str,
    ) -> Dict[str, Any]:
        proposal = self.load_patch_proposal()
        if proposal is None:
            raise AuditFlowError("Patch proposal is missing.")
        if phrase.strip() != proposal.get("rejection_phrase"):
            raise AuditFlowError(
                "Patch rejection phrase mismatch."
            )
        proposal["status"] = "rejected"
        proposal["rejected_at"] = utc_now()
        proposal["rejected_by"] = self.actor
        write_json(self.patch_proposal_path, proposal)
        return {
            "status": "passed",
            "status_code": "PATCH_REJECTED",
            "output_paths": [str(self.patch_proposal_path)],
        }

    def run_post_patch_tests(self) -> Dict[str, Any]:
        return self._run_test_suites(
            POST_PATCH_TESTS,
            report_type="conversational_post_patch_validation",
            output=self.post_patch_tests_path,
        )

    def write_private_memory_note(self) -> Optional[Path]:
        if not self.normalized_audit_path.exists():
            return None
        audit = read_json(self.normalized_audit_path)
        proposal = self.load_patch_proposal() or {}
        tests = (
            read_json(self.post_patch_tests_path)
            if self.post_patch_tests_path.exists()
            else {}
        )
        usage = audit.get("usage", {})

        path = (
            self.memory_root
            / "30-model-audits"
            / f"{self.mission_id}_local_model_audit.md"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "---",
            "type: konoha_local_model_audit",
            f"mission_id: {self.mission_id}",
            f"created_at: {utc_now()}",
            f"provider: {audit.get('provider')}",
            f"model: {audit.get('model')}",
            "---",
            "",
            "# Local model audit",
            "",
            "## Authority",
            "",
            "- Model output is evidence only.",
            "- Memory does not authorize action.",
            "- Git operations require separate approval.",
            "",
            "## Usage",
            "",
            f"- input_tokens: `{usage.get('input_tokens')}`",
            f"- output_tokens: `{usage.get('output_tokens')}`",
            f"- total_duration: `{usage.get('total_duration')}`",
            "",
            "## Findings",
            "",
            (
                "- model_suggested_issues: "
                f"`{len(audit.get('model_suggested_issues', []))}`"
            ),
            (
                "- validated_issues: "
                f"`{len(audit.get('validated_issues', []))}`"
            ),
            (
                "- suppressed_issues: "
                f"`{len(audit.get('suppressed_issues', []))}`"
            ),
            "",
            "## Patch",
            "",
            f"- status: `{proposal.get('status')}`",
            f"- patch_sha256: `{proposal.get('patch_sha256')}`",
            (
                "- changed_paths: `"
                + ", ".join(proposal.get("changed_paths", []))
                + "`"
            ),
            "",
            "## Post-patch tests",
            "",
            f"- status: `{tests.get('status')}`",
            f"- failure_count: `{tests.get('failure_count')}`",
            "",
        ]
        path.write_text(
            "\n".join(lines),
            encoding="utf-8",
            newline="\n",
        )
        return path
