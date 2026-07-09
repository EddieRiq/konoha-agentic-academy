#!/usr/bin/env python3
"""Konoha v3.0.1 local model bootstrap, repository audit, and patch planning.

This tool is intentionally local-first and approval-gated.

It can:
- profile the local machine/runtime from WSL/Linux/Windows using read-only inspection;
- recommend a local Ollama model from the observed profile;
- create an Ollama install plan without executing it;
- pull a local model only with explicit network approval;
- run a repository consistency audit through a local Ollama model or a mock model;
- generate a patch plan for README/docs consistency;
- apply only approved documentation patch operations.

It does not:
- read secrets or private Village contents by default;
- invoke remote models;
- run arbitrary shell;
- push to Git;
- treat a local model recommendation or audit as permission.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_VERSION = "1.0.0"

TOKENS = {
    "profile": "PROFILE_LOCAL_COMPUTER",
    "recommend": "RECOMMEND_LOCAL_MODEL",
    "install_plan": "PLAN_OLLAMA_INSTALL",
    "download": "DOWNLOAD_LOCAL_MODEL",
    "audit": "RUN_LOCAL_MODEL_AUDIT",
    "apply_patch": "APPLY_LOCAL_MODEL_DOC_PATCH",
}

BOUNDARIES = {
    "remote_model_invocation": "blocked",
    "unapproved_local_model_invocation": "blocked",
    "unapproved_model_download": "blocked",
    "unapproved_command_execution": "blocked",
    "arbitrary_shell": "blocked",
    "private_context_access_by_default": "blocked",
    "git_operations": "blocked_in_this_tool_use_existing_beta_git_gate",
    "network_access_by_default": "blocked_except_explicit_ollama_pull_or_localhost_api",
}

FORBIDDEN_PARTS = {
    ".git",
    ".venv",
    ".venv-wsl",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "site-packages",
    "alliance/kirigakure",
    "secrets",
    "credentials",
    "private",
    "local",
}

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".sh", ".ps1", ".html", ".css", ".js", ".ts",
}


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def emit(data: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        status = "PASSED" if data.get("status", "passed") == "passed" else "FAILED"
        print(f"KONOHA LOCAL MODEL AUDIT {status}")
        print(f"Command: {data.get('command')}")
        for k, v in BOUNDARIES.items():
            print(f"{k}: {v}")
        paths = data.get("output_paths") or []
        if paths:
            print("Output paths:")
            for p in paths:
                print(f"- {p}")
        blockers = data.get("blockers") or []
        if blockers:
            print("Blockers:")
            for b in blockers:
                print(f"- {b}")


def fail(command: str, blockers: List[str], as_json: bool = False) -> int:
    emit({
        "report_type": "konoha_local_model_audit_error",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "command": command,
        "status": "failed",
        "boundaries": BOUNDARIES,
        "blockers": blockers,
    }, as_json)
    return 1


def require_token(confirm: bool, provided: Optional[str], expected: str, command: str) -> Optional[List[str]]:
    if not confirm:
        return [f"{command} requires explicit confirmation flag"]
    if provided != expected:
        return [f"{command} requires approval token {expected}"]
    return None


def ensure_inside(root: Path, target: Path) -> Path:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if root_resolved == target_resolved or root_resolved in target_resolved.parents:
        return target_resolved
    raise ValueError(f"path escapes allowed root: {target}")


def write_json(path: Path, data: Dict[str, Any], force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"output exists; use --force: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8", newline="\n")


def append_once(path: Path, marker: str, block: str) -> bool:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker in text:
        return False
    if text and not text.endswith("\n"):
        text += "\n"
    text += "\n" + block.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def detect_wsl() -> bool:
    try:
        rel = Path("/proc/sys/kernel/osrelease")
        if rel.exists() and "microsoft" in rel.read_text(encoding="utf-8", errors="ignore").lower():
            return True
    except Exception:
        pass
    return "WSL_DISTRO_NAME" in os.environ


def detect_ram_gib() -> Optional[float]:
    # Linux / WSL path first
    meminfo = Path("/proc/meminfo")
    if meminfo.exists():
        try:
            for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return round(kb / 1024 / 1024, 2)
        except Exception:
            pass
    # POSIX fallback
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            if pages and page_size:
                return round((pages * page_size) / (1024**3), 2)
    except Exception:
        pass
    return None


def safe_which(name: str) -> Optional[str]:
    return shutil.which(name)


def run_git_describe(repo_root: Path) -> Dict[str, Any]:
    result: Dict[str, Any] = {"available": False}
    if not safe_which("git"):
        return result
    for key, cmd in {
        "branch": ["git", "-C", str(repo_root), "branch", "--show-current"],
        "status_short": ["git", "-C", str(repo_root), "status", "--short"],
        "last_commit": ["git", "-C", str(repo_root), "log", "--oneline", "-1"],
    }.items():
        try:
            cp = subprocess.run(cmd, check=False, shell=False, capture_output=True, text=True, timeout=15)
            result["available"] = True
            result[key] = cp.stdout.strip()
            result[f"{key}_exit_code"] = cp.returncode
        except Exception as exc:
            result[f"{key}_error"] = str(exc)
    return result


def collect_profile(repo_root: Path, sandbox_root: Path) -> Dict[str, Any]:
    disk = shutil.disk_usage(str(repo_root))
    profile = {
        "report_type": "local_computer_profile",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "hardware_profile_is_evidence_only": True,
            "local_config_is_not_permission": True,
        },
        "boundaries": BOUNDARIES,
        "runtime": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "is_wsl": detect_wsl(),
            "cwd": str(Path.cwd()),
        },
        "hardware": {
            "cpu_count": os.cpu_count(),
            "ram_gib": detect_ram_gib(),
            "gpu": "not_inspected",
            "vram_gib": None,
            "disk_free_gib_at_repo_root": round(disk.free / (1024**3), 2),
            "disk_total_gib_at_repo_root": round(disk.total / (1024**3), 2),
        },
        "tools": {
            "git": safe_which("git"),
            "ollama": safe_which("ollama"),
            "claude": safe_which("claude"),
            "codex": safe_which("codex"),
            "jq": safe_which("jq"),
            "nvidia_smi": safe_which("nvidia-smi"),
        },
        "repo": run_git_describe(repo_root),
        "paths": {
            "repo_root": str(repo_root.resolve()),
            "sandbox_root": str(sandbox_root.resolve()),
        },
    }
    return profile


def recommend_from_profile(profile: Dict[str, Any], task_domain: str) -> Dict[str, Any]:
    ram = profile.get("hardware", {}).get("ram_gib")
    disk_free = profile.get("hardware", {}).get("disk_free_gib_at_repo_root")
    ollama_available = bool(profile.get("tools", {}).get("ollama"))
    cpu = profile.get("hardware", {}).get("cpu_count") or 0

    reasons: List[str] = []
    blockers: List[str] = []
    candidate = "gemma3:4b"
    fallback = "gemma3:1b"
    use_case = "general repo summarization and consistency audit"

    if "code" in task_domain.lower() or "dev" in task_domain.lower():
        candidate = "qwen2.5-coder:7b"
        fallback = "qwen2.5-coder:1.5b"
        use_case = "code-aware repository summarization and consistency audit"

    if ram is None:
        reasons.append("RAM could not be measured; choose a small fallback unless manually overridden.")
        candidate = fallback
    elif ram < 8:
        candidate = fallback
        reasons.append(f"RAM is {ram} GiB; recommending a very small model.")
    elif ram < 16:
        candidate = fallback
        reasons.append(f"RAM is {ram} GiB; recommending a small coding/general model.")
    elif ram < 32:
        reasons.append(f"RAM is {ram} GiB; recommending a 4B-7B local model if disk allows.")
    else:
        reasons.append(f"RAM is {ram} GiB; a 7B local model should be reasonable for supervised audits.")

    if disk_free is not None and disk_free < 10:
        blockers.append(f"Low free disk at repo root: {disk_free} GiB. Confirm model storage location before pulling.")
    if cpu and cpu < 4:
        reasons.append(f"CPU count is {cpu}; expect slower local inference.")
    if not ollama_available:
        blockers.append("Ollama CLI not detected. Create an install plan before pulling models.")

    return {
        "report_type": "local_model_recommendation",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "recommendation_is_evidence_only": True,
            "model_choice_is_not_permission": True,
            "download_requires_separate_approval": True,
        },
        "boundaries": BOUNDARIES,
        "task_domain": task_domain,
        "recommended_provider": "ollama",
        "recommended_model": candidate,
        "fallback_model": fallback,
        "use_case": use_case,
        "ollama_available": ollama_available,
        "reasons": reasons,
        "blockers": blockers,
        "next_approval_needed": "PLAN_OLLAMA_INSTALL" if not ollama_available else "DOWNLOAD_LOCAL_MODEL",
        "suggested_commands": {
            "install_plan_only": "curl -fsSL https://ollama.com/install.sh | sh",
            "download_model": f"ollama pull {candidate}",
            "run_model": f"ollama run {candidate}",
        },
    }


def cmd_profile(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    sandbox_root = Path(args.sandbox_root)
    try:
        ensure_inside(Path.cwd(), repo_root) if not repo_root.is_absolute() else repo_root.resolve()
    except Exception:
        pass

    profile = collect_profile(repo_root, sandbox_root)
    if args.output:
        blockers = require_token(args.confirm_profile, args.approval_token, TOKENS["profile"], "profile")
        if blockers:
            return fail("profile", blockers, args.json)
        out = Path(args.output)
        write_json(out, profile, args.force)
        result = {"command": "profile", "status": "passed", "output_paths": [str(out.resolve())], **profile}
    else:
        result = {"command": "profile", "status": "passed", **profile}
    emit(result, args.json)
    return 0


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_recommend(args: argparse.Namespace) -> int:
    blockers = require_token(args.confirm_recommendation, args.approval_token, TOKENS["recommend"], "recommend")
    if blockers:
        return fail("recommend", blockers, args.json)

    if args.profile:
        profile = load_json(Path(args.profile))
    else:
        profile = collect_profile(Path(args.repo_root), Path(args.sandbox_root))
    recommendation = recommend_from_profile(profile, args.task_domain)
    if args.model_override:
        recommendation["recommended_model"] = args.model_override
        recommendation.setdefault("reasons", []).append("Model override supplied by user.")
        recommendation["suggested_commands"]["download_model"] = f"ollama pull {args.model_override}"
        recommendation["suggested_commands"]["run_model"] = f"ollama run {args.model_override}"

    out = Path(args.output)
    write_json(out, recommendation, args.force)
    emit({"command": "recommend", "status": "passed", "output_paths": [str(out.resolve())], **recommendation}, args.json)
    return 0


def cmd_install_plan(args: argparse.Namespace) -> int:
    blockers = require_token(args.confirm_plan, args.approval_token, TOKENS["install_plan"], "install-plan")
    if blockers:
        return fail("install-plan", blockers, args.json)

    plan = {
        "report_type": "ollama_install_plan",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "install_plan_is_not_permission": True,
            "network_access_requires_separate_human_approval": True,
        },
        "boundaries": BOUNDARIES,
        "install_command": ["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"],
        "manual_command_for_user_review": "curl -fsSL https://ollama.com/install.sh | sh",
        "notes": [
            "This tool does not run the install command.",
            "Install Ollama manually or through a separately approved controlled command.",
            "After install, run `ollama --version` and `ollama serve` if needed.",
        ],
    }
    out = Path(args.output)
    write_json(out, plan, args.force)
    emit({"command": "install-plan", "status": "passed", "output_paths": [str(out.resolve())], **plan}, args.json)
    return 0


def cmd_pull_model(args: argparse.Namespace) -> int:
    blockers = require_token(args.confirm_download, args.approval_token, TOKENS["download"], "pull-model")
    if blockers:
        return fail("pull-model", blockers, args.json)
    if not args.allow_network:
        return fail("pull-model", ["pull-model requires --allow-network"], args.json)
    if not safe_which("ollama"):
        return fail("pull-model", ["ollama CLI not found on PATH"], args.json)
    if not re.match(r"^[A-Za-z0-9._:/+-]+$", args.model):
        return fail("pull-model", ["model name contains unsupported characters"], args.json)

    started = time.time()
    cp = subprocess.run(["ollama", "pull", args.model], shell=False, capture_output=True, text=True, timeout=args.timeout_seconds)
    report = {
        "report_type": "local_model_download_report",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "download_report_is_evidence_only": True,
            "download_does_not_authorize_model_invocation": True,
        },
        "boundaries": BOUNDARIES,
        "provider": "ollama",
        "model": args.model,
        "command": ["ollama", "pull", args.model],
        "exit_code": cp.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "stdout": cp.stdout[-12000:],
        "stderr": cp.stderr[-12000:],
        "success": cp.returncode == 0,
    }
    out = Path(args.output)
    write_json(out, report, args.force)
    emit({"command": "pull-model", "status": "passed" if cp.returncode == 0 else "failed", "output_paths": [str(out.resolve())], **report}, args.json)
    return 0 if cp.returncode == 0 else 1


def is_forbidden_path(path: Path) -> bool:
    parts = set(path.parts)
    joined = "/".join(path.parts)
    for forbidden in FORBIDDEN_PARTS:
        if forbidden in parts or forbidden in joined:
            return True
    if path.name.startswith(".env"):
        return True
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return True
    return False


def repo_file_inventory(repo_root: Path, limit: int = 500) -> List[str]:
    files: List[str] = []
    for path in sorted(repo_root.rglob("*")):
        if len(files) >= limit:
            break
        try:
            rel = path.relative_to(repo_root)
        except ValueError:
            continue
        if is_forbidden_path(rel):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            files.append(str(rel).replace("\\", "/"))
    return files


def read_snippet(repo_root: Path, rel: str, max_chars: int = 5000) -> str:
    path = repo_root / rel
    if not path.exists() or not path.is_file():
        return ""
    if is_forbidden_path(Path(rel)):
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
    return text[:max_chars]


def heuristic_inconsistencies(repo_root: Path, files: List[str]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    readme = read_snippet(repo_root, "README.md", 20000)
    changelog = read_snippet(repo_root, "CHANGELOG.md", 20000)
    if "Konoha Beta" not in readme and "v3.0.0" not in readme:
        issues.append({
            "id": "readme_missing_v3_beta_status",
            "severity": "medium",
            "evidence": "README.md does not clearly mention Konoha Beta/v3.0 runtime status.",
            "suggested_change": "Add a concise current beta status section to README.md.",
        })
    if "local model" not in readme.lower() and "Ollama" not in readme:
        issues.append({
            "id": "readme_missing_local_model_runtime",
            "severity": "medium",
            "evidence": "README.md does not clearly mention local model bootstrap/Ollama audit path.",
            "suggested_change": "Add v3.0.1 local model bootstrap and repo consistency audit note.",
        })
    if any(f.startswith("tools/beta_runtime") for f in files) and "tools/beta_runtime" not in readme:
        issues.append({
            "id": "readme_missing_beta_runtime_path",
            "severity": "low",
            "evidence": "tools/beta_runtime exists but README.md may not surface the terminal beta runtime path.",
            "suggested_change": "Mention tools/beta_runtime as beta terminal runtime entrypoint.",
        })
    if "v3.0.1" not in changelog:
        issues.append({
            "id": "changelog_missing_v3_0_1",
            "severity": "low",
            "evidence": "CHANGELOG.md does not mention v3.0.1 local model audit patch.",
            "suggested_change": "Add v3.0.1 entry under Unreleased/Added.",
        })
    return issues


def build_audit_prompt(repo_root: Path, files: List[str]) -> str:
    readme = read_snippet(repo_root, "README.md", 12000)
    guides_readme = read_snippet(repo_root, "docs/guides/README.md", 6000)
    examples_readme = read_snippet(repo_root, "examples/README.md", 6000)
    roadmap = read_snippet(repo_root, "docs/roadmap.md", 8000)
    file_list = "\n".join(files[:250])
    return f"""
