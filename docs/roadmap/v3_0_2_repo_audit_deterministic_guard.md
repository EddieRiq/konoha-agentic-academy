# v3.0.2 Repo Audit Deterministic Guard

## Goal

Reduce false positives in local model repository audits before building the Hokage Terminal Shell.

## Added

- Deterministic marker checks for README, CHANGELOG, docs roadmap and guides index.
- Separation of model-suggested issues from validated issues.
- Suppression of possible false positives with explicit deterministic evidence.
- Patch plan generation only from validated issues.
- Tests covering a local model false positive that is contradicted by README/docs markers.

## Safety

- Local model output remains evidence only.
- Suppressed issues are not silently discarded; they are recorded for review.
- Patch plans remain approval-gated.
- Git operations remain delegated to the beta Git gate.

## Next

v3.1.0 should add Hokage Terminal Shell with ASCII/ANSI UI, persona selection, mission menu, local Obsidian-compatible memory notes and deterministic guard integration.
