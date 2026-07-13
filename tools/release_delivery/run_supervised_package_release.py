#!/usr/bin/env python3
"""Compose supervised package installation, acceptance, and release closure.

This wrapper does not replace the package installation or release workflows.
It validates that both plans describe the same release and then calls the
existing tools with their existing explicit tokens.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

SCHEMA_VERSION = "1.0.0"
PLAN_REPORT_TYPE = "supervised_package_release_plan"
REPORT_TYPE = "supervised_package_release_report"
RUN_TOKEN = "RUN_SUPERVISED_PACKAGE_RELEASE"
INSTALL_TOKEN = "APPLY_SUPERVISED_PACKAGE_INSTALLATION"

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,95}$")

PRIVATE_PREFIXES = (
    ".env",
    "alliance/kirigakure",
    "memory/local",
    "vault",
    "sandbox",
)

BOUNDARIES = {
    "arbitrary_shell": "blocked",
    "package_installation": "delegated_existing_guard",
    "canonical_tests": "delegated_existing_release_workflow",
    "git_mutations": "delegated_explicit_tokens_only",
    "tag_mutations": "delegated_explicit_tokens_only",
    "release_mutations": "delegated_explicit_tokens_only",
    "network_access": "explicit_allow_network_only",
    "private_context_access": "blocked",
    "output": "sandbox_only",
}


class DeliveryError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_relative_path(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    value = raw.strip().replace("\\", "/")
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:/", value):
        return None
    while value.startswith("./"):
        value = value[2:]
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return value


def is_private_path(relative: str) -> bool:
    lowered = relative.lower()
    if lowered == ".env" or lowered.startswith(".env."):
        return True
    for prefix in PRIVATE_PREFIXES:
        if lowered == prefix or lowered.startswith(prefix + "/"):
            return True
    parts = lowered.split("/")
    return (
        len(parts) >= 3
        and parts[0] == "alliance"
        and parts[2] in {"private-library", "memory"}
    )


def resolve_repo_file(
    repo_root: Path,
    raw: Any,
    label: str,
    *,
    allow_sandbox: bool = False,
) -> Path:
    relative = normalize_relative_path(raw)
    if relative is None:
        raise DeliveryError(f"{label} must be repository-relative")
    if is_private_path(relative) and not (
        allow_sandbox and relative.startswith("sandbox/")
    ):
        raise DeliveryError(f"{label} points to blocked context")
    path = (repo_root / relative).resolve()
    if not is_relative_to(path, repo_root):
        raise DeliveryError(f"{label} escapes repository root")
    if not path.is_file():
        raise DeliveryError(f"{label} not found: {relative}")
    return path


def resolve_output(repo_root: Path, raw: str) -> Path:
    sandbox = (repo_root / "sandbox").resolve()
    output = Path(raw)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()
    if not is_relative_to(output, sandbox):
        raise DeliveryError("delivery output must stay under sandbox")
    return output


def read_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DeliveryError(f"{label} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DeliveryError(
            f"{label} invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise DeliveryError(f"{label} must be a JSON object")
    return payload


def write_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    force: bool,
) -> None:
    if path.exists() and not force:
        raise DeliveryError(f"output exists; use --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise DeliveryError(f"unable to load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def validate_plan(payload: Mapping[str, Any]) -> Dict[str, Any]:
    required = {
        "schema_version",
        "report_type",
        "delivery_id",
        "expected_base_commit",
        "target_version",
        "installation_manifest_path",
        "release_plan_path",
        "focused_suites",
        "clean_install_smoke",
        "authority",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise DeliveryError(
            "delivery plan missing fields: " + ", ".join(missing)
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        raise DeliveryError("delivery schema_version mismatch")
    if payload.get("report_type") != PLAN_REPORT_TYPE:
        raise DeliveryError("delivery report_type mismatch")

    delivery_id = payload.get("delivery_id")
    if (
        not isinstance(delivery_id, str)
        or SAFE_ID_RE.fullmatch(delivery_id) is None
    ):
        raise DeliveryError("delivery_id is invalid")

    base = payload.get("expected_base_commit")
    if (
        not isinstance(base, str)
        or COMMIT_RE.fullmatch(base) is None
    ):
        raise DeliveryError("expected_base_commit is invalid")

    version = payload.get("target_version")
    if (
        not isinstance(version, str)
        or VERSION_RE.fullmatch(version) is None
    ):
        raise DeliveryError("target_version is invalid")

    for field in (
        "installation_manifest_path",
        "release_plan_path",
    ):
        value = normalize_relative_path(payload.get(field))
        if value is None or is_private_path(value):
            raise DeliveryError(f"{field} is invalid")

    suites = payload.get("focused_suites")
    if not isinstance(suites, list) or not suites:
        raise DeliveryError("focused_suites must be non-empty")

    normalized_suites: List[Dict[str, Any]] = []
    seen = set()
    for index, raw in enumerate(suites):
        if not isinstance(raw, dict):
            raise DeliveryError(
                f"focused_suites[{index}] must be an object"
            )
        name = raw.get("name")
        path = normalize_relative_path(raw.get("path"))
        pattern = raw.get("pattern")
        expected = raw.get("expected_tests")
        if (
            not isinstance(name, str)
            or SAFE_ID_RE.fullmatch(name) is None
            or name in seen
        ):
            raise DeliveryError(
                f"focused_suites[{index}].name is invalid"
            )
        if path is None or not path.startswith("tests/"):
            raise DeliveryError(
                f"focused_suites[{index}].path is invalid"
            )
        if not isinstance(pattern, str) or not pattern:
            raise DeliveryError(
                f"focused_suites[{index}].pattern is invalid"
            )
        if not isinstance(expected, int) or expected <= 0:
            raise DeliveryError(
                f"focused_suites[{index}].expected_tests is invalid"
            )
        seen.add(name)
        normalized_suites.append(
            {
                "name": name,
                "path": path,
                "pattern": pattern,
                "expected_tests": expected,
            }
        )

    smoke = payload.get("clean_install_smoke")
    if not isinstance(smoke, dict):
        raise DeliveryError("clean_install_smoke must be an object")
    smoke_tool = normalize_relative_path(smoke.get("tool_path"))
    expected_version = smoke.get("expected_version")
    if (
        smoke_tool is None
        or is_private_path(smoke_tool)
        or not isinstance(expected_version, str)
        or expected_version != version.removeprefix("v")
    ):
        raise DeliveryError("clean_install_smoke is invalid")

    authority = payload.get("authority")
    required_authority = {
        "plan_is_not_permission": True,
        "installation_token_required": True,
        "release_tokens_required": True,
        "network_is_explicit": True,
        "tests_are_evidence_only": True,
    }
    if not isinstance(authority, dict):
        raise DeliveryError("authority must be an object")
    for key, expected in required_authority.items():
        if authority.get(key) is not expected:
            raise DeliveryError(
                f"authority requires {key}=true"
            )

    result = dict(payload)
    result["focused_suites"] = normalized_suites
    result["clean_install_smoke"] = {
        "tool_path": smoke_tool,
        "expected_version": expected_version,
    }
    return result


class DeliveryRunner:
    def __init__(
        self,
        repo_root: Path,
        plan: Mapping[str, Any],
        args: argparse.Namespace,
    ) -> None:
        self.repo_root = repo_root
        self.plan = plan
        self.args = args
        self.report_dir = (
            repo_root / "sandbox" / "reports"
        ).resolve()
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.logs: List[Dict[str, Any]] = []
        self.steps: List[Dict[str, Any]] = []

    def run(
        self,
        label: str,
        command: Sequence[str],
        *,
        timeout: int = 1200,
        expected_rcs: Sequence[int] = (0,),
    ) -> subprocess.CompletedProcess[str]:
        try:
            completed = subprocess.run(
                list(command),
                cwd=self.repo_root,
                text=True,
                capture_output=True,
                shell=False,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise DeliveryError(
                f"{label} timed out"
            ) from exc

        log = self.report_dir / (
            f"{self.plan['delivery_id']}-"
            f"{len(self.logs)+1:02d}-{label}.log"
        )
        log.write_text(
            "COMMAND\n"
            + json.dumps(list(command))
            + "\n\nSTDOUT\n"
            + completed.stdout
            + "\n\nSTDERR\n"
            + completed.stderr
            + f"\n\nRETURN_CODE\n{completed.returncode}\n",
            encoding="utf-8",
            newline="\n",
        )
        self.logs.append(
            {
                "label": label,
                "command": list(command),
                "returncode": completed.returncode,
                "log": str(log),
            }
        )

        if completed.returncode not in expected_rcs:
            raise DeliveryError(
                f"{label} failed with RC={completed.returncode}; "
                f"see {log}"
            )
        return completed

    def validate_alignment(self) -> Dict[str, Any]:
        install_path = resolve_repo_file(
            self.repo_root,
            self.plan["installation_manifest_path"],
            "installation manifest",
        )
        release_path = resolve_repo_file(
            self.repo_root,
            self.plan["release_plan_path"],
            "release plan",
        )

        install_tool = self.repo_root / (
            "tools/package_installation/"
            "run_supervised_package_installation.py"
        )
        release_tool = self.repo_root / (
            "tools/release_workflow/run_supervised_release.py"
        )
        install_module = load_module(
            "delivery_install_validator",
            install_tool,
        )
        release_module = load_module(
            "delivery_release_validator",
            release_tool,
        )

        installation = install_module.validate_manifest(
            read_json_object(install_path, "installation manifest")
        )
        release = release_module.validate_plan(
            read_json_object(release_path, "release plan")
        )

        expected_base = self.plan["expected_base_commit"]
        target = self.plan["target_version"]

        checks = {
            "installation_base": (
                installation["expected_base_commit"]
                == expected_base
            ),
            "release_base": (
                release["expected_base_commit"] == expected_base
            ),
            "release_version": (
                release["target_version"] == target
            ),
            "public_scope": (
                installation["expected_public_paths"]
                == release["public_paths"]
            ),
        }
        failed = sorted(
            key for key, passed in checks.items() if not passed
        )
        if failed:
            raise DeliveryError(
                "package/release alignment failed: "
                + ", ".join(failed)
            )

        return {
            "installation": installation,
            "release": release,
            "installation_path": install_path,
            "release_path": release_path,
            "install_tool": install_tool,
            "release_tool": release_tool,
            "checks": checks,
        }

    def run_focused_suites(self) -> List[Dict[str, Any]]:
        results = []
        for suite in self.plan["focused_suites"]:
            completed = self.run(
                f"tests-{suite['name']}",
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    suite["path"],
                    "-p",
                    suite["pattern"],
                ],
                timeout=self.args.test_timeout,
            )
            match = re.search(
                r"Ran\s+(\d+)\s+tests?",
                completed.stderr + "\n" + completed.stdout,
            )
            if match is None:
                raise DeliveryError(
                    f"unable to read test count for {suite['name']}"
                )
            actual = int(match.group(1))
            if actual != suite["expected_tests"]:
                raise DeliveryError(
                    f"{suite['name']} expected "
                    f"{suite['expected_tests']} tests, found {actual}"
                )
            results.append(
                {
                    "name": suite["name"],
                    "expected_tests": suite["expected_tests"],
                    "actual_tests": actual,
                    "passed": True,
                }
            )
        return results

    def execute(self) -> Dict[str, Any]:
        if not self.args.confirm_run:
            raise DeliveryError("--confirm-run is required")
        if self.args.delivery_token != RUN_TOKEN:
            raise DeliveryError(
                f"--delivery-token must be {RUN_TOKEN}"
            )
        if self.args.installation_token != INSTALL_TOKEN:
            raise DeliveryError(
                f"--installation-token must be {INSTALL_TOKEN}"
            )
        if not self.args.allow_network:
            raise DeliveryError("--allow-network is required")

        aligned = self.validate_alignment()
        install_report = (
            self.report_dir
            / f"{self.plan['delivery_id']}-installation.json"
        )
        smoke_report = (
            self.report_dir
            / f"{self.plan['delivery_id']}-clean-install-smoke.json"
        )
        release_report = (
            self.report_dir
            / f"{self.plan['delivery_id']}-release.json"
        )
        status_report = (
            self.report_dir
            / f"{self.plan['delivery_id']}-status.json"
        )
        pre_status_report = (
            self.report_dir
            / f"{self.plan['delivery_id']}-pre-status.json"
        )

        head_result = self.run(
            "git-head",
            ["git", "rev-parse", "HEAD"],
            timeout=60,
        )
        current_head = head_result.stdout.strip()
        expected_base = self.plan["expected_base_commit"]

        focused: List[Dict[str, Any]] = []
        installation_summary: Dict[str, Any]
        smoke_summary: Dict[str, Any]
        resume_mode = current_head != expected_base

        if not resume_mode:
            self.run(
                "package-installation",
                [
                    sys.executable,
                    "-S",
                    str(aligned["install_tool"]),
                    "--repo-root",
                    ".",
                    "--manifest",
                    str(aligned["installation_path"]),
                    "--output",
                    str(install_report),
                    "--apply",
                    "--approval-token",
                    self.args.installation_token,
                    "--force",
                    "--json",
                ],
            )
            installation = read_json_object(
                install_report,
                "installation report",
            )
            if (
                installation.get("status_code") != "INSTALLED"
                or installation.get("installed") is not True
            ):
                raise DeliveryError(
                    "package installation did not reach INSTALLED"
                )
            installation_summary = {
                "status_code": installation.get("status_code"),
                "report": str(install_report),
            }
            self.steps.append(
                {
                    "step": "package_installation",
                    "status": "passed",
                    "report": str(install_report),
                }
            )

            focused = self.run_focused_suites()
            self.steps.append(
                {
                    "step": "focused_acceptance",
                    "status": "passed",
                    "suites": focused,
                }
            )

            smoke_tool = resolve_repo_file(
                self.repo_root,
                self.plan["clean_install_smoke"]["tool_path"],
                "clean install smoke tool",
            )
            self.run(
                "clean-install-smoke",
                [
                    sys.executable,
                    "-S",
                    str(smoke_tool),
                    "--repo-root",
                    ".",
                    "--expected-version",
                    self.plan["clean_install_smoke"][
                        "expected_version"
                    ],
                    "--output",
                    str(smoke_report),
                    "--force",
                    "--json",
                ],
            )
            smoke = read_json_object(
                smoke_report,
                "clean install smoke report",
            )
            if (
                smoke.get("status_code")
                != "CLEAN_INSTALL_SMOKE_PASSED"
            ):
                raise DeliveryError(
                    "clean install smoke did not pass"
                )
            smoke_summary = {
                "status_code": smoke.get("status_code"),
                "report": str(smoke_report),
            }
            self.steps.append(
                {
                    "step": "clean_install_smoke",
                    "status": "passed",
                    "report": str(smoke_report),
                }
            )
        else:
            self.run(
                "pre-release-status",
                [
                    sys.executable,
                    str(aligned["release_tool"]),
                    "--repo-root",
                    ".",
                    "--plan",
                    str(aligned["release_path"]),
                    "--output",
                    str(pre_status_report),
                    "--status",
                    "--allow-network",
                    "--force",
                    "--json",
                ],
                timeout=600,
            )
            pre_status = read_json_object(
                pre_status_report,
                "pre-release status report",
            )
            snapshot = pre_status.get("snapshot") or {}
            if snapshot.get("release_commit_aligned") is not True:
                raise DeliveryError(
                    "current HEAD is neither expected base nor "
                    "the exact planned release commit"
                )
            if pre_status.get("blocked") is True:
                raise DeliveryError(
                    "aligned release commit is blocked: "
                    + str(pre_status.get("status_code"))
                )
            if pre_status.get("safe_to_resume") is not True:
                raise DeliveryError(
                    "aligned release commit is not safe to resume"
                )

            installation_summary = {
                "status_code": "SKIPPED_ALIGNED_RELEASE_COMMIT",
                "report": None,
            }
            smoke_summary = {
                "status_code": "SKIPPED_ALIGNED_RELEASE_COMMIT",
                "report": None,
            }
            self.steps.extend(
                [
                    {
                        "step": "package_installation",
                        "status": "skipped_aligned_release_commit",
                    },
                    {
                        "step": "focused_acceptance",
                        "status": "skipped_reuse_canonical_gate",
                    },
                    {
                        "step": "clean_install_smoke",
                        "status": "skipped_aligned_release_commit",
                    },
                ]
            )

            if (
                pre_status.get("status_code") == "RELEASE_CLOSED"
                and pre_status.get("release_closed") is True
            ):
                self.steps.append(
                    {
                        "step": "release_status",
                        "status": "already_closed",
                        "report": str(pre_status_report),
                    }
                )
                return {
                    "schema_version": SCHEMA_VERSION,
                    "report_type": REPORT_TYPE,
                    "generated_at": utc_now(),
                    "delivery_id": self.plan["delivery_id"],
                    "target_version": self.plan["target_version"],
                    "status": "passed",
                    "status_code": "PACKAGE_RELEASE_CLOSED",
                    "release_closed": True,
                    "head": current_head,
                    "resume_mode": True,
                    "installation": installation_summary,
                    "focused_acceptance": focused,
                    "clean_install_smoke": smoke_summary,
                    "release": {
                        "status_code": "RELEASE_CLOSED",
                        "report": str(pre_status_report),
                    },
                    "final_status": {
                        "status_code": "RELEASE_CLOSED",
                        "report": str(pre_status_report),
                    },
                    "steps": self.steps,
                    "command_logs": self.logs,
                    "alignment": aligned["checks"],
                    "boundaries": BOUNDARIES,
                    "authority": {
                        "wrapper_did_not_replace_existing_gates": True,
                        "all_mutation_tokens_were_explicit": True,
                        "tests_were_reused_only_by_existing_guard": True,
                        "final_status_was_read_only": True,
                    },
                }

        release_command = [
            sys.executable,
            str(aligned["release_tool"]),
            "--repo-root",
            ".",
            "--plan",
            str(aligned["release_path"]),
            "--output",
            str(release_report),
            "--confirm-run",
            "--workflow-token",
            self.args.workflow_token,
            "--git-plan-token",
            self.args.git_plan_token,
            "--git-stage-token",
            self.args.git_stage_token,
            "--git-commit-token",
            self.args.git_commit_token,
            "--git-push-token",
            self.args.git_push_token,
            "--tag-create-token",
            self.args.tag_create_token,
            "--tag-push-token",
            self.args.tag_push_token,
            "--release-publish-token",
            self.args.release_publish_token,
            "--latest-promotion-token",
            self.args.latest_promotion_token,
            "--allow-network",
            "--test-timeout",
            str(self.args.test_timeout),
            "--force",
            "--json",
        ]
        self.run(
            "unified-release",
            release_command,
            timeout=max(self.args.test_timeout + 600, 1800),
        )
        release = read_json_object(
            release_report,
            "release report",
        )
        if (
            release.get("status_code") != "RELEASE_CLOSED"
            or release.get("release_closed") is not True
        ):
            raise DeliveryError(
                "unified release did not reach RELEASE_CLOSED"
            )
        self.steps.append(
            {
                "step": "unified_release",
                "status": "passed",
                "report": str(release_report),
            }
        )

        self.run(
            "release-status",
            [
                sys.executable,
                str(aligned["release_tool"]),
                "--repo-root",
                ".",
                "--plan",
                str(aligned["release_path"]),
                "--output",
                str(status_report),
                "--status",
                "--allow-network",
                "--force",
                "--json",
            ],
            timeout=600,
        )
        status = read_json_object(
            status_report,
            "release status report",
        )
        if (
            status.get("status_code") != "RELEASE_CLOSED"
            or status.get("release_closed") is not True
        ):
            raise DeliveryError(
                "final read-only status is not RELEASE_CLOSED"
            )
        self.steps.append(
            {
                "step": "release_status",
                "status": "passed",
                "report": str(status_report),
            }
        )

        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "delivery_id": self.plan["delivery_id"],
            "target_version": self.plan["target_version"],
            "status": "passed",
            "status_code": "PACKAGE_RELEASE_CLOSED",
            "release_closed": True,
            "head": release.get("head"),
            "resume_mode": resume_mode,
            "installation": installation_summary,
            "focused_acceptance": focused,
            "clean_install_smoke": smoke_summary,
            "release": {
                "status_code": release.get("status_code"),
                "report": str(release_report),
            },
            "final_status": {
                "status_code": status.get("status_code"),
                "report": str(status_report),
            },
            "steps": self.steps,
            "command_logs": self.logs,
            "alignment": aligned["checks"],
            "boundaries": BOUNDARIES,
            "authority": {
                "wrapper_did_not_replace_existing_gates": True,
                "all_mutation_tokens_were_explicit": True,
                "tests_were_evidence_only": True,
                "final_status_was_read_only": True,
            },
        }


def print_minimal(
    report: Mapping[str, Any],
    output: Path,
) -> None:
    print("KONOHA SUPERVISED PACKAGE-TO-RELEASE")
    print(f"version: {report.get('target_version')}")
    print(f"status_code: {report.get('status_code')}")
    print(f"head: {report.get('head')}")
    print(
        "focused_suites: "
        f"{len(report.get('focused_acceptance') or [])}"
    )
    print(
        "clean_install_smoke: "
        f"{(report.get('clean_install_smoke') or {}).get('status_code')}"
    )
    print(
        "release: "
        f"{(report.get('release') or {}).get('status_code')}"
    )
    print(
        "final_status: "
        f"{(report.get('final_status') or {}).get('status_code')}"
    )
    print(f"report: {output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run supervised package installation, acceptance, "
            "release, and final status."
        )
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test-timeout", type=int, default=1200)

    parser.add_argument("--confirm-run", action="store_true")
    parser.add_argument("--allow-network", action="store_true")
    parser.add_argument("--delivery-token", default="")
    parser.add_argument("--installation-token", default="")
    parser.add_argument("--workflow-token", default="")
    parser.add_argument("--git-plan-token", default="")
    parser.add_argument("--git-stage-token", default="")
    parser.add_argument("--git-commit-token", default="")
    parser.add_argument("--git-push-token", default="")
    parser.add_argument("--tag-create-token", default="")
    parser.add_argument("--tag-push-token", default="")
    parser.add_argument("--release-publish-token", default="")
    parser.add_argument("--latest-promotion-token", default="")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.test_timeout <= 0:
            raise DeliveryError("--test-timeout must be positive")

        repo_root = Path(args.repo_root).resolve()
        plan_path = resolve_repo_file(
            repo_root,
            args.plan,
            "delivery plan",
        )
        output = resolve_output(repo_root, args.output)
        plan = validate_plan(
            read_json_object(plan_path, "delivery plan")
        )
        runner = DeliveryRunner(repo_root, plan, args)
        report = runner.execute()
        write_json(output, report, force=args.force)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print_minimal(report, output)
        return 0

    except DeliveryError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "blocked",
            "status_code": "BLOCKED_PACKAGE_RELEASE",
            "release_closed": False,
            "blocker": str(exc),
            "boundaries": BOUNDARIES,
        }
        try:
            repo_root = Path(args.repo_root).resolve()
            output = resolve_output(repo_root, args.output)
            write_json(output, payload, force=args.force)
        except Exception:
            output = None

        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA PACKAGE-TO-RELEASE BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
            if output is not None:
                print(f"report: {output}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
