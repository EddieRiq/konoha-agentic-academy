#!/usr/bin/env python3
"""Run the Konoha Local Web UI Alpha.

The UI is local-only by default and adds no new runtime authority.
It exposes mission/workspace/report/approval views over existing local files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local-only Konoha Web UI Alpha."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument(
        "--workspace-root",
        default="sandbox/workspace",
        help="Mission workspace root. Defaults to sandbox/workspace.",
    )
    parser.add_argument(
        "--sandbox-root",
        default="sandbox",
        help="Sandbox root. Defaults to sandbox.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help="Bind host. Defaults to 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Bind port. Defaults to 8765.",
    )
    parser.add_argument(
        "--allow-non-localhost",
        action="store_true",
        help="Allow binding to a non-localhost address. Disabled by default.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate UI dependencies and configuration, then exit.",
    )
    parser.add_argument("--json", action="store_true", help="Print self-test as JSON.")
    return parser


def validate_host(host: str, allow_non_localhost: bool) -> None:
    allowed = {"127.0.0.1", "localhost", "::1"}
    if host not in allowed and not allow_non_localhost:
        raise ValueError(
            "Local Web UI must bind to localhost by default. "
            "Use --allow-non-localhost only after explicit human approval."
        )


def dependency_status() -> dict:
    deps = {}
    for name in ("fastapi", "uvicorn", "jinja2"):
        try:
            __import__(name)
            deps[name] = "present"
        except Exception as exc:  # pragma: no cover - exact import errors vary
            deps[name] = f"missing: {exc}"
    return deps


def run_self_test(args: argparse.Namespace) -> int:
    try:
        validate_host(args.host, args.allow_non_localhost)
        deps = dependency_status()
        missing = {k: v for k, v in deps.items() if not v.startswith("present")}
        report = {
            "status": "passed" if not missing else "failed",
            "ui": "local_web_ui_alpha",
            "host": args.host,
            "port": args.port,
            "repo_root": str(Path(args.repo_root).resolve()),
            "workspace_root": str(Path(args.workspace_root).resolve()),
            "sandbox_root": str(Path(args.sandbox_root).resolve()),
            "dependencies": deps,
            "execution": "blocked",
            "filesystem_mutation": "workspace and sandbox reports only",
            "repository_apply": "blocked",
            "git_operations": "blocked",
            "private_context_access": "blocked",
            "real_model_invocation": "blocked",
            "network_access": "localhost_ui_only",
            "ui_adds_authority": False,
        }
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            if missing:
                print("LOCAL WEB UI SELF-TEST FAILED")
                for dep, status in missing.items():
                    print(f"Missing dependency: {dep}: {status}")
                print("Install with: python -m pip install fastapi uvicorn jinja2")
            else:
                print("LOCAL WEB UI SELF-TEST PASSED")
                print("Host:", args.host)
                print("Port:", args.port)
                print("Execution: blocked")
                print("Repository apply: blocked")
                print("Git operations: blocked")
                print("Private context access: blocked")
                print("Real model invocation: blocked")
                print("Network access: localhost UI only")
        return 0 if not missing else 2
    except Exception as exc:
        if args.json:
            print(json.dumps({"status": "failed", "blocker": str(exc)}, indent=2))
        else:
            print("LOCAL WEB UI SELF-TEST FAILED")
            print("Blocker:", exc)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test(args)

    try:
        validate_host(args.host, args.allow_non_localhost)
    except Exception as exc:
        print("LOCAL WEB UI FAILED")
        print("Blocker:", exc)
        return 1

    script_repo_root = _repo_root_from_script()
    if str(script_repo_root) not in sys.path:
        sys.path.insert(0, str(script_repo_root))

    try:
        import uvicorn
        from tools.ui_server.app import create_app
    except Exception as exc:
        print("LOCAL WEB UI FAILED")
        print("Blocker: missing UI dependency or import failure:", exc)
        print("Install with: python -m pip install fastapi uvicorn jinja2")
        return 2

    app = create_app(
        repo_root=Path(args.repo_root).resolve(),
        workspace_root=Path(args.workspace_root).resolve(),
        sandbox_root=Path(args.sandbox_root).resolve(),
    )

    print("LOCAL WEB UI STARTING")
    print(f"URL: http://{args.host}:{args.port}")
    print("Execution: blocked")
    print("Repository apply: blocked")
    print("Git operations: blocked")
    print("Private context access: blocked")
    print("Real model invocation: blocked")
    print("Network access: localhost UI only")

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