You are Konoha Local Model Auditor.

Task:
Compare the repository file inventory against README and index documents.
Find missing or inconsistent public documentation about current runtime capabilities.
Do not assume permission to edit. Produce evidence and proposed changes only.

Return concise JSON with this shape:
{{
  "summary": "...",
  "inconsistencies": [
    {{"id": "...", "severity": "low|medium|high", "evidence": "...", "suggested_change": "..."}}
  ],
  "recommended_commit_message": "..."
}}

Repository files:
{file_list}

README.md excerpt:
{readme}

docs/guides/README.md excerpt:
{guides_readme}

examples/README.md excerpt:
{examples_readme}

docs/roadmap.md excerpt:
{roadmap}
""".strip()


def call_ollama(model: str, prompt: str, host: str, timeout: int) -> Tuple[str, Dict[str, Any]]:
    url = host.rstrip("/") + "/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    data = json.loads(body)
    text = data.get("response", "")
    usage = {
        "usage_source": "provider_reported",
        "input_tokens": data.get("prompt_eval_count"),
        "output_tokens": data.get("eval_count"),
        "total_duration": data.get("total_duration"),
        "prompt_eval_duration": data.get("prompt_eval_duration"),
        "eval_duration": data.get("eval_duration"),
    }
    return text, usage


def parse_jsonish(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def make_patch_plan(repo_root: Path, issues: List[Dict[str, Any]], model_summary: str, recommended_commit: str) -> Dict[str, Any]:
    operations: List[Dict[str, Any]] = []
    issue_ids = {i.get("id") for i in issues}
    if "readme_missing_v3_beta_status" in issue_ids or "readme_missing_local_model_runtime" in issue_ids:
        operations.append({
            "operation": "append_once",
            "path": "README.md",
            "marker": "## Konoha Beta Local Model Audit",
            "content": """## Konoha Beta Local Model Audit

