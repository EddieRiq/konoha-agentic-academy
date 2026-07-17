from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

PRIVATE_MARKERS = (
    "alliance/kirigakure/",
    "private-library/",
    "/memory/",
    "memory/local/",
    "vault/",
    "sandbox/",
    ".env",
    "credentials",
    "token",
    "secret",
)

DEFAULT_REQUIRED = (
    "AGENTS.md",
    "docs/architecture/konoha_v4_operating_model.md",
    "config/konoha_v4_capabilities.json",
    "config/policies/read_only_workspace_commands.json",
)

@dataclass(frozen=True)
class ProviderReadiness:
    provider: str
    executable: str | None
    available: bool
    version: str
    models: list[str]
    evidence: str

@dataclass
class AcquiredContext:
    workspace_root: str
    workspace_read_authorized: bool
    private_paths_excluded: list[str]
    loaded_files: dict[str, str]
    missing_files: list[str]
    provider_readiness: dict[str, dict[str, Any]]
    registered_families: list[str]
    read_only_policy: dict[str, Any]
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

def _run(command: list[str], cwd: Path, timeout: int = 20) -> tuple[int, str, str]:
    try:
        cp = subprocess.run(
            command, cwd=cwd, text=True, capture_output=True,
            timeout=timeout, check=False,
        )
        return cp.returncode, cp.stdout.strip(), cp.stderr.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(exc)

def _safe_repo_file(repo: Path, rel: str) -> Path | None:
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        return None
    normalized = rel_path.as_posix()
    if any(marker in normalized for marker in PRIVATE_MARKERS):
        return None
    path = (repo / rel_path).resolve()
    try:
        path.relative_to(repo.resolve())
    except ValueError:
        return None
    return path

def _extract_local_references(text: str) -> list[str]:
    candidates = set()
    for token in re.findall(r"(?<![\w/.-])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+\.(?:md|json|yaml|yml|toml))", text):
        candidates.add(token)
    return sorted(candidates)

def _read_text(path: Path, limit: int = 120_000) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > limit:
        return text[:limit] + "\n[TRUNCATED BY CONTEXT ACQUISITION POLICY]"
    return text

def _probe_provider(provider: str, repo: Path) -> ProviderReadiness:
    executable = shutil.which(provider)
    if not executable:
        return ProviderReadiness(provider, None, False, "", [], "executable_not_found")

    models: list[str] = []
    if provider == "codex":
        code, out, err = _run([executable, "--version"], repo)
    elif provider == "claude":
        code, out, err = _run([executable, "--version"], repo)
    elif provider == "ollama":
        code, out, err = _run([executable, "--version"], repo)
        list_code, list_out, _ = _run([executable, "list"], repo)
        if list_code == 0:
            for line in list_out.splitlines()[1:]:
                parts = line.split()
                if parts:
                    models.append(parts[0])
    else:
        return ProviderReadiness(provider, executable, False, "", [], "unsupported_provider")

    version = out or err
    return ProviderReadiness(
        provider=provider,
        executable=executable,
        available=(code == 0),
        version=version[:500],
        models=models,
        evidence="deterministic_local_probe",
    )

def acquire_context(repo: Path, registry: Any) -> AcquiredContext:
    repo = repo.resolve()
    loaded: dict[str, str] = {}
    missing: list[str] = []
    notes: list[str] = []

    queue = list(DEFAULT_REQUIRED)
    visited: set[str] = set()
    while queue:
        rel = queue.pop(0)
        if rel in visited:
            continue
        visited.add(rel)
        path = _safe_repo_file(repo, rel)
        if path is None:
            notes.append(f"excluded_by_policy:{rel}")
            continue
        if not path.is_file():
            if rel == "AGENTS.md":
                notes.append("AGENTS.md_absent_not_user_context")
            else:
                missing.append(rel)
            continue
        text = _read_text(path)
        loaded[rel] = text
        if rel.endswith(".md"):
            for ref in _extract_local_references(text):
                if ref not in visited:
                    queue.append(ref)

    policy_path = repo / "config" / "policies" / "read_only_workspace_commands.json"
    if policy_path.is_file():
        read_only_policy = json.loads(policy_path.read_text(encoding="utf-8"))
    else:
        read_only_policy = {}

    providers = {
        name: asdict(_probe_provider(name, repo))
        for name in ("codex", "claude", "ollama")
    }

    return AcquiredContext(
        workspace_root=str(repo),
        workspace_read_authorized=True,
        private_paths_excluded=list(PRIVATE_MARKERS),
        loaded_files=loaded,
        missing_files=sorted(set(missing)),
        provider_readiness=providers,
        registered_families=registry.available_families(),
        read_only_policy=read_only_policy,
        notes=notes,
    )

_LOCAL_RESOLVABLE_PATTERNS = (
    "no tengo aún el contenido leído",
    "primera fase de ejecución debe leer",
    "no está provisto el contenido",
    "si existe y es accesible",
    "no está confirmado si las herramientas",
    "disponibilidad de claude",
    "disponibilidad de ollama",
    "definición formal de jounin",
    "lista completa de comandos read-only",
    "rutas locales o privadas están autorizadas",
)

def normalize_missing_context(items: list[str], context: AcquiredContext) -> tuple[list[str], list[str]]:
    """Separate genuine user decisions from context that Konoha can resolve itself."""
    user_required: list[str] = []
    locally_resolved: list[str] = []
    loaded_lower = {k.lower() for k in context.loaded_files}
    families_lower = {x.lower() for x in context.registered_families}

    for raw in items:
        text = str(raw).strip()
        lower = text.lower()
        resolvable = any(pattern in lower for pattern in _LOCAL_RESOLVABLE_PATTERNS)

        for rel in loaded_lower:
            if rel in lower:
                resolvable = True
        if "jounin" in lower and any("jounin" in x for x in families_lower):
            resolvable = True
        if ("read-only" in lower or "read only" in lower) and context.read_only_policy:
            resolvable = True
        if any(provider in lower and "dispon" in lower for provider in context.provider_readiness):
            resolvable = True

        if resolvable:
            locally_resolved.append(text)
        else:
            user_required.append(text)
    return user_required, locally_resolved
