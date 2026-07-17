from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class RegistryError(RuntimeError):
    pass

class CapabilityRegistry:
    def __init__(self, repo: Path):
        self.repo = repo
        self.path = repo / "config" / "konoha_v4_capabilities.json"
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def agent_family(self, name: str) -> dict[str, Any]:
        path = self.repo / "agents" / "families" / f"{name}.json"
        if not path.exists():
            raise RegistryError(f"No existe la familia especializada: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def model_allowed(self, provider: str, model: str, family: str) -> bool:
        for item in self.data["models"]:
            if item["provider"] != provider:
                continue
            if model not in {item["model"], "provider_default"}:
                continue
            return family in item["eligible_families"] or "*" in item["eligible_families"]
        return False

    def available_families(self) -> list[str]:
        return sorted(p.stem for p in (self.repo / "agents" / "families").glob("*.json"))
