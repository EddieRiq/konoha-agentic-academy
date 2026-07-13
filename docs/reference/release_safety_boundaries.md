# Release Safety Boundaries

## Product and maintainer surfaces

Product operations:

```text
doctor
status
shell
mission start/run/plan/review/teachback/close
```

Maintainer operations:

```text
package status/install
release status
release deliver
supervised release workflow
Git plan/stage/commit/push
```

Product commands do not authorize maintainer commands.

## Package installation

Package installation validates:

```text
direct_repo_paths ∩ helper_modified_paths = ∅
direct_repo_paths ∪ helper_modified_paths = expected_public_paths
```

It performs no Git or network operation.

## Release workflow

Release publication retains distinct explicit tokens for:

```text
workflow run
Git plan
Git stage
Git commit
Git push
tag creation
tag publication
GitHub Release publication
Latest promotion
```

A command block containing all tokens remains one user approval event for the
planned release, but the underlying gates remain semantically distinct.

## Public/private boundary

Never publish:

```text
.env
credentials or tokens
sandbox runtime evidence
alliance/kirigakure
private-library
alliance/*/memory
memory/local
vault
client/company/private data
copyrighted private assets or literature
```

## Stop conditions

Stop release work when:

- tests fail;
- expected scope differs;
- staged paths exist unexpectedly;
- base commit or branch differs;
- a private path appears;
- an evidence source is stale or corrupt;
- tag or release state diverges;
- force, delete or rewrite would be required;
- human approval evidence is ambiguous.

## Non-authority

Test, package, status and release reports are evidence only.
## Managed terminal distribution

The one-line installer may write only to explicit paths under the current
user's home. It creates a managed marker and state record.

Upgrade requires:

```text
healthy managed state
clean checkout
canonical origin
newer explicit tag
--allow-network
--confirm-upgrade
UPGRADE_KONOHA_INSTALL
```

Uninstall requires:

```text
healthy managed state
--confirm-uninstall
UNINSTALL_KONOHA_CLI
```

Uninstall moves the source to recoverable trash. It does not recursively purge
the installation.

## Package-to-release wrapper

The wrapper composes existing guards. It does not collapse their authority.

Required explicit approvals remain:

```text
package installation
delivery wrapper
Git plan
Git stage
Git commit
Git push
tag creation
tag publication
GitHub Release publication
Latest promotion
network
```

A resumed delivery must be on the exact planned release commit and must be
classified safe-to-resume by the existing read-only release status tool.