Konoha v3.0.1 adds a local-first beta patch flow for computer profiling, Ollama local model recommendation, approved local model download, repository consistency audit, documentation patch planning, and gated Git follow-up.

Local model audits are evidence only. Model output is not permission. Repository changes, commits, and pushes still require explicit human approval."""
        })
    if "changelog_missing_v3_0_1" in issue_ids:
        operations.append({
            "operation": "append_once",
            "path": "CHANGELOG.md",
            "marker": "Added v3.0.1 Local Model Bootstrap",
            "content": """## [v3.0.1] - Local Model Bootstrap, Repo Audit and Patch Flow

### Added

- Added v3.0.1 Local Model Bootstrap, Repo Consistency Audit and Auto-Git Patch Flow with WSL/local computer profile, Ollama recommendation, approved model download, local model repository audit, documentation patch planning, and gated Git follow-up."""
        })
    operations.append({
        "operation": "append_once",
        "path": "docs/roadmap.md",
        "marker": "v3.0.1 Local Model Bootstrap, Repo Audit and Patch Flow",
        "content": """### v3.0.1 Local Model Bootstrap, Repo Audit and Patch Flow

- Add initial local computer analysis, local model recommendation, approved Ollama model download, local model repository consistency audit, and documentation patch planning before broader v3.1 optimization patches."""
    })
    return {
        "report_type": "local_repo_patch_plan",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "patch_plan_is_not_permission": True,
            "apply_requires_separate_approval": True,
            "git_requires_existing_beta_git_gate": True,
        },
        "boundaries": BOUNDARIES,
        "summary": model_summary,
        "issues_considered": issues,
        "operations": operations,
        "recommended_commit_message": recommended_commit or "Update Konoha beta local model audit documentation",
        "requires_approval_token": TOKENS["apply_patch"],
        "next_git_gate": {
            "use_existing_command": "tools/beta_runtime/run_konoha_beta.py git-plan/git-stage/git-commit/git-push",
            "suggested_commit_message": recommended_commit or "Update Konoha beta local model audit documentation",
        },
    }


def cmd_audit_repo(args: argparse.Namespace) -> int:
    blockers = require_token(args.confirm_audit, args.approval_token, TOKENS["audit"], "audit-repo")
    if blockers:
        return fail("audit-repo", blockers, args.json)
    if args.use_ollama and not args.allow_localhost:
        return fail("audit-repo", ["audit-repo with --use-ollama requires --allow-localhost"], args.json)
    if not args.use_ollama and not args.mock_local_model:
        return fail("audit-repo", ["choose either --use-ollama or --mock-local-model"], args.json)

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    files = repo_file_inventory(repo_root, limit=args.file_limit)
    prompt = build_audit_prompt(repo_root, files)
    heuristic_issues = heuristic_inconsistencies(repo_root, files)
    model_raw = ""
    usage: Dict[str, Any] = {"usage_source": "not_used", "input_tokens": None, "output_tokens": None}
    model_json: Optional[Dict[str, Any]] = None

    if args.mock_local_model:
        model_raw = json.dumps({
            "summary": "Mock local model audit completed. Review heuristic issues and proposed documentation patch before applying.",
            "inconsistencies": heuristic_issues,
            "recommended_commit_message": "Update beta local model audit documentation"
        }, indent=2)
        usage = {
            "usage_source": "mock_estimated",
            "input_tokens": max(1, len(prompt) // 4),
            "output_tokens": max(1, len(model_raw) // 4),
        }
        model_json = parse_jsonish(model_raw)
    else:
        try:
            model_raw, usage = call_ollama(args.model, prompt, args.ollama_host, args.timeout_seconds)
            model_json = parse_jsonish(model_raw)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            return fail("audit-repo", [f"Ollama local audit failed: {exc}"], args.json)

    model_issues = []
    model_summary = ""
    recommended_commit = ""
    if model_json:
        model_summary = str(model_json.get("summary", ""))
        model_issues = model_json.get("inconsistencies") or []
        recommended_commit = str(model_json.get("recommended_commit_message", ""))
    if not isinstance(model_issues, list):
        model_issues = []

    # Preserve heuristic issues even if the model misses them.
    combined = []
    seen = set()
    for issue in list(model_issues) + heuristic_issues:
        if not isinstance(issue, dict):
            continue
        ident = issue.get("id") or issue.get("evidence") or json.dumps(issue, sort_keys=True)
        if ident in seen:
            continue
        seen.add(ident)
        combined.append(issue)

    audit = {
        "report_type": "local_repo_consistency_audit",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "local_model_output_is_evidence_only": True,
            "audit_report_is_not_permission": True,
            "token_usage_is_evidence_only": True,
        },
        "boundaries": BOUNDARIES,
        "provider": "ollama" if args.use_ollama else "mock_local_model",
        "model": args.model,
        "repo_root": str(repo_root),
        "files_considered_count": len(files),
        "files_considered_sample": files[:200],
        "prompt_chars": len(prompt),
        "model_raw_response": model_raw,
        "model_parsed": model_json,
        "usage": usage,
        "inconsistencies": combined,
        "status": "needs_human_review" if combined else "no_obvious_inconsistencies_found",
        "question_for_human": "¿Está bien aplicar el patch plan propuesto o querés ajustar qué documentación debe cambiar?",
    }
    patch_plan = make_patch_plan(repo_root, combined, model_summary or "Local repo consistency audit completed.", recommended_commit)

    audit_json = output_dir / f"{args.audit_id}_repo_consistency_audit.json"
    audit_md = output_dir / f"{args.audit_id}_repo_consistency_audit.md"
    patch_json = output_dir / f"{args.audit_id}_repo_patch_plan.json"
    write_json(audit_json, audit, args.force)
    write_json(patch_json, patch_plan, args.force)
    md = [
        f"# Local Repo Consistency Audit: {args.audit_id}",
        "",
        "## Authority",
        "",
        "- Local model output is evidence only.",
        "- Audit report is not permission.",
        "- Patch plan requires explicit approval.",
        "",
        "## Summary",
        "",
        audit.get("model_parsed", {}).get("summary", "Review JSON audit for model response.") if isinstance(audit.get("model_parsed"), dict) else "Review JSON audit for model response.",
        "",
        "## Proposed inconsistencies / faltantes",
        "",
    ]
    for issue in combined:
        md.append(f"- **{issue.get('id', 'issue')}** ({issue.get('severity', 'unknown')}): {issue.get('evidence', '')} Proposed: {issue.get('suggested_change', '')}")
    md += [
        "",
        "## Human question",
        "",
        audit["question_for_human"],
        "",
        "## Recommended commit message",
        "",
        patch_plan["recommended_commit_message"],
        "",
    ]
    audit_md.write_text("\n".join(md), encoding="utf-8", newline="\n")

    emit({
        "command": "audit-repo",
        "status": "passed",
        "output_paths": [str(audit_json), str(audit_md), str(patch_json)],
        "audit": audit,
    }, args.json)
    return 0


def cmd_apply_doc_patch(args: argparse.Namespace) -> int:
    blockers = require_token(args.confirm_apply, args.approval_token, TOKENS["apply_patch"], "apply-doc-patch")
    if blockers:
        return fail("apply-doc-patch", blockers, args.json)
    repo_root = Path(args.repo_root).resolve()
    plan = load_json(Path(args.patch_plan))
    changed: List[str] = []
    skipped: List[str] = []

    for op in plan.get("operations", []):
        if op.get("operation") != "append_once":
            skipped.append(f"unsupported operation: {op.get('operation')}")
            continue
        rel = Path(op["path"])
        if is_forbidden_path(rel):
            skipped.append(f"forbidden path: {rel}")
            continue
        target = ensure_inside(repo_root, repo_root / rel)
        if append_once(target, op["marker"], op["content"]):
            changed.append(str(rel).replace("\\", "/"))
        else:
            skipped.append(f"marker already present: {rel}")

    report = {
        "report_type": "local_repo_doc_patch_apply_report",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "authority": {
            "patch_apply_report_is_evidence_only": True,
            "git_requires_existing_beta_git_gate": True,
        },
        "boundaries": BOUNDARIES,
        "patch_plan": str(Path(args.patch_plan).resolve()),
        "changed_paths": changed,
        "skipped": skipped,
        "recommended_commit_message": plan.get("recommended_commit_message"),
        "next_step": "Review git diff, run tests, then use beta runtime Git gate if approved.",
    }
    out = Path(args.output)
    write_json(out, report, args.force)
    emit({"command": "apply-doc-patch", "status": "passed", "output_paths": [str(out.resolve())], **report}, args.json)
    return 0


def cmd_states(args: argparse.Namespace) -> int:
    emit({
        "command": "states",
        "status": "passed",
        "report_type": "local_model_audit_states",
        "schema_version": SCHEMA_VERSION,
        "generated_at": now(),
        "approval_tokens": TOKENS,
        "boundaries": BOUNDARIES,
        "commands": [
            "profile",
            "recommend",
            "install-plan",
            "pull-model",
            "audit-repo",
            "apply-doc-patch",
            "states",
        ],
    }, args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Konoha v3.0.1 local model bootstrap and repo audit")
    sub = p.add_subparsers(dest="command", required=True)

    def add_common(sp):
        sp.add_argument("--json", action="store_true")

    sp = sub.add_parser("profile")
    add_common(sp)
    sp.add_argument("--repo-root", default=".")
    sp.add_argument("--sandbox-root", default="./sandbox")
    sp.add_argument("--output")
    sp.add_argument("--confirm-profile", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_profile)

    sp = sub.add_parser("recommend")
    add_common(sp)
    sp.add_argument("--repo-root", default=".")
    sp.add_argument("--sandbox-root", default="./sandbox")
    sp.add_argument("--profile")
    sp.add_argument("--task-domain", default="repo_consistency_audit")
    sp.add_argument("--model-override")
    sp.add_argument("--output", required=True)
    sp.add_argument("--confirm-recommendation", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_recommend)

    sp = sub.add_parser("install-plan")
    add_common(sp)
    sp.add_argument("--output", required=True)
    sp.add_argument("--confirm-plan", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_install_plan)

    sp = sub.add_parser("pull-model")
    add_common(sp)
    sp.add_argument("--model", required=True)
    sp.add_argument("--output", required=True)
    sp.add_argument("--allow-network", action="store_true")
    sp.add_argument("--confirm-download", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--timeout-seconds", type=int, default=1800)
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_pull_model)

    sp = sub.add_parser("audit-repo")
    add_common(sp)
    sp.add_argument("--repo-root", default=".")
    sp.add_argument("--audit-id", required=True)
    sp.add_argument("--model", default="gemma3:4b")
    sp.add_argument("--output-dir", required=True)
    sp.add_argument("--use-ollama", action="store_true")
    sp.add_argument("--mock-local-model", action="store_true")
    sp.add_argument("--allow-localhost", action="store_true")
    sp.add_argument("--ollama-host", default="http://localhost:11434")
    sp.add_argument("--timeout-seconds", type=int, default=300)
    sp.add_argument("--file-limit", type=int, default=500)
    sp.add_argument("--confirm-audit", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_audit_repo)

    sp = sub.add_parser("apply-doc-patch")
    add_common(sp)
    sp.add_argument("--repo-root", default=".")
    sp.add_argument("--patch-plan", required=True)
    sp.add_argument("--output", required=True)
    sp.add_argument("--confirm-apply", action="store_true")
    sp.add_argument("--approval-token")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_apply_doc_patch)

    sp = sub.add_parser("states")
    add_common(sp)
    sp.set_defaults(func=cmd_states)

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        return fail(args.command, [str(exc)], getattr(args, "json", False))


if __name__ == "__main__":
    raise SystemExit(main())
