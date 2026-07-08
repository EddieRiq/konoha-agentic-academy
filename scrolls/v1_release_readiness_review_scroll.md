# v1.0 Release Readiness Review Scroll

Use this Scroll before tagging `v1.0.0`.

## Required evidence

- Release readiness checker passed.
- Unit tests passed.
- Integrated smoke tests passed.
- Dogfood Mission Suite passed.
- Repo inspection passed.
- Git readiness passed.
- Sensitive grep showed no private leaks.
- Release notes clearly state stable boundaries.

## Review questions

1. Does the repo explain what v1.0.0 supports?
2. Does it also explain what v1.0.0 does not support?
3. Are real adapters still blocked by default?
4. Are Git writes still gated?
5. Are sandbox outputs still local and ignored when appropriate?
6. Are private Village paths still ignored?
7. Are release notes honest about dry-run scope?
8. Can a new user run the v1.0 smoke checks from README/docs?
9. Are all release artifacts generic and public-safe?
10. Has a human reviewed the readiness evidence?

## Non-authority reminder

The release readiness checker does not approve the release. It only provides evidence.
