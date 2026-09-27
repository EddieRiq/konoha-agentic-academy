"""Explicitly authorized local repository study, persistence and terminal use.

No remote acquisition, providers, application execution or patch application.
Run with ``python -m tools.repo_evidence.workflow --help``.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlsplit

from tools.teachback.manage_teachback import (
    TeachbackError, start_repository_teachback, respond_repository_teachback,
    validate_repository_teachback,
)
from .acquire_repo_evidence import (
    Authorization, RepositoryEvidenceError, acquire_repo_evidence, is_evidence_current,
    _run_git,
)
from .persistence import load_evidence_pack, persist_evidence_pack
from .study import build_repository_study, validate_repository_study, explain_repository_study


@dataclass(frozen=True)
class StudyAuthorization:
    authorized_repo_root: str
    authorized_by: str
    authorization_note: str
    public_repository: bool
    source_url: str | None = None

    def validate(self, repo: Path) -> None:
        if (self.public_repository is not True or self.authorized_by != "human"
                or not isinstance(self.authorization_note, str) or not self.authorization_note.strip()
                or len(self.authorization_note) > 2000
                or self.authorized_repo_root != str(repo.resolve())):
            raise RepositoryEvidenceError("explicit_public_repository_authorization_required")
        if self.source_url is not None:
            url = urlsplit(self.source_url)
            if (len(self.source_url) > 2000 or url.scheme != "https" or not url.hostname
                    or url.username or url.password or url.query or url.fragment):
                raise RepositoryEvidenceError("public_source_url_invalid")


def _session_dir(state_root: Path, study_id: str) -> Path:
    if not isinstance(study_id, str) or not re.fullmatch(r"study-[0-9a-f]{32}", study_id):
        raise RepositoryEvidenceError("study_id_invalid")
    root = state_root.resolve()
    child = root / study_id
    if child.is_symlink() or child.resolve().parent != root:
        raise RepositoryEvidenceError("study_state_path_unsafe")
    return child


def _check_state_location(repo: Path, state_root: Path) -> None:
    try:
        relative = state_root.resolve().relative_to(repo.resolve())
    except ValueError:
        return  # explicitly selected local state outside the studied repo
    if not relative.parts:
        raise RepositoryEvidenceError("study_state_must_be_private")
    code, _, _ = _run_git(["check-ignore", "-q", "--", relative.as_posix() + "/probe.json"], repo)
    if code != 0:
        raise RepositoryEvidenceError("study_state_must_be_ignored_or_outside_repository")


def _read_state(path: Path) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise RepositoryEvidenceError("study_state_not_regular")
            raw = stream.read(2_000_001)
        if len(raw) > 2_000_000:
            raise RepositoryEvidenceError("study_state_too_large")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (OSError, ValueError, RecursionError) as exc:
        raise RepositoryEvidenceError("study_state_unavailable") from exc


def _write_new(path: Path, value: dict) -> None:
    # Immutable projection/state origin; reentry never overwrites provenance.
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode()
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)


def start_study(repo: Path, authorization: StudyAuthorization, state_root: Path) -> dict:
    authorization.validate(repo)  # before any target evidence acquisition
    _check_state_location(repo, state_root)
    pack = acquire_repo_evidence(repo, Authorization(authorization.authorized_by, authorization.authorization_note))
    study = build_repository_study(pack)
    directory = _session_dir(state_root, study.study_id)
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    persist_evidence_pack(directory, pack)
    record = {"schema_version": "1.0.0", "authorization": asdict(authorization),
              "study": study.as_dict(), "teachback": start_repository_teachback(study)}
    path = directory / "study.json"
    try:
        _write_new(path, record)
    except FileExistsError:
        return load_study(repo, authorization, state_root, study.study_id)[0]
    return record


def load_study(repo: Path, authorization: StudyAuthorization, state_root: Path, study_id: str):
    authorization.validate(repo)
    _check_state_location(repo, state_root)
    directory = _session_dir(state_root, study_id)
    record = _read_state(directory / "study.json")
    if (set(record) != {"schema_version", "authorization", "study", "teachback"}
            or record["schema_version"] != "1.0.0" or record["authorization"] != asdict(authorization)
            or not isinstance(record["study"], dict)):
        raise RepositoryEvidenceError("study_authorization_or_record_mismatch")
    pack = load_evidence_pack(directory, record["study"].get("evidence_reference"))
    if pack.authorized_repo_root != str(repo.resolve()) or not is_evidence_current(pack, repo):
        raise RepositoryEvidenceError("repository_evidence_stale_new_study_required")
    study = validate_repository_study(record["study"], pack)
    if study.study_id != study_id:
        raise RepositoryEvidenceError("study_identity_mismatch")
    validate_repository_teachback(record["teachback"], study)
    return record, study, pack


def respond_to_study(repo: Path, authorization: StudyAuthorization, state_root: Path,
                     study_id: str, human_input: str, *, actor: str) -> dict:
    record, study, _ = load_study(repo, authorization, state_root, study_id)
    record["teachback"] = respond_repository_teachback(record["teachback"], study, human_input, actor=actor)
    directory = _session_dir(state_root, study_id)
    temporary = directory / "teachback-update.json"
    try:
        _write_new(temporary, record)
    except FileExistsError as exc:
        raise RepositoryEvidenceError("study_update_pending_human_reconciliation") from exc
    temporary.replace(directory / "study.json")
    return record


def recommend_study(repo: Path, authorization: StudyAuthorization, state_root: Path,
                    study_id: str, *, model_suggestions=None) -> dict:
    from .learning import self_improvement_recommendations
    record, study, pack = load_study(repo, authorization, state_root, study_id)
    return self_improvement_recommendations(study, pack, record["teachback"], model_suggestions)


def compare_studies(donor_repo: Path, donor_authorization: StudyAuthorization,
                    donor_state_root: Path, donor_study_id: str,
                    target_repo: Path, target_authorization: StudyAuthorization,
                    target_state_root: Path, target_study_id: str) -> dict:
    from .learning import donor_learning
    # Explicit authorization of both exact targets precedes either load.
    donor_authorization.validate(donor_repo)
    target_authorization.validate(target_repo)
    donor_record, donor, donor_pack = load_study(donor_repo, donor_authorization, donor_state_root, donor_study_id)
    target_record, target, target_pack = load_study(target_repo, target_authorization, target_state_root, target_study_id)
    return donor_learning(donor, donor_pack, donor_record["teachback"], target, target_pack,
                          target_record["teachback"], source_url=donor_authorization.source_url)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Local public repository study; no network or patch execution.")
    parser.add_argument("command", choices=("study", "explain", "respond", "recommend", "compare"))
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--authorize-repo", required=True, help="Exact absolute repository root explicitly authorized by the human.")
    parser.add_argument("--public", action="store_true", help="Human asserts this is an authorized public repository.")
    parser.add_argument("--authorization-note", required=True)
    parser.add_argument("--source-url", help="Optional human-declared public origin, not remotely verified.")
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--study-id")
    parser.add_argument("--category")
    parser.add_argument("--human-input", help="Exact human response; omitted means read one terminal line.")
    parser.add_argument("--target-repo", type=Path)
    parser.add_argument("--authorize-target-repo")
    parser.add_argument("--target-public", action="store_true")
    parser.add_argument("--target-authorization-note")
    parser.add_argument("--target-source-url")
    parser.add_argument("--target-state-root", type=Path)
    parser.add_argument("--target-study-id")
    args = parser.parse_args(argv)
    authorization = StudyAuthorization(args.authorize_repo, "human", args.authorization_note, args.public, args.source_url)
    try:
        if args.command == "study":
            record = start_study(args.repo, authorization, args.state_root)
            print(json.dumps(record, indent=2, ensure_ascii=False))
        elif args.command == "explain":
            _, study, _ = load_study(args.repo, authorization, args.state_root, args.study_id)
            print(explain_repository_study(study, args.category))
        elif args.command == "respond":
            human_input = args.human_input if args.human_input is not None else input("Human> ")
            record = respond_to_study(args.repo, authorization, args.state_root, args.study_id, human_input, actor="human")
            print(json.dumps(record["teachback"], indent=2))
        elif args.command == "recommend":
            print(json.dumps(recommend_study(args.repo, authorization, args.state_root, args.study_id), indent=2))
        else:
            if args.target_repo is None or args.target_state_root is None:
                raise RepositoryEvidenceError("explicit_comparison_target_required")
            target_authorization = StudyAuthorization(args.authorize_target_repo, "human", args.target_authorization_note,
                                                      args.target_public, args.target_source_url)
            report = compare_studies(args.repo, authorization, args.state_root, args.study_id,
                                     args.target_repo, target_authorization, args.target_state_root, args.target_study_id)
            print(json.dumps(report, indent=2))
        return 0
    except (RepositoryEvidenceError, TeachbackError, ValueError, OSError, EOFError) as exc:
        print(f"Repository study stopped: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
