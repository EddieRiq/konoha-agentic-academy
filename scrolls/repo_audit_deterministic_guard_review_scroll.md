# Repo Audit Deterministic Guard Review Scroll

## Review target

Konoha v3.0.2 deterministic repo audit guard.

## Checks

- Local model output is evidence only.
- Deterministic marker checks run before patch planning.
- Candidate issues are split into validated and suppressed.
- Suppressed issues include reason and evidence.
- Patch plan uses validated issues only.
- No patch is proposed when README/docs already contain required markers.

## Known limitation

The guard is intentionally conservative and marker-based. It does not fully understand documentation quality; it only prevents known repeated false positives before the Hokage Terminal Shell is introduced.
