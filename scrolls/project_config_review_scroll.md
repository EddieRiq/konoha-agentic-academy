# Project Config Review Scroll

Status: pre-release / review Scroll.

## Purpose

This Scroll reviews Konoha project configuration changes and the policy contract around local-first execution boundaries.

## Required inputs

- Proposed config file.
- Config schema.
- Config validation report.
- Diff of changed config fields.
- Evidence that validator tests passed.

## Review checklist

### Identity and schema

- `config_type` is `konoha_project_config`.
- `schema_version` is present.
- Project mode remains `local_first`.

### Sandbox

- Sandbox paths are repo-relative.
- Sandbox paths do not use path traversal.
- `runs_dir`, `tmp_dir`, and `reports_dir` remain inside the configured sandbox root.

### Allowed paths

- Allowed apply destinations are narrow.
- Allowed staging paths are narrow.
- Private paths are not allowlisted.
- Local-only paths are not allowlisted.

### Safety flags

The following must remain true or blocked:

- execution blocked;
- filesystem mutation blocked by default;
- repository apply requires approval;
- Git staging requires approval;
- Git commit blocked;
- Git push blocked;
- adapter execution blocked;
- private context access blocked;
- network access blocked.

### Approval tokens

- Apply token remains `APPLY_SANDBOX_PLAN`.
- Git staging token remains `STAGE_ALLOWLISTED_FILES`.
- Tokens are not treated as standalone authorization.

## Stop conditions

Stop review if:

- private paths are allowlisted;
- Git commit or push is enabled;
- execution is enabled;
- adapter execution is enabled;
- network access is enabled;
- approval is weakened;
- config path traversal is present;
- validator tests fail.

## Output

The reviewer should return one of:

- `approved_for_pre_release`;
- `revision_required`;
- `blocked`.

This Scroll does not authorize runtime actions, Git operations, adapter execution, private context access, or mission execution.
