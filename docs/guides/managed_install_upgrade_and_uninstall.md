# Managed Install Upgrade and Uninstall

## Status

```bash
konoha install-status
```

Status validates:

- managed state and marker identity;
- install root, virtual environment and CLI;
- exact release tag and commit;
- canonical GitHub origin;
- clean working tree;
- global command presence.

The report is evidence only.

## Upgrade

```bash
konoha upgrade \
  --target-version v3.4.0 \
  --allow-network \
  --confirm-upgrade \
  --approval-token UPGRADE_KONOHA_INSTALL
```

Upgrade requires a healthy managed installation. It fetches only the requested
tag and checks out that exact tag in detached mode.

Blocked operations:

```text
force checkout
hard reset
branch rewrite
automatic latest selection
unapproved network
dirty-install upgrade
```

If checkout verification fails, the tool attempts to return to the previously
recorded commit and restores the previous state record.

## Uninstall

```bash
konoha uninstall \
  --confirm-uninstall \
  --approval-token UNINSTALL_KONOHA_CLI
```

Uninstall is recoverable:

- removes the global wrapper;
- moves the managed source tree to a timestamped `.uninstalled-*` path;
- archives the install state;
- does not recursively delete the source.

The archived path can be inspected before manual deletion.

## Stop conditions

Stop when:

- state or marker identities differ;
- paths escape the user's home;
- origin differs from the canonical repository;
- HEAD, tag or state commit disagree;
- the working tree is dirty;
- the requested upgrade is not newer;
- an exact approval token is missing.
