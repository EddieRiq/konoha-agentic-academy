# v3.2.6 Repository Consolidation Scope

## Objective

Close the remaining pre-distribution repository debt in one release:

```text
structured Teachback
evidence-bound Mission Closure
canonical CLI and command registry
runtime manifest alignment
current-state documentation
```

This is the final `v3.2.x` feature release.

## Included

### Teachback

- Levels `0..4`.
- Results `passed`, `needs_clarification`, `failed`, `skipped`.
- Explicit human evidence.
- Execution and review source paths.
- Manifest/risk policy.
- Idempotent identical reentry.
- Non-overridable conflict.

### Closure

- Successful execution evidence.
- Approved human review evidence.
- Closure-eligible Teachback.
- Separate human closure token.
- Source SHA-256 fingerprint.
- Idempotent closure reentry.
- Conflict blocked even with `--force`.
- Explicit local/private memory outputs.

### Runtime alignment

- Beta mission manifests declare Teachback policy.
- Unified Mission Runtime manifests declare Teachback policy.
- Product Runtime mission manifests declare Teachback policy.
- Hokage Shell sessions create compatible mission manifests.
- Beta and Hokage record compatible human review evidence.

### CLI coherence

- `tools/konoha_cli.py` is canonical.
- `tools/command_registry.py` is the command source of truth.
- Active and deprecated commands are separated.
- Help and registry inspection use the same metadata.
- CLI does not inject tokens or network flags.

### Documentation

- Current README status.
- Frozen roadmap through `v3.4.0`.
- Structured Teachback guide.
- Evidence-bound closure guide.
- Canonical CLI guide.
- Capability matrix.
- Release safety boundaries.
- Review Scroll and examples.

## Excluded

```text
global `konoha` command
pyproject/wheel packaging
one-line installer
upgrade/uninstall
package-to-release wrapper
Web UI work
new model or adapter families
new release/package guard layers
```

These belong to `v3.3.0`, except finished product UX which belongs to `v3.4.0`.

## Acceptance criteria

1. No phrase-only Teachback closure remains active.
2. Mission Closure cannot fabricate a passed record.
3. `needs_clarification` and failed execution/review block closure.
4. Identical Teachback and closure reentry are idempotent.
5. Conflicting evidence is blocked even with `--force`.
6. Active CLI registry paths exist.
7. CLI injects no approval token or network permission.
8. Runtime manifests expose compatible Teachback policy.
9. Package installation and release workflow regression suites remain green.
10. Canonical tests pass on the exact release commit.
11. Public/private scope scan passes.
12. Roadmap names only `v3.3.0` and `v3.4.0` as planned product milestones.

## Known limitations

- Human explanation quality is recorded, not automatically judged by a model.
- The user or reviewer remains responsible for truthful evidence.
- The repository CLI is still invoked through Python until `v3.3.0`.
- Closure writes memory only to an explicitly supplied local root.
