#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, re, tomllib
from pathlib import Path

class VersionContractError(RuntimeError):
    pass

def read_runtime_version(path: Path) -> tuple[str, str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in {"VERSION", "TAG"}:
                if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
                    raise VersionContractError(f"{name} must be a string")
                values[name] = node.value.value
    if set(values) != {"VERSION", "TAG"}:
        raise VersionContractError("tools/version.py must define VERSION and TAG")
    return values["VERSION"], values["TAG"]

def inspect(root: Path) -> dict:
    root = root.resolve()
    package_version = tomllib.loads((root/"pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    runtime_version, runtime_tag = read_runtime_version(root/"tools/version.py")
    text = (root/"scripts/install.sh").read_text(encoding="utf-8")
    match = re.search(r'(?m)^VERSION="(v\d+\.\d+\.\d+)"$', text)
    if not match:
        raise VersionContractError("scripts/install.sh VERSION is missing")
    installer_tag = match.group(1)
    expected_tag = f"v{package_version}"
    errors = []
    if runtime_version != package_version:
        errors.append(f"runtime_version={runtime_version} != package_version={package_version}")
    if runtime_tag != expected_tag:
        errors.append(f"runtime_tag={runtime_tag} != expected_tag={expected_tag}")
    if installer_tag != expected_tag:
        errors.append(f"installer_tag={installer_tag} != expected_tag={expected_tag}")
    return {
        "schema_version":"1.0.0",
        "report_type":"konoha_version_contract",
        "status":"passed" if not errors else "failed",
        "values":{
            "package_version":package_version,
            "runtime_version":runtime_version,
            "runtime_tag":runtime_tag,
            "installer_tag":installer_tag,
            "expected_tag":expected_tag,
        },
        "errors":errors,
    }

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",default=".")
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args()
    report=inspect(Path(args.repo_root))
    if args.json:
        print(json.dumps(report,indent=2,sort_keys=True))
    else:
        print("KONOHA VERSION CONTRACT")
        for k,v in report["values"].items():
            print(f"{k}: {v}")
        print(f"status: {report['status']}")
        for e in report["errors"]:
            print(f"error: {e}")
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":
    raise SystemExit(main())
