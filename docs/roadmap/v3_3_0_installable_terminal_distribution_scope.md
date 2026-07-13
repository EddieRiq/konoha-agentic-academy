# v3.3.0 Installable Terminal Distribution Scope

## Objective

Deliver Konoha as a one-line managed terminal installation and close the
maintainer package-to-release workflow in the same release.

## Included

- canonical version module;
- `pyproject.toml` and console-script metadata;
- one-line Bash installer for Linux/WSL;
- global `konoha` wrapper;
- managed install state and marker;
- read-only install status;
- explicit-tag upgrade with rollback;
- recoverable uninstall;
- isolated clean-install smoke;
- package-to-release wrapper;
- CLI registry entries;
- schemas, examples, guides and review Scroll;
- dogfood through the new wrapper.

## Excluded

- Web UI work;
- daemon/background service;
- automatic latest upgrade;
- native Windows installer;
- remote model installation;
- new mission capabilities;
- new release state machine;
- destructive purge;
- v3.4 product-polish work.

## Acceptance criteria

1. One-line installer requires explicit confirmation and token.
2. Clone is pinned to `v3.3.0`.
3. `konoha --version` returns `3.3.0`.
4. Command registry validates from an isolated venv.
5. Managed paths remain under the user home.
6. Status detects commit/tag/origin/dirty divergence.
7. Upgrade requires a newer explicit tag, network flag and token.
8. Uninstall is recoverable rather than destructive.
9. Package and release plans have exact scope alignment.
10. Wrapper retains every existing release token.
11. Wrapper reentry recognizes an already closed release.
12. Focused and canonical tests pass on the exact release commit.
13. Public/private scan passes.
14. Final status is `PACKAGE_RELEASE_CLOSED`.
