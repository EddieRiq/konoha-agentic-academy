from __future__ import annotations
import argparse
from pathlib import Path
from . import __version__
from .conversation import run

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="konoha", add_help=True)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    return run(Path(args.repo).resolve())
