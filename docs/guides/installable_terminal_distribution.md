# Installable Terminal Distribution

## One-line install

```bash
curl -fsSL \
  https://raw.githubusercontent.com/EddieRiq/konoha-agentic-academy/v3.3.0/scripts/install.sh \
  | bash -s -- \
      --version v3.3.0 \
      --confirm-install \
      --approval-token INSTALL_KONOHA_CLI
```

The installer:

1. clones the exact annotated release tag;
2. verifies the checkout matches that tag;
3. creates a private virtual environment;
4. creates `~/.local/bin/konoha`;
5. records managed state outside the repository;
6. validates `konoha --version` and the command registry.

It does not install a daemon, start background agents, enable network after the
clone, or inject mission/release approval tokens.

## Default locations

```text
source:
  ${XDG_DATA_HOME:-~/.local/share}/konoha-agentic-academy

command:
  ${XDG_BIN_HOME:-~/.local/bin}/konoha

state:
  ${XDG_STATE_HOME:-~/.local/state}/konoha/install.json
```

All paths must remain under the current user's home.

## First commands

```bash
konoha --version
konoha --help
konoha doctor --repo-root .
konoha init --repo-root .
konoha status --repo-root .
konoha shell --repo-root .
```

## Installation authority

The one-line command contains explicit install confirmation and the exact
installation token. That token authorizes only the managed install steps in
`scripts/install.sh`.

It does not authorize:

- a mission;
- model invocation;
- file mutation outside the managed install paths;
- Git delivery;
- release publication;
- upgrade;
- uninstall.

## Developer installation

The repository contains `pyproject.toml` and a console-script definition for
editable development environments:

```bash
python -m pip install --no-deps --no-build-isolation -e .
konoha --version
```

The supported end-user path is the managed source installation, because Konoha
uses repository-relative schemas, examples, Scrolls and tools.

## Clean-install smoke

Maintainers run:

```bash
python -S tools/distribution/run_clean_install_smoke.py \
  --repo-root . \
  --expected-version 3.3.0 \
  --output ./sandbox/reports/v3-3-0-clean-install-smoke.json \
  --force
```

The smoke creates an isolated temporary virtual environment under sandbox,
creates the same wrapper shape, and verifies version, registry, help, doctor,
managed-install status help and release-delivery help.
