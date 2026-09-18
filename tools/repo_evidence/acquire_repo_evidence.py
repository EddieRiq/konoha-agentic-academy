"""Deterministic RepositoryEvidencePack acquisition.

No model call. No writes into the target repository. Reuses
tools.konoha_v4.context_acquisition.PRIVATE_MARKERS - the only path-exclusion
logic actually enforced anywhere in this codebase today (see
context_acquisition._safe_repo_file). config/policies/read_only_workspace_
commands.json's "excluded_by_default" list is loaded by acquire_context() as
descriptive metadata only - it has no existing callable parser anywhere in
the codebase (verified by grep), so it is not re-derived here; this module
applies the same enforced constant context_acquisition.py already trusts,
plus a separately-justified GENERATED_DIRS set for VCS/build-cache noise
(a different concern from "private", never blurred into PRIVATE_MARKERS).

AcquiredContext (tools.konoha_v4.context_acquisition) stays Konoha's own
doctrine/capability context. RepositoryEvidencePack describes the target
workspace being studied - the two are never merged.
"""

from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
import sys
import threading
import tomllib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.konoha_v4.context_acquisition import PRIVATE_MARKERS

CONTRACT_VERSION = "1.0.0"

# ponytail: no reusable generated/cache-dir exclusion list exists anywhere
# in the codebase (verified by grep before writing this) - one conservative,
# named set introduced here rather than a config file, since it never varies
# per repo. This is a distinct concern from PRIVATE_MARKERS (private/secret
# content) and is never merged into it.
GENERATED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode", ".tox",
}

# ponytail: no reusable file-size bound exists for a full-tree scan
# (context_acquisition._read_text's 120_000-char limit is a per-file text
# truncation for a small fixed doctrine list, not a scan-scope bound) - one
# conservative named constant. Oversized files are still hashed into
# scan_scope_digest (a content change is still detected) but are skipped for
# symbol/import/doc-claim extraction, recorded honestly in unknowns.
MAX_SCAN_FILE_BYTES = 2_000_000

# A tracked file that git's index still lists but that no longer exists in
# the working tree (deleted without `git rm`) still participates in
# scan_scope_digest - it is never silently excluded from the fingerprint,
# since "the file that should be here is gone" is itself a scan-scope-
# relevant fact. This sentinel is neither 64 hex chars nor a value
# hashlib.sha256 can ever produce, so it can never collide with a genuine
# content hash.
MISSING_TRACKED_SENTINEL = "MISSING_TRACKED"

# Read+hash+symlink-safety-check parallelism. Repository acquisition on this
# workspace is DrvFS/9P per-syscall-latency-bound, not CPU-bound (confirmed
# by the read-only performance investigation) - 4 workers materially cuts
# wall-clock time without contending for CPU cores.
_IO_WORKERS = 4

_TEST_DIR_MARKERS = ("tests/", "test/")


class RepositoryEvidenceError(RuntimeError):
    """Authorization or acquisition failure - never silently downgraded."""


@dataclass(frozen=True)
class Authorization:
    authorized_by: str
    authorization_note: str
    excluded_paths: tuple[str, ...] = ()


@dataclass
class RepositoryEvidencePack:
    pack_id: str
    authorized_repo_root: str
    authorization: dict[str, Any]
    contract_version: str
    workspace_identity: dict[str, Any]
    scan_scope_digest: str
    scan_paths: list[str]
    missing_tracked_files: list[str]
    languages: dict[str, int]
    manifests: list[dict[str, Any]]
    entrypoints: list[dict[str, Any]]
    modules: list[dict[str, Any]]
    symbols: list[dict[str, Any]]
    imports_graph: list[dict[str, Any]]
    test_files: list[dict[str, Any]]
    test_to_prod_links: list[dict[str, Any]]
    doc_claims: list[dict[str, Any]]
    contradiction_candidates: list[dict[str, Any]]
    dead_code_candidates: list[dict[str, Any]]
    unknowns: list[dict[str, Any]]
    provenance_index: dict[str, dict[str, Any]]
    generated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Hashing / Git identity
# ---------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _run_git(args: list[str], root: Path, timeout: int = 20) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        cp = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            text=True, capture_output=True, check=False, timeout=timeout, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, "", ""
    return cp.returncode, cp.stdout.strip(), cp.stderr.strip()


def git_identity(root: Path) -> tuple[str, str | None, str | None]:
    """("git"|"none", head, branch). Uses `git -C <root> rev-parse`, never
    `.git` directory existence, so a linked worktree (no local `.git` dir)
    or a nested non-root directory is still classified correctly."""
    code, out, _ = _run_git(["rev-parse", "--is-inside-work-tree"], root)
    if code != 0 or out != "true":
        return "none", None, None
    _, head, _ = _run_git(["rev-parse", "HEAD"], root)
    _, branch, _ = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], root)
    return "git", (head or None), (branch or None)


# ---------------------------------------------------------------------------
# Eligible-file enumeration (exclusion + symlink safety)
# ---------------------------------------------------------------------------

def _is_private_or_excluded(rel: str, excluded_paths: tuple[str, ...]) -> bool:
    if any(marker in rel for marker in PRIVATE_MARKERS):
        return True
    return any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in excluded_paths)


