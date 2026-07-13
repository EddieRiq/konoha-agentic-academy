#!/usr/bin/env python3
"""Run an isolated terminal-distribution smoke without network access."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

SCHEMA_VERSION = "1.0.0"
REPORT_TYPE = "konoha_clean_install_smoke_report"


class SmokeError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_output(repo_root: Path, raw: str) -> Path:
    sandbox = (repo_root / "sandbox").resolve()
    output = Path(raw)
    if not output.is_absolute():
        output = repo_root / output
    output = output.resolve()
    if not is_relative_to(output, sandbox):
        raise SmokeError("smoke output must stay under sandbox")
    return output


def run(
    command: Sequence[str],
    cwd: Path,
    *,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            text=True,
            capture_output=True,
            shell=False,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise SmokeError(
            f"smoke command timed out: {list(command)!r}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise SmokeError(
            f"smoke command failed RC={completed.returncode}: "
            f"{list(command)!r}: {detail or 'no output'}"
        )
    return completed


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def execute_smoke(
    repo_root: Path,
    *,
    expected_version: str,
) -> Dict[str, Any]:
    cli = repo_root / "tools" / "konoha_cli.py"
    if not cli.is_file():
        raise SmokeError("canonical CLI is missing")

    commands = []
    with tempfile.TemporaryDirectory(
        prefix="konoha-install-smoke-",
        dir=repo_root / "sandbox",
    ) as temp:
        root = Path(temp).resolve()
        venv = root / ".venv"

        run([sys.executable, "-m", "venv", str(venv)], repo_root)
        python = venv / "bin" / "python"
        if not python.is_file():
            raise SmokeError("isolated venv python is missing")

        wrapper = root / "bin" / "konoha"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text(
            "#!/usr/bin/env sh\n"
            f'exec env PYTHONDONTWRITEBYTECODE=1 '
            f'"{python}" "{cli}" "$@"\n',
            encoding="utf-8",
            newline="\n",
        )
        os.chmod(wrapper, 0o755)

        checks = [
            ("version", [str(wrapper), "--version"]),
            (
                "registry",
                [str(wrapper), "--validate-registry"],
            ),
            ("help", [str(wrapper), "--help"]),
            (
                "doctor_help",
                [str(wrapper), "doctor", "--help"],
            ),
            (
                "install_status_help",
                [str(wrapper), "install-status", "--help"],
            ),
            (
                "release_delivery_help",
                [str(wrapper), "release", "deliver", "--help"],
            ),
        ]

        outputs: Dict[str, Dict[str, Any]] = {}
        for label, command in checks:
            completed = run(command, repo_root)
            commands.append(command)
            outputs[label] = {
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }

        observed_version = outputs["version"]["stdout"].strip()
        if observed_version != expected_version:
            raise SmokeError(
                f"expected version {expected_version}, "
                f"found {observed_version}"
            )
        if "KONOHA COMMAND REGISTRY PASSED" not in (
            outputs["registry"]["stdout"]
        ):
            raise SmokeError("registry smoke marker missing")
        if "Konoha Agentic Academy CLI" not in (
            outputs["help"]["stdout"]
        ):
            raise SmokeError("CLI help marker missing")

        return {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "passed",
            "status_code": "CLEAN_INSTALL_SMOKE_PASSED",
            "expected_version": expected_version,
            "observed_version": observed_version,
            "checks": {
                label: True
                for label, _command in checks
            },
            "commands": commands,
            "boundaries": {
                "network_access": "blocked",
                "repository_mutation": "blocked",
                "git_operations": "blocked",
                "temporary_workspace": "sandbox_only",
                "cleanup": "automatic",
            },
            "authority": {
                "smoke_is_evidence_only": True,
                "smoke_does_not_authorize_release": True,
            },
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an isolated Konoha terminal install smoke."
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--expected-version", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        repo_root = Path(args.repo_root).resolve()
        output = resolve_output(repo_root, args.output)
        if output.exists() and not args.force:
            raise SmokeError("output exists; use --force")

        report = execute_smoke(
            repo_root,
            expected_version=args.expected_version,
        )
        write_json(output, report)

        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("KONOHA CLEAN INSTALL SMOKE PASSED")
            print(f"version: {report['observed_version']}")
            print(f"report: {output}")
        return 0

    except SmokeError as exc:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "report_type": REPORT_TYPE,
            "generated_at": utc_now(),
            "status": "blocked",
            "status_code": "BLOCKED_CLEAN_INSTALL_SMOKE",
            "blocker": str(exc),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("KONOHA CLEAN INSTALL SMOKE BLOCKED", file=sys.stderr)
            print(f"blocker: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
