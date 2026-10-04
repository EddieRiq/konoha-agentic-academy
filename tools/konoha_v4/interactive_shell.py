"""Terminal presentation and safe project metadata for the Konoha shell.

This module intentionally contains no mission runtime, provider calls, or
repository file inspection. The existing conversation loop remains the engine.
"""
from __future__ import annotations

import hashlib
import os
import random
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


WORDMARK = "K O N O H A"


def sanitize_display(value: object) -> str:
    """Replace non-printable characters in untrusted terminal display text."""
    return "".join(character if character.isprintable() else "�" for character in str(value))

MASCOTS = {
    "rookie_shinobi": "  /\\  \n (o_o)\n /|_|\\",
    "masked_scout": "  .--.\n /o  o\\\n | -- |",
    "wandering_swordsman": "  __\n (.. )\n /|==",
    "storm_captain": "  .-.\n (⚡)\n /|\\",
    "spirit_guard": "  (^)\n (   )\n  / \\",
    "scroll_keeper": "  ___\n /___\\\n |:::|",
}


@dataclass(frozen=True)
class ProjectInfo:
    cwd: Path
    git_root: Path | None
    name: str
    branch: str | None
    git_state: str
    remote_identity: str | None
    identity: str


def _git(cwd: Path, *args: str) -> str | None:
    env = dict(os.environ)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        result = subprocess.run(
            ["git", *args], cwd=str(cwd), env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            check=False, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip()


def safe_remote_identity(remote: str | None) -> str | None:
    """Return a display-safe remote identity without userinfo/query secrets."""
    if not remote:
        return None
    if "://" in remote:
        try:
            parsed = urlsplit(remote)
            if parsed.scheme.lower() not in {"http", "https", "ssh", "git"}:
                return None
            host = parsed.hostname or ""
            if parsed.port:
                host += f":{parsed.port}"
            path = parsed.path.rstrip("/")
            if path.endswith(".git"):
                path = path[:-4]
            safe = urlunsplit((parsed.scheme.lower(), host.lower(), path, "", ""))
            return safe or None
        except ValueError:
            return None
    # SCP-like SSH remotes: user@host:path. Drop the user portion.
    match = re.fullmatch(r"(?:[^@/:]+@)?([^:/]+):(.+)", remote)
    if match:
        host, path = match.groups()
        return f"ssh://{host.lower()}/{path.rstrip('/').removesuffix('.git')}"
    return None


def detect_project(cwd: Path | None = None) -> ProjectInfo:
    current = (cwd or Path.cwd()).resolve()
    raw_root = _git(current, "rev-parse", "--show-toplevel")
    git_root = Path(raw_root).resolve() if raw_root else None
    project_path = git_root or current
    branch = _git(project_path, "branch", "--show-current") if git_root else None
    if git_root and not branch:
        branch = "detached HEAD"
    status = (
        _git(project_path, "status", "--porcelain=v1", "--untracked-files=all")
        if git_root else None
    )
    git_state = (
        ("dirty" if status else "clean") if status is not None
        else ("unknown" if git_root else "not a Git repository")
    )
    remote = _git(project_path, "config", "--get", "remote.origin.url") if git_root else None
    remote_identity = safe_remote_identity(remote)
    identity_source = "\0".join((str(project_path), remote_identity or ""))
    identity = hashlib.sha256(identity_source.encode("utf-8")).hexdigest()[:24]
    return ProjectInfo(
        cwd=current, git_root=git_root, name=project_path.name or "project",
        branch=branch or None, git_state=git_state,
        remote_identity=remote_identity, identity=identity,
    )


def state_root_for_project(info: ProjectInfo) -> Path:
    override = os.environ.get("KONOHA_PROJECT_STATE_ROOT") or os.environ.get("KONOHA_STATE_ROOT")
    if override:
        base = Path(override).expanduser()
    elif os.environ.get("XDG_STATE_HOME"):
        base = Path(os.environ["XDG_STATE_HOME"]).expanduser() / "konoha"
    else:
        base = Path.home() / ".local" / "state" / "konoha"
    return base / "projects" / info.identity


def select_mascot() -> tuple[str, str]:
    forced = os.environ.get("KONOHA_MASCOT")
    if forced in MASCOTS:
        return forced, MASCOTS[forced]
    name = random.choice(tuple(MASCOTS))
    return name, MASCOTS[name]


def print_splash(*, tty: bool, no_color: bool = False, no_splash: bool = False,
                 art_directory: Path | None = None) -> str | None:
    if not tty or no_splash or os.environ.get("KONOHA_NO_SPLASH"):
        return None
    name, mascot = select_mascot()
    color = "" if no_color or "NO_COLOR" in os.environ or os.environ.get("TERM") == "dumb" else "\033[36m"
    reset = "" if not color else "\033[0m"
    print(f"{color}{WORDMARK}{reset}")
    if not render_local_art_if_available(art_directory):
        print(f"\n{mascot}\n  {name}")
    return name


def dashboard_lines(info: ProjectInfo, workspace: Path) -> list[str]:
    return [
        f"Project: {sanitize_display(info.name)}",
        f"Project identity: {sanitize_display(info.identity)}",
        f"Repository: {sanitize_display(info.git_root) if info.git_root else 'not detected'}",
        f"Branch: {sanitize_display(info.branch) if info.branch else 'not available'}",
        f"Git state: {sanitize_display(info.git_state)}",
        f"Remote: {sanitize_display(info.remote_identity) if info.remote_identity else 'not configured'}",
        f"Workspace path: {sanitize_display(workspace)}",
        f"Project workspace: {'available' if workspace.is_dir() else 'not created'}",
        "Active mission: not checked at startup",
        "Provider readiness: not checked at startup",
    ]


def provider_executable_status() -> dict[str, bool]:
    """Report local executable presence only; do not invoke providers."""
    return {name: shutil.which(name) is not None for name in ("codex", "claude", "ollama")}


def local_art_path() -> Path | None:
    configured = os.environ.get("KONOHA_ART_DIR")
    return Path(configured).expanduser() if configured else None


def render_local_art_if_available(directory: Path | None) -> bool:
    """Use chafa only for explicitly configured local art; always fail soft."""
    if directory is None or not directory.is_dir() or not shutil.which("chafa"):
        return False
    candidates = sorted(
        p for p in directory.iterdir()
        if not p.is_symlink() and p.parent.resolve() == directory.resolve()
        and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}
        and p.is_file()
    )
    if not candidates:
        return False
    try:
        result = subprocess.run(
            ["chafa", "--symbols", "block", str(candidates[0])],
            check=False, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if result.returncode or not result.stdout:
        return False
    print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    return True