def _enumerate_via_walk(
    root: Path, authorization: Authorization,
) -> tuple[list[tuple[str, Path]], list[str], list[dict[str, Any]]]:
    """Deterministic, sorted (relpath, abspath) walk - the fallback used for
    a non-Git repository (or any repository where the Git fast path itself
    could not be trusted, see enumerate_eligible_files). This walk only ever
    sees what currently exists on disk, so it can never observe a
    tracked-but-deleted file itself; missing_tracked_files is always empty
    for this path.

    Symlinked directories are never followed, even when they resolve inside
    root (avoids both an escape and a circular-symlink walk); each one is
    explicitly inspected and recorded with a distinct reason for why it was
    not descended into. A symlinked file resolving outside root is refused
    and recorded, never read; one resolving inside root is treated as an
    ordinary in-scope file. Returns (eligible_files, missing_tracked_files, skipped_unknowns).
    """
    excluded_paths = authorization.excluded_paths
    eligible: list[tuple[str, Path]] = []
    skipped: list[dict[str, Any]] = []

    def walk(current: Path) -> None:
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name)
        except OSError:
            return
        for entry in entries:
            rel = entry.relative_to(root).as_posix()
            if entry.is_symlink() and entry.is_dir():
                try:
                    resolved_dir = entry.resolve(strict=True)
                    resolved_dir.relative_to(root)
                except (OSError, ValueError):
                    skipped.append({"path": rel, "reason": "symlink_dir_escape_refused"})
                else:
                    skipped.append({"path": rel, "reason": "symlink_dir_not_followed"})
                continue
            if entry.is_dir():
                name = entry.name
                if name in GENERATED_DIRS or _is_private_or_excluded(rel, excluded_paths):
                    continue
                walk(entry)
                continue
            if entry.is_symlink():
                try:
                    resolved_file = entry.resolve(strict=True)
                    resolved_file.relative_to(root)
                except (OSError, ValueError):
                    skipped.append({"path": rel, "reason": "symlink_file_escape_refused"})
                    continue
                target = resolved_file
            elif entry.is_file():
                target = entry
            else:
                continue
            if _is_private_or_excluded(rel, excluded_paths):
                continue
            eligible.append((rel, target))

    walk(root)
    eligible.sort(key=lambda item: item[0])
    return eligible, [], skipped


def _git_ls_files(root: Path, args: list[str]) -> list[str] | None:
    """NUL-safe `git ls-files -z <args>`, decoded as UTF-8 with
    surrogateescape for any non-UTF-8 byte (never raises on it). Returns
    None on any failure - git missing, not a work tree, non-zero exit,
    timeout - so the caller always has a safe "fall back to the walker"
    signal instead of a partial/ambiguous result."""
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        cp = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", "-C", str(root), "ls-files", "-z", *args],
            capture_output=True, check=False, timeout=60, env=env,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if cp.returncode != 0:
        return None
    return [p.decode("utf-8", errors="surrogateescape") for p in cp.stdout.split(b"\x00") if p]


def _git_candidate_paths(root: Path) -> tuple[set[str], set[str]] | None:
    """(all_candidates, tracked_candidates) relpaths, or None if root is not
    a usable Git work tree (triggers the walk fallback).

    all_candidates is the `--cached --others --exclude-standard` union in
    ONE combined invocation - confirmed by direct test that `--exclude-
    standard` only ever prunes `--others` entries, so a tracked file stays
    in scope even if a later .gitignore pattern would otherwise match it.
    tracked_candidates (`--cached` alone) is used only to classify a
    candidate later found missing from the working tree as MISSING_TRACKED
    (expected: `rm`'d without `git rm`) versus a genuine, fail-closed,
    unexpected disappearance of an untracked file. Git is used here purely
    for path enumeration - never trusted for content, identity, or symlink
    safety (see _check_symlink_safety)."""
    vcs, _, _ = git_identity(root)
    if vcs != "git":
        return None
    combined = _git_ls_files(root, ["--cached", "--others", "--exclude-standard"])
    if combined is None:
        return None
    tracked = _git_ls_files(root, ["--cached"])
    if tracked is None:
        return None
    return set(combined), set(tracked)


def _filtered_candidates(candidates: set[str], authorization: Authorization) -> list[str]:
    """Applies the same GENERATED_DIRS-by-directory-component and
    PRIVATE_MARKERS/excluded_paths rules the walk fallback applies per
    directory, but against a flat candidate-path set."""
    excluded_paths = authorization.excluded_paths
    kept = []
    for rel in candidates:
        parts = rel.split("/")
        if any(part in GENERATED_DIRS for part in parts[:-1]):
            continue
        if _is_private_or_excluded(rel, excluded_paths):
            continue
        kept.append(rel)
    return sorted(kept)


