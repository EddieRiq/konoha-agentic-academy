from __future__ import annotations
import argparse
from pathlib import Path
from . import __version__
from .conversation import resume_mission, run

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="konoha", add_help=True)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--repo", default=".")
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
    return run(repo, plan_only=args.plan_only)

if __name__ == "__main__":
    raise SystemExit(main())
