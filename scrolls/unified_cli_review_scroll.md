# Unified CLI Review Scroll

Status: v0.21.0 baseline.

Use this Scroll to review changes to the Unified CLI Entrypoint.

## Review objective

Confirm that the CLI improves usability without weakening existing gates.

## Required evidence

A review must include:

- command list;
- delegated internal tool mapping;
- help output or command examples;
- tests for routing;
- confirmation that dispatch is allowlisted;
- confirmation that arbitrary shell execution is not introduced;
- confirmation that approval tokens are still required by delegated gates;
- confirmation that non-zero delegated exit codes propagate.

## Safety checklist

Reviewers must verify that the CLI does not:

- execute arbitrary shell commands;
- accept arbitrary script paths;
- invoke adapters directly;
- read private Village context;
- create commits;
- push changes;
- clean or reset files;
- bypass apply approval;
- bypass staging approval;
- convert preview commands into confirmed actions.

## Allowed behavior

The CLI may:

- parse user-facing subcommands;
- call allowlisted internal Python tools;
- pass explicit arguments to delegated tools;
- print delegated output;
- return delegated exit codes.

## Blockers

Block the change if:

- `shell=True` is used;
- arbitrary command strings are executed;
- a user-provided path can select an executable tool;
- approval tokens are generated automatically;
- Git write behavior is added outside the Git staging gate;
- private or ignored paths become default scan targets;
- failures from delegated tools are swallowed.

## Review outcome

Use one of:

- `approved_for_release`;
- `revision_required`;
- `blocked`.

The CLI is approved only if it remains an entrypoint over existing gates, not a new authority layer.
