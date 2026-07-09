# Controlled Tool Execution Gate

The Controlled Tool Execution Gate is the first Konoha boundary that can execute a small set of allowlisted internal tools under explicit human approval.

It is not a general shell runner. It does not accept arbitrary commands. It does not grant new runtime authority.

## Core rule

```text
Controlled tool execution is evidence only.
A tool result is not permission to apply, stage, commit, push, invoke models, invoke adapters, access private context, or close a mission.
```

## Allowed actions in v1.8.0

```text
mission_workspace_validate
mission_workspace_inspect
approval_status
approval_reports_list
runtime_package_validate
```

Each action maps to a fixed internal Konoha script and a fixed argument shape.

## Approval

Confirmed execution requires:

```text
--confirm-execution
--approval-token EXECUTE_CONTROLLED_TOOL
```

Preview mode is the default and performs no delegated execution.

## Required safety flags

Every execution plan must declare:

```text
execution_scope: allowlisted_tool_only
private_context_access: false
network_access: false
git_operations: false
repository_apply: false
real_model_invocation: false
arbitrary_shell: false
background_agent: false
```

If any blocked flag is enabled, the gate fails.

## Filesystem boundary

The gate itself writes only controlled tool execution reports under:

```text
sandbox/reports/
```

Delegated tools may write only according to their own already-established boundaries.

## Blocked

The gate may not:

- execute arbitrary shell commands;
- use `shell=True`;
- accept arbitrary executable paths;
- use network access;
- invoke real models;
- invoke adapters;
- access private Village context;
- apply repository changes;
- perform Git operations;
- run background agents;
- close missions.

## UI relationship

The Local Web UI Alpha may display controlled execution plans and reports. It should not add new permission. Any UI-driven controlled execution must still pass this gate and require explicit token entry.

## v2.0 alignment gate

Before v2.0.0, Konoha must pause for a v2.0 Alignment Review Gate conversation to confirm the system still matches the original intent, local-first design, human-in-the-loop control, autonomy limits, and safety doctrine.