def _check_symlink_safety(
    root: Path, rel: str, cache: dict[str, bool], lock: threading.Lock,
) -> tuple[str, bool, str | None]:
    """(rel, exists, refusal_reason - None if safe). A REAL, unconditional
    filesystem inspection of every ancestor directory and the leaf path
    itself - Git's index file mode is NEVER trusted as proof of current
    symlink state, since a tracked regular file can be swapped for a
    symlink on disk without re-staging. Only the syscalls themselves are
    parallelized (see _check_all_symlink_safety) and ancestor-directory
    results are memoized (many candidates share a directory prefix) - every
    unique path is still actually stat()'d at least once, never skipped or
    inferred. Existence is folded into this same per-file check (rather
    than a second sequential pass afterward) - on this workspace's
    DrvFS/9P mount, a second per-file stat pass run sequentially on the
    main thread cost several extra seconds by itself in measurement."""
    parts = rel.split("/")
    cur = root
    for part in parts[:-1]:
        cur = cur / part
        key = str(cur)
        with lock:
            cached = cache.get(key)
        if cached is None:
            cached = cur.is_symlink()
            with lock:
                cache[key] = cached
        if cached:
            return rel, False, "symlink_dir_not_followed_or_escape"
    full = root / rel
    if full.is_symlink():
        is_dir_target = full.is_dir()  # follows the symlink to check target type
        try:
            resolved_file = full.resolve(strict=True)
            resolved_file.relative_to(root)
        except (OSError, ValueError):
            reason = "symlink_dir_escape_refused" if is_dir_target else "symlink_file_escape_refused"
            return rel, False, reason
        if is_dir_target:
            # Git lists an untracked symlink-to-directory as a leaf path (it
            # never descends into it) - the walk fallback's own "symlinked
            # directories are never followed" invariant applies identically
            # here: recorded and refused, never treated as an ordinary file.
            return rel, False, "symlink_dir_not_followed"
        return rel, True, None
    return rel, full.exists(), None


