"""Command suggestion helpers.

The Local Web UI Alpha displays equivalent CLI commands, but does not run them.
"""

from __future__ import annotations

from pathlib import Path


def suggest_commands(
    repo_root: Path,
    workspace_root: Path,
    sandbox_root: Path,
    mission_id: str,
) -> dict[str, str]:
    return {
        "mission_validate": (
            "python .\\tools\\mission_workspace\\manage_mission_workspace.py validate "
            f"--workspace-root \"{workspace_root}\" --mission-id \"{mission_id}\""
        ),
        "approval_status": (
            "python .\\tools\\approval_console\\manage_mission_approval.py status "
            f"--workspace-root \"{workspace_root}\" --mission-id \"{mission_id}\""
        ),
        "planner_preview": (
            "python .\\tools\\planner_loop\\run_hokage_planner_loop.py "
            f"--repo-root \"{repo_root}\" --workspace-root \"{workspace_root}\" "
            f"--mission-id \"{mission_id}\" --sandbox-root \"{sandbox_root}\" "
            "--run-id \"ui-alpha-planner-preview\" "
            "--contract \".\\examples\\model_invocation\\model_invocation_contract.example.json\" "
            "--request \".\\examples\\model_invocation\\mock_model_request_plan.example.json\""
        ),
    }
