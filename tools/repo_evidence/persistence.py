"""Content-addressed storage for the exact evidence approved in a plan.

Loading never acquires evidence. The approved reference binds the full payload,
not just a working-tree digest or a generated summary.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import fields
from pathlib import Path

from .acquire_repo_evidence import RepositoryEvidencePack, RepositoryEvidenceError

MAX_PACK_BYTES = 50_000_000


def _encoded(pack: RepositoryEvidencePack) -> bytes:
    return json.dumps(pack.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def evidence_reference(pack: RepositoryEvidencePack) -> dict[str, str]:
    return {"pack_id": pack.pack_id, "sha256": hashlib.sha256(_encoded(pack)).hexdigest()}


def _path(mission_dir: Path, reference: dict) -> Path:
    if (not isinstance(reference, dict) or set(reference) != {"pack_id", "sha256"}
            or not isinstance(reference["pack_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", reference["pack_id"])
            or not isinstance(reference["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])):
        raise RepositoryEvidenceError("repository_evidence_reference_invalid")
    return mission_dir / ("repository-evidence-" + reference["sha256"] + ".json")


def persist_evidence_pack(mission_dir: Path, pack: RepositoryEvidencePack) -> dict[str, str]:
    reference = evidence_reference(pack)
    payload = _encoded(pack)
    if len(payload) > MAX_PACK_BYTES:
        raise RepositoryEvidenceError("repository_evidence_pack_too_large")
    path = _path(mission_dir, reference)
    mission_dir.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError:
        # Idempotence is allowed only for identical bytes. Never overwrite.
        load_evidence_pack(mission_dir, reference)
    else:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    return reference


def load_evidence_pack(mission_dir: Path, reference: dict) -> RepositoryEvidencePack:
    path = _path(mission_dir, reference)
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as stream:
            import stat
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise RepositoryEvidenceError("repository_evidence_pack_invalid")
            raw = stream.read(MAX_PACK_BYTES + 1)
        if len(raw) > MAX_PACK_BYTES or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise RepositoryEvidenceError("repository_evidence_integrity_failed")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or set(payload) != {f.name for f in fields(RepositoryEvidencePack)}:
            raise RepositoryEvidenceError("repository_evidence_pack_invalid")
        pack = RepositoryEvidencePack(**payload)
        if pack.pack_id != reference["pack_id"]:
            raise RepositoryEvidenceError("repository_evidence_identity_mismatch")
        return pack
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise RepositoryEvidenceError("repository_evidence_pack_unavailable") from exc