def _check_all_symlink_safety(
    root: Path, candidates: list[str],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Returns (existing_safe_rels, missing_safe_rels, skipped_unknowns)."""
    cache: dict[str, bool] = {}
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=_IO_WORKERS) as pool:
        results = list(pool.map(lambda rel: _check_symlink_safety(root, rel, cache, lock), candidates))
    existing: list[str] = []
    missing: list[str] = []
    skipped: list[dict[str, Any]] = []
    for rel, exists, reason in results:
        if reason is not None:
            skipped.append({"path": rel, "reason": reason})
        elif exists:
            existing.append(rel)
        else:
            missing.append(rel)
    return existing, missing, skipped


def _enumerate_via_git(
    root: Path, authorization: Authorization, git_sets: tuple[set[str], set[str]],
) -> tuple[list[tuple[str, Path]], list[str], list[dict[str, Any]]]:
    all_candidates, tracked = git_sets
    filtered = _filtered_candidates(all_candidates, authorization)
    existing_rels, missing_rels, skipped = _check_all_symlink_safety(root, filtered)

    eligible = sorted(((rel, root / rel) for rel in existing_rels), key=lambda item: item[0])
    missing_tracked: list[str] = []
    for rel in missing_rels:
        if rel in tracked:
            missing_tracked.append(rel)
        else:
            # An --others (untracked) candidate that vanished between the
            # Git enumeration and this check is a genuine TOCTOU race, not
            # the expected "deleted without git rm" case - recorded
            # honestly, never silently dropped.
            skipped.append({"path": rel, "reason": "untracked_path_vanished_before_read"})

    return eligible, sorted(missing_tracked), skipped


def enumerate_eligible_files(
    root: Path, authorization: Authorization,
) -> tuple[list[tuple[str, Path]], list[str], list[dict[str, Any]]]:
    """Returns (eligible_files, missing_tracked_files, skipped_unknowns).

    eligible_files: sorted (relpath, abspath) pairs for files that exist,
    passed exclusion + real symlink-safety checks. missing_tracked_files:
    sorted relpaths that Git's index still tracks but that no longer exist
    in the working tree (see MISSING_TRACKED_SENTINEL) - always empty for a
    non-Git repository, since the walk fallback can only ever see what is
    actually present on disk. skipped_unknowns: symlink refusals and other
    honestly-recorded gaps.

    Tries a Git-index-based fast path first (see _git_candidate_paths) and
    falls back to the exact original recursive filesystem walk
    (_enumerate_via_walk) for a non-Git repository or if the fast path
    itself could not be trusted. Git is used ONLY for path enumeration in
    the fast path - content identity and symlink safety are always
    re-verified directly against the filesystem, never inferred from Git.
    """
    root = root.resolve()
    git_sets = _git_candidate_paths(root)
    if git_sets is not None:
        return _enumerate_via_git(root, authorization, git_sets)
    return _enumerate_via_walk(root, authorization)


def scan_scope_digest(files: list[tuple[str, str]]) -> str:
    """files: (relpath, content_sha256_or_MISSING_TRACKED_SENTINEL) pairs -
    order-independent. A tracked-but-deleted file's sentinel entry
    participates here exactly like a real content hash would - it is never
    excluded from the fingerprint, so present<->deleted<->restored
    transitions are always detected as a scope change."""
    return _sha256_bytes(
        "\n".join(f"{rel}:{content_hash}" for rel, content_hash in sorted(files)).encode("utf-8")
    )


@dataclass
class _FileReadResult:
    rel: str
    content_hash: str | None  # None only on a genuine post-symlink-check OSError (TOCTOU race) - fail closed, never silently skipped.
    size: int
    oversized: bool
    is_binary: bool
    text: str | None  # populated only when not oversized and not binary


def _read_and_classify(root: Path, rel: str) -> _FileReadResult:
    """ONE open+full-read per file, reused for content hash, size, binary
    detection, and text decode - never a second read of the same file
    (confirmed by the read-only performance investigation to be the single
    largest avoidable cost: the previous implementation opened each file up
    to three separate times)."""
    path = root / rel
    try:
        data = path.read_bytes()
    except OSError:
        return _FileReadResult(rel, None, 0, False, False, None)
    content_hash = hashlib.sha256(data).hexdigest()
    size = len(data)
    if size > MAX_SCAN_FILE_BYTES:
        return _FileReadResult(rel, content_hash, size, True, False, None)
    is_binary = b"\x00" in data[:8192]
    text = None if is_binary else data.decode("utf-8", errors="replace")
    return _FileReadResult(rel, content_hash, size, False, is_binary, text)


def _read_and_classify_all(root: Path, eligible: list[tuple[str, Path]]) -> list[_FileReadResult]:
    """ThreadPoolExecutor(4)-parallelized - I/O-bound blocking reads on this
    workspace's DrvFS/9P mount, not CPU-bound (confirmed by benchmark).
    pool.map preserves input order, and eligible is already sorted, so the
    result order is deterministic."""
    with ThreadPoolExecutor(max_workers=_IO_WORKERS) as pool:
        return list(pool.map(lambda item: _read_and_classify(root, item[0]), eligible))


# ---------------------------------------------------------------------------
# Python module/import resolution
# ---------------------------------------------------------------------------

def _module_name(rel: str) -> str | None:
    if not rel.endswith(".py"):
        return None
    parts = rel[: -len(".py")].split("/")
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def _resolve_module(module: str, module_index: dict[str, str]) -> str | None:
    if module in module_index:
        return module_index[module]
    probe = module
    while "." in probe:
        probe = probe.rsplit(".", 1)[0]
        if probe in module_index:
            return module_index[probe]
    return None


def _resolve_import_target(
    rel: str, node: ast.Import | ast.ImportFrom, module_index: dict[str, str],
) -> list[tuple[str, str]]:
    """Returns [(raw_target, resolved_module_or_'')] for every name this
    import statement could plausibly reference in-scope. Handles absolute
    imports and relative imports (node.level); relative-import package
    resolution always walks the raw, full-path-derived module tree (see
    _module_name/_build_module_index) since "." / ".." are about physical
    directory nesting, never about the src/-stripped alias."""
    importing_module = _module_name(rel) or ""
    is_init = Path(rel).name == "__init__.py"
    base_parts = importing_module.split(".") if importing_module else []
    package_parts = base_parts if is_init else base_parts[:-1]

    results: list[tuple[str, str]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            results.append((alias.name, alias.name))
        return results

    # ast.ImportFrom: "from BASE import NAME" may reference BASE itself
    # (e.g. attributes defined in BASE/__init__.py) or the submodule
    # BASE.NAME (e.g. BASE/NAME.py) - both are real candidates and both are
    # tried; a plain `_resolve_module(node.module, ...)` call alone (the
    # earlier, buggy version of this function) silently resolved
    # `from pkg import submodule` to pkg/__init__.py and never even tried
    # pkg/submodule.py.
    if node.level and node.level > 0:
        up = node.level - 1
        target_package = package_parts[: len(package_parts) - up] if up else package_parts
        base = ".".join(target_package + ([node.module] if node.module else []))
    else:
        base = node.module or ""

    if base:
        results.append((base, base))
    for alias in node.names:
        submodule = f"{base}.{alias.name}" if base else alias.name
        raw_label = f"{'.' * (node.level or 0)}{node.module or ''}.{alias.name}" if node.level else submodule
        results.append((raw_label, submodule))
    return results


def _build_module_index(parsed: dict[str, ast.Module]) -> dict[str, str]:
    """Maps every resolvable dotted module name to its source file.

    Every parsed file always gets its raw, full-path-derived name (e.g.
    "src.core.parser" for src/core/parser.py) - this is always correct and
    needs no guessing about layout. In addition, a file that lives under a
    conventional top-level "src/" directory also gets a stripped alias
    (e.g. "core.parser"), because a real PEP 517 src-layout adds src/
    itself to sys.path, so code imports it as "core.parser", never
    "src.core.parser" - and a pyproject.toml script target like
    "pkg.cli:main" is written against that same stripped form.

    Both forms live in one flat index built once, so no call site needs a
    "try candidate, then retry with a guessed prefix" fallback anywhere -
    resolution is always a single direct lookup. Whether src/ is stripped
    for a given file is decided per-file, purely from that file's own path
    prefix - never by requiring every module in the whole repository to
    share one common top-level root, which is what silently broke this
    when a repository also has an unrelated top-level tests/ directory (a
    completely normal layout: tests/ is not, and must not be required to
    be, under src/).
    """
    index: dict[str, str] = {}
    for rel in parsed:
        raw = _module_name(rel)
        if raw:
            index[raw] = rel
    for rel in parsed:
        if not rel.startswith("src/"):
            continue
        raw = _module_name(rel)
        if not raw or not raw.startswith("src."):
            continue
        stripped = raw[len("src."):]
        if stripped and stripped not in index:
            index[stripped] = rel
    return index


# ---------------------------------------------------------------------------
# Manifest entrypoints (pyproject.toml [project.scripts] / poetry scripts)
# ---------------------------------------------------------------------------

def _manifest_script_entries(text: dict[str, Any]) -> dict[str, str]:
    scripts: dict[str, str] = {}
    project_scripts = text.get("project", {}).get("scripts")
    if isinstance(project_scripts, dict):
        scripts.update({k: v for k, v in project_scripts.items() if isinstance(v, str)})
    poetry_scripts = (
        text.get("tool", {}).get("poetry", {}).get("scripts")
        if isinstance(text.get("tool"), dict) else None
    )
    if isinstance(poetry_scripts, dict):
        scripts.update({k: v for k, v in poetry_scripts.items() if isinstance(v, str)})
    return scripts


def _find_manifest_key_line(raw_text: str, key: str) -> int:
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=", re.MULTILINE)
    match = pattern.search(raw_text)
    if not match:
        return 1
    return raw_text.count("\n", 0, match.start()) + 1


# ---------------------------------------------------------------------------
# Acquisition
# ---------------------------------------------------------------------------

def acquire_repo_evidence(
    repo_root: Path, authorization: Authorization,
) -> RepositoryEvidencePack:
    """Deterministic, model-free. Same code path for Konoha's own repo or
    any other authorized local repository - no special self-inspection
    branch. Never writes into repo_root. Fails closed (raises
    RepositoryEvidenceError) rather than silently narrowing scan scope if
    any in-scope, non-excluded, non-symlink-refused file cannot be hashed -
    this keeps scan_paths/scan_scope_digest and is_evidence_current()
    using exactly the same notion of scan scope by construction."""
    root = repo_root.resolve()
    if not root.is_dir():
        raise RepositoryEvidenceError(f"authorized_repo_root is not a directory: {root}")

    eligible, missing_tracked, symlink_skips = enumerate_eligible_files(root, authorization)

    unknowns: list[dict[str, Any]] = list(symlink_skips)
    for rel in missing_tracked:
        unknowns.append({"path": rel, "reason": "tracked_path_deleted_in_worktree"})
    provenance_index: dict[str, dict[str, Any]] = {}
    languages: dict[str, int] = {}
    manifests: list[dict[str, Any]] = []
    doc_claims: list[dict[str, Any]] = []
    py_sources: dict[str, str] = {}
    file_hash: dict[str, str] = {}
    scanned: list[tuple[str, str]] = [(rel, MISSING_TRACKED_SENTINEL) for rel in missing_tracked]
    manifest_raw_text: dict[str, str] = {}

    def next_ref() -> str:
        return f"prov-{len(provenance_index):04d}"

    _MANIFEST_NAMES = {
        "pyproject.toml": "python", "setup.py": "python", "setup.cfg": "python",
        "requirements.txt": "python", "package.json": "node", "Cargo.toml": "rust",
        "go.mod": "go",
    }

    read_results = _read_and_classify_all(root, eligible)
    for r in read_results:
        rel = r.rel
        if r.content_hash is None:
            raise RepositoryEvidenceError(f"could not read in-scope file: {rel}")

        content_hash = r.content_hash
        file_hash[rel] = content_hash
        scanned.append((rel, content_hash))

        ext = Path(rel).suffix or "(none)"
        languages[ext] = languages.get(ext, 0) + 1

        name = Path(rel).name
        if name in _MANIFEST_NAMES:
            manifests.append({"path": rel, "kind": _MANIFEST_NAMES[name]})

        if r.oversized:
            unknowns.append({"path": rel, "reason": "oversized_skipped_for_extraction"})
            continue

        if r.is_binary:
            unknowns.append({"path": rel, "reason": "binary_skipped_for_extraction"})
            continue

        text = r.text
        if rel.endswith(".py"):
            py_sources[rel] = text
        elif rel.endswith(".toml") and name == "pyproject.toml":
            manifest_raw_text[rel] = text
        elif rel.endswith(".md"):
            for lineno, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if "`" in stripped or "--" in stripped:
                    ref = next_ref()
                    provenance_index[ref] = {
                        "path": rel, "line_start": lineno, "line_end": lineno,
                        "content_sha256": content_hash, "extraction_method": "regex",
                    }
                    doc_claims.append({"path": rel, "line": lineno, "statement": stripped, "evidence_ref": ref})

    # --- Parse every Python source once ---
    parsed: dict[str, ast.Module] = {}
    for rel, text in py_sources.items():
        try:
            parsed[rel] = ast.parse(text, filename=rel)
        except SyntaxError:
            unknowns.append({"path": rel, "reason": "python_syntax_error_unparseable"})

    module_index = _build_module_index(parsed)

    # --- Symbols + __main__ entrypoints ---
    symbols: list[dict[str, Any]] = []
    entrypoints: list[dict[str, Any]] = []
    for rel, tree in parsed.items():
        content_hash = file_hash[rel]
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                ref = next_ref()
                provenance_index[ref] = {
                    "path": rel, "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "content_sha256": content_hash, "extraction_method": "ast",
                }
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                symbols.append({"path": rel, "name": node.name, "kind": kind, "line": node.lineno, "evidence_ref": ref})
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
                and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)
                and len(node.test.comparators) == 1
                and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "__main__"
            ):
                ref = next_ref()
                provenance_index[ref] = {
                    "path": rel, "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno),
                    "content_sha256": content_hash, "extraction_method": "ast",
                }
                entrypoints.append({
                    "path": rel, "reason": "if __name__ == \"__main__\"",
                    "evidence_ref": ref, "resolved_path": rel, "target_evidence_ref": ref,
                })

    # --- Manifest-declared entrypoints (pyproject.toml scripts) ---
    # A manifest declaration is always kept as evidence (the entry exists in
    # pyproject.toml, proven by evidence_ref) - but resolved_path is only
    # ever set to a real file when the target module is actually present in
    # scan scope, and (when the target names "module:symbol") only when
    # that exact top-level symbol is actually defined there. A module that
    # resolves but whose named symbol doesn't exist is NOT labeled a proven
    # entrypoint - resolved_path/target_evidence_ref stay None and the gap
    # is recorded honestly in unknowns, per source-evidence requirement.
    symbol_ref_by_path_name: dict[tuple[str, str], str] = {
        (sym["path"], sym["name"]): sym["evidence_ref"] for sym in symbols
    }
    for rel, raw_text in manifest_raw_text.items():
        try:
            data = tomllib.loads(raw_text)
        except tomllib.TOMLDecodeError:
            unknowns.append({"path": rel, "reason": "toml_unparseable"})
            continue
        for script_name, target in _manifest_script_entries(data).items():
            if ":" in target:
                module_target, symbol_name = target.split(":", 1)
            else:
                module_target, symbol_name = target, None

            # Exact match only - not _resolve_module's parent-walk fallback.
            # That fallback exists for import statements, where partially
            # resolving "pkg.deep.sub" to "pkg/__init__.py" is legitimate
            # (an attribute, not a submodule file, can live there). A
            # manifest script target names one specific module; silently
            # accepting an unrelated parent package as a match would hide
            # a real "this module does not exist" condition behind a
            # confusing symbol-not-found message instead.
            resolved = module_index.get(module_target)
            target_ref: str | None = None
            if resolved is None:
                unknowns.append({
                    "path": rel,
                    "reason": (
                        f"manifest_entrypoint_target_unresolved: {script_name} -> {target} "
                        f"(module '{module_target}' not found in scan scope)"
                    ),
                })
            elif symbol_name:
                target_ref = symbol_ref_by_path_name.get((resolved, symbol_name))
                if target_ref is None:
                    unknowns.append({
                        "path": rel,
                        "reason": (
                            f"manifest_entrypoint_target_unresolved: {script_name} -> {target} "
                            f"(symbol '{symbol_name}' not found in {resolved})"
                        ),
                    })
                    resolved = None

            line = _find_manifest_key_line(raw_text, script_name)
            ref = next_ref()
            provenance_index[ref] = {
                "path": rel, "line_start": line, "line_end": line,
                "content_sha256": file_hash[rel], "extraction_method": "manifest_parse",
            }
            entrypoints.append({
                "path": rel, "reason": f"pyproject.toml script '{script_name}' -> {target}",
                "evidence_ref": ref, "resolved_path": resolved, "target_evidence_ref": target_ref,
            })

    # --- Import graph ---
    # A candidate is only worth attempting to resolve at all when its own
    # top-level component is not definitively stdlib (sys.stdlib_module_names
    # is exact and needs no guessing). module_index already contains both
    # the raw and the src/-stripped-alias form of every local module (see
    # _build_module_index), so a single direct _resolve_module lookup is
    # always enough here - no per-call-site prefix-retry. A genuine
    # third-party import (e.g. "requests") that resolves to nothing is
    # honestly recorded in unknowns as unresolved, per source evidence
    # requirement, rather than guessed away.
    def _worth_resolving(candidate: str) -> bool:
        top = candidate.split(".", 1)[0]
        return top not in sys.stdlib_module_names

    imports_graph: list[dict[str, Any]] = []
    fan_in: dict[str, int] = {rel: 0 for rel in parsed}
    fan_out: dict[str, int] = {rel: 0 for rel in parsed}
    for rel, tree in parsed.items():
        content_hash = file_hash[rel]
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            seen_targets: set[str] = set()
            for raw_target, candidate in _resolve_import_target(rel, node, module_index):
                if not candidate or not _worth_resolving(candidate):
                    continue
                resolved = _resolve_module(candidate, module_index)
                if resolved is None:
                    unknowns.append({"path": rel, "reason": f"unresolved_import:{raw_target}"})
                    continue
                if resolved == rel or resolved in seen_targets:
                    continue
                seen_targets.add(resolved)
                ref = next_ref()
                provenance_index[ref] = {
                    "path": rel, "line_start": node.lineno, "line_end": node.lineno,
                    "content_sha256": content_hash, "extraction_method": "ast",
                }
                imports_graph.append({"from_path": rel, "to_path": resolved, "evidence_ref": ref})
                fan_out[rel] = fan_out.get(rel, 0) + 1
                fan_in[resolved] = fan_in.get(resolved, 0) + 1

    # --- Modules / test files / test-to-prod links ---
    modules: list[dict[str, Any]] = []
    test_files: list[dict[str, Any]] = []
    for rel in parsed:
        ref = next_ref()
        provenance_index[ref] = {
            "path": rel, "line_start": 1, "line_end": 1,
            "content_sha256": file_hash[rel], "extraction_method": "ast",
        }
        modules.append({"path": rel, "fan_in": fan_in.get(rel, 0), "fan_out": fan_out.get(rel, 0), "evidence_ref": ref})
        lower = f"/{rel}"
        if any(marker in lower for marker in _TEST_DIR_MARKERS) or Path(rel).name.startswith("test_"):
            test_files.append({"path": rel, "evidence_ref": ref})

    imports_by_source: dict[str, list[str]] = {}
    for edge in imports_graph:
        imports_by_source.setdefault(edge["from_path"], []).append(edge["to_path"])
    test_paths = {t["path"] for t in test_files}
    test_to_prod_links: list[dict[str, Any]] = []
    for test in test_files:
        for target in imports_by_source.get(test["path"], []):
            if target not in test_paths:
                test_to_prod_links.append({
                    "test_path": test["path"], "prod_path": target,
                    "basis": "imports", "evidence_ref": test["evidence_ref"],
                })

    # --- Dead-code candidates: AST-level usage count (same-file included) ---
    usage_counts: dict[str, int] = {}
    for tree in parsed.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                usage_counts[node.id] = usage_counts.get(node.id, 0) + 1
            elif isinstance(node, ast.Attribute):
                usage_counts[node.attr] = usage_counts.get(node.attr, 0) + 1

    dead_code_candidates: list[dict[str, Any]] = []
    for sym in symbols:
        if sym["kind"] not in {"function", "class"}:
            continue
        if sym["path"] in test_paths:
            # ponytail: a test function is invoked by discovery, not by
            # reference, so "no incoming reference" is a guaranteed false
            # positive here, not a dead-code signal - excluded rather than
            # reported as a misleading candidate.
            continue
        if fan_in.get(sym["path"], 0) > 0:
            continue
        # usage_counts includes the definition's own Name/Attribute nodes
        # only if referenced elsewhere as a Load/Attribute - the def
        # statement itself binds the name via Store, never counted here.
        if usage_counts.get(sym["name"], 0) == 0:
            dead_code_candidates.append({
                "path": sym["path"], "symbol": sym["name"],
                "basis": "no_incoming_import_edge_and_no_ast_reference_found",
                "evidence_ref": sym["evidence_ref"],
            })

    # --- Doc-vs-source contradiction candidates ---
    all_py_text = "\n".join(py_sources.values())
    contradiction_candidates: list[dict[str, Any]] = []
    for claim in doc_claims:
        for token in re.findall(r"`([^`]+)`", claim["statement"]):
            bare = token.lstrip("-")
            if bare and bare not in all_py_text:
                contradiction_candidates.append({
                    "doc_claim_ref": claim["evidence_ref"],
                    "conflicting_source_ref": None,
                    "basis": f"doc references `{token}`, not found in any scanned Python source",
                })

    vcs, head, branch = git_identity(root)
    digest = scan_scope_digest(scanned)
    repo_root_id = _sha256_bytes(str(root).encode("utf-8"))
    pack_id = _sha256_bytes(
        f"{repo_root_id}|{head or 'none'}|{digest}|{CONTRACT_VERSION}".encode("utf-8")
    )[:32]

    return RepositoryEvidencePack(
        pack_id=pack_id,
        authorized_repo_root=str(root),
        authorization={
            "authorized_by": authorization.authorized_by,
            "authorization_note": authorization.authorization_note,
            "excluded_paths": list(authorization.excluded_paths),
        },
        contract_version=CONTRACT_VERSION,
        workspace_identity={"repo_root_id": repo_root_id, "vcs": vcs, "head": head, "branch": branch},
        scan_scope_digest=digest,
        scan_paths=sorted(rel for rel, _ in scanned),
        missing_tracked_files=sorted(missing_tracked),
        languages=languages,
        manifests=manifests,
        entrypoints=entrypoints,
        modules=modules,
        symbols=symbols,
        imports_graph=imports_graph,
        test_files=test_files,
        test_to_prod_links=test_to_prod_links,
        doc_claims=doc_claims,
        contradiction_candidates=contradiction_candidates,
        dead_code_candidates=dead_code_candidates,
        unknowns=unknowns,
        provenance_index=provenance_index,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def is_evidence_current(pack: RepositoryEvidencePack, repo_root: Path) -> bool:
    """Recomputes the identical scan scope fresh, via the same
    enumerate_eligible_files() used at acquisition time (Git fast path or
    walk fallback, symlink-safety-checked identically either way), so
    acquisition and freshness checking can never diverge on what "in scope"
    means. False on: any present file's content changing, a present file
    becoming tracked-but-missing or vice versa (both change the
    MISSING_TRACKED-sentinel-inclusive fingerprint - see scan_scope_digest),
    a new eligible file appearing, the eligible/excluded set changing, HEAD
    changing, or the acquisition contract version changing. A
    tracked-but-missing file that is still tracked-but-missing contributes
    the identical sentinel both times, so that case alone is correctly
    treated as unchanged."""
    if pack.contract_version != CONTRACT_VERSION:
        return False
    root = repo_root.resolve()
    authorization = Authorization(
        authorized_by=pack.authorization.get("authorized_by", ""),
        authorization_note=pack.authorization.get("authorization_note", ""),
        excluded_paths=tuple(pack.authorization.get("excluded_paths", ())),
    )
    try:
        eligible, missing_tracked, _ = enumerate_eligible_files(root, authorization)
    except OSError:
        return False
    current_rels = sorted([rel for rel, _ in eligible] + missing_tracked)
    if current_rels != sorted(pack.scan_paths):
        return False

    scanned: list[tuple[str, str]] = [(rel, MISSING_TRACKED_SENTINEL) for rel in missing_tracked]
    for r in _read_and_classify_all(root, eligible):
        if r.content_hash is None:
            return False
        scanned.append((r.rel, r.content_hash))
    if scan_scope_digest(scanned) != pack.scan_scope_digest:
        return False

    vcs, head, _ = git_identity(root)
    return vcs == pack.workspace_identity.get("vcs") and head == pack.workspace_identity.get("head")


# ---------------------------------------------------------------------------
# Bounded evidence view - the one materialization path shared by the planner
# (embedded in the Codex planning context) and the executor (embedded in a
# worker's resolved_source_bundle for repository_state), so neither ever
# needs its own serializer for this pack.
# ---------------------------------------------------------------------------

DEFAULT_BOUNDED_VIEW_LIMITS: dict[str, int] = {
    "manifests": 20,
    "entrypoints": 20,
    "modules": 30,
    "symbols": 50,
    "imports_graph": 50,
    "test_to_prod_links": 30,
    "contradiction_candidates": 20,
    "dead_code_candidates": 20,
    "doc_claims": 10,
    "unknowns": 20,
}

_REF_KEYS = ("evidence_ref", "doc_claim_ref", "conflicting_source_ref", "target_evidence_ref", "resolved_path")


def _collect_refs(item: Any, into: set[str]) -> None:
    if not isinstance(item, dict):
        return
    for key in _REF_KEYS:
        ref = item.get(key)
        if isinstance(ref, str) and ref.startswith("prov-"):
            into.add(ref)


def _bounded_collection(name: str, items: list, limits: dict[str, int], referenced_refs: set[str]) -> dict[str, Any]:
    """One collection's deterministic slice, in the exact shape every
    bounded collection in this view uses: total/included/truncated/items -
    never a bare list, so a consumer can never mistake a slice for the
    whole pack."""
    n = limits[name]
    sliced = list(items[:n])
    for item in sliced:
        _collect_refs(item, referenced_refs)
    return {
        "total": len(items),
        "included": len(sliced),
        "truncated": len(sliced) < len(items),
        "items": sliced,
    }


def bounded_evidence_view(
    pack: RepositoryEvidencePack, limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Deterministic, truncated view of a RepositoryEvidencePack, safe to
    embed in a planner or worker prompt payload.

    Every bounded collection uses the exact shape {total, included,
    truncated, items} - a consumer can never mistake a slice for the whole
    pack (honest truncation, per the bounded-payload requirement). No
    random or model-selected sampling: modules are ranked by
    (fan_in + fan_out) descending, then path, for a stable "most
    structurally central first" order; every other list takes a
    deterministic first-N slice in the pack's own stored order. Only the
    provenance_index entries actually referenced by included items are
    carried along - never the full index - so a worker citing an
    evidence_ref it was actually shown can resolve it, without the payload
    growing with the whole pack. scan_paths_total/missing_tracked_total/
    unknowns both expose overall coverage even where the detail list itself
    is bounded.
    """
    limits = {**DEFAULT_BOUNDED_VIEW_LIMITS, **(limits or {})}
    referenced_refs: set[str] = set()

    def bounded(name: str, items: list) -> dict[str, Any]:
        return _bounded_collection(name, items, limits, referenced_refs)

    ranked_modules = sorted(
        pack.modules, key=lambda m: (-(m["fan_in"] + m["fan_out"]), m["path"]),
    )

    view: dict[str, Any] = {
        "pack_id": pack.pack_id,
        "authorized_repo_root": pack.authorized_repo_root,
        "workspace_identity": dict(pack.workspace_identity),
        "languages": dict(pack.languages),
        "scan_paths_total": len(pack.scan_paths),
        "missing_tracked_total": len(pack.missing_tracked_files),
        "manifests": bounded("manifests", pack.manifests),
        "entrypoints": bounded("entrypoints", pack.entrypoints),
        "modules": bounded("modules", ranked_modules),
        "symbols": bounded("symbols", pack.symbols),
        "imports_graph": bounded("imports_graph", pack.imports_graph),
        "test_to_prod_links": bounded("test_to_prod_links", pack.test_to_prod_links),
        "contradiction_candidates": bounded("contradiction_candidates", pack.contradiction_candidates),
        "dead_code_candidates": bounded("dead_code_candidates", pack.dead_code_candidates),
        "doc_claims": bounded("doc_claims", pack.doc_claims),
        "unknowns": bounded("unknowns", pack.unknowns),
    }
    view["provenance"] = {
        ref: pack.provenance_index[ref] for ref in sorted(referenced_refs) if ref in pack.provenance_index
    }
    return view
