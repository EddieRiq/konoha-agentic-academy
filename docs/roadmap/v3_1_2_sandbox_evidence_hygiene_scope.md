# v3.1.2 Sandbox Evidence Hygiene Scope

## Objective

Keep generated Konoha runtime evidence local and prevent accidental staging from `sandbox/`.

## Included

- General ignore rule for generated sandbox content.
- Explicit preservation of public sandbox files.
- Operator guide, roadmap scope and review Scroll.
- README, CHANGELOG and index markers.

## Excluded

- Hokage Shell behavior changes.
- Local model audit changes.
- Beta runtime changes.
- Canonical test runner.
- Mission Continuity.
- Automatic deletion or Git operations.

## Acceptance criteria

1. Existing reports remain on disk.
2. Generated sandbox paths are ignored.
3. The three public sandbox files remain tracked.
4. Focused tests pass.
5. Smoke output does not dirty Git status.
