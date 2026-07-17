from __future__ import annotations
import hashlib, json, threading
from pathlib import Path
from typing import Callable

SUPPORTED = {".md", ".txt", ".pdf", ".tex"}

def scan_authorized_sources(config_path: Path, state_dir: Path) -> dict:
    if not config_path.exists():
        return {"status": "not_configured", "new_sources": []}
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest_path = state_dir / "sources" / "manifest.json"
    previous = {}
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    current, new = {}, []
    for root_raw in config.get("authorized_roots", []):
        root = Path(root_raw).expanduser()
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in SUPPORTED:
                continue
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            current[str(p)] = {"sha256": digest, "size": p.stat().st_size}
            if previous.get(str(p), {}).get("sha256") != digest:
                new.append(str(p))
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return {"status": "scanned", "new_sources": new, "auto_process": bool(config.get("auto_process_local"))}

def start_scan(config_path: Path, state_dir: Path, callback: Callable[[dict], None]) -> threading.Thread:
    def runner():
        callback(scan_authorized_sources(config_path, state_dir))
    thread = threading.Thread(target=runner, name="konoha-source-scan", daemon=True)
    thread.start()
    return thread
