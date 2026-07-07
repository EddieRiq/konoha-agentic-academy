# Context Capsule Lifecycle Review Scroll

Status: documentation-first baseline.

This Scroll reviews whether a context capsule can be used safely, refreshed, approved, invalidated, or retired.

## Purpose

Use this Scroll before:

- approving a capsule for routine intake;
- using a capsule to reduce repeated instruction loading;
- refreshing a stale capsule;
- replacing source-file reading with capsule-first intake;
- creating public capsules from Konoha doctrine;
- creating local capsules inside an Allied Village.

## Required inputs

A review must include:

- capsule manifest;
- source file list;
- source hashes;
- intended use;
- stop conditions;
- full-source required triggers;
- review status;
- token budget reason.

## Review checklist

### Scope

- [ ] Capsule scope is narrow.
- [ ] Intended use is explicit.
- [ ] Non-authorized uses are explicit.
- [ ] Sensitive actions are not authorized by the capsule.

### Sources

- [ ] Every summarized source is listed.
- [ ] Source hashes are recorded.
- [ ] Source roles are documented.
- [ ] Local private sources remain local.
- [ ] Public capsules do not include private content.

### Authority

- [ ] Capsule does not replace Konoha laws.
- [ ] Capsule does not replace Mission Charter requirements.
- [ ] Capsule does not grant permissions.
- [ ] Capsule does not weaken stop conditions.
- [ ] Capsule states when full source is required.

### Staleness

- [ ] Stale conditions are defined.
- [ ] Hash mismatch behavior is defined.
- [ ] Refresh report is required after source changes.
- [ ] Deprecated capsules cannot be used as primary intake.

### Token governance

- [ ] Capsule use has a token budget reason.
- [ ] Expected intake savings are documented.
- [ ] Token savings do not remove safety checks.
- [ ] Usage reporting is required after missions.

## Stop conditions

Stop review if:

- sources are missing;
- hashes are missing;
- the capsule includes private or copyrighted content in a public path;
- the capsule claims authority over doctrine;
- the capsule weakens approval, safety, Git, release, or private-context rules;
- the capsule is being used for a sensitive mission without full-source review;
- there is a source/capsule conflict.

## Verdicts

### Approved for routine use

The capsule may be used as primary intake for routine, low-risk missions.

### Needs changes

The capsule can be fixed but is not yet approved.

### Source-required

The mission or scope requires direct source reading.

### Stale

The capsule must be refreshed before use.

### Blocked

The capsule is unsafe, misleading, private in a public path, or authority-confusing.

## Output

A review should produce:

```text
capsule:
scope:
sources reviewed:
hash status:
verdict:
allowed use:
full-source triggers:
token budget note:
required changes:
```

## Reviewer rule

A reviewer may approve capsule use for routine intake. A reviewer may not use a capsule to grant permissions that doctrine or Mission Charter do not grant.
