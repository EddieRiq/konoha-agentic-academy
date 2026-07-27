from __future__ import annotations
import argparse
from pathlib import Path
from . import __version__
from .conversation import resume_mission, run

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="konoha", add_help=True)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--repo", default=".")
    parser.add_argument(
        "--resume", metavar="MISSION_ID", default=None,
        help="Reanuda una misión existente por mission_id sin abrir una nueva conversación.",
    )
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    repo = Path(args.repo).resolve()
    if args.resume:
        return resume_mission(repo, args.resume)
    return run(repo)

if __name__ == "__main__":
    raise SystemExit(main())
