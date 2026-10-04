from __future__ import annotations
import argparse
import sys
from pathlib import Path
from . import __version__
from .conversation import resume_mission, run

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="konoha", add_help=True)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--no-splash", action="store_true", help="Disable the interactive startup identity.")
    parser.add_argument("--no-color", action="store_true", help="Disable terminal colors.")
    parser.add_argument("command", nargs="?", choices=["shell"], help="Open the interactive shell explicitly.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--resume", metavar="MISSION_ID", default=None,
        help="Reanuda una misión existente por mission_id sin abrir una nueva conversación.",
    )
    mode_group.add_argument(
        "--plan-only", action="store_true",
        help=(
            "Planificación técnica supervisada: produce, valida y revisa un "
            "MissionPlan de forma determinística sin otorgar autoridad de "
            "ejecución ni ejecutar ninguna tarea."
        ),
    )
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    repo = Path(args.repo).resolve()
    if args.resume:
        return resume_mission(repo, args.resume)
    shell_requested = args.command == "shell"
    default_tty_entry = (
        not args.command and not args.plan_only
        and sys.stdin.isatty() and sys.stdout.isatty()
    )
    return run(
        repo,
        plan_only=args.plan_only,
        interactive_shell=shell_requested or default_tty_entry,
        no_splash=args.no_splash,
        no_color=args.no_color,
    )

if __name__ == "__main__":
    raise SystemExit(main())
