"""Safety boundaries for the Local Web UI Alpha."""

from __future__ import annotations


def boundaries() -> list[dict]:
    return [
        {"name": "Execution", "status": "blocked"},
        {"name": "Repository apply", "status": "blocked"},
        {"name": "Git operations", "status": "blocked"},
        {"name": "Private context access", "status": "blocked"},
        {"name": "Real model invocation", "status": "blocked from UI alpha"},
        {"name": "Network access", "status": "localhost UI only"},
        {"name": "UI authority", "status": "adds no new authority"},
        {"name": "Tokens", "status": "not stored and not autofilled"},
        {"name": "v2.0 Alignment Review Gate", "status": "required before v2.0.0"},
    ]
