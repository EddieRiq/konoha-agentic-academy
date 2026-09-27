# Repository comprehension and supervised learning (unreleased v4.2.x)

This guide describes the implemented local core and terminal module. v4.1.1
remains the latest published release. The final conversational CLI integration
is the next product step; these changes do not publish v4.2.0 or v4.2.1.

## Study an explicitly authorized public repository

Use an existing local checkout. This workflow does not clone, fetch, download,
run repository code, invoke a provider or apply patches. A real remote
acquisition requires a separate explicit human/network authorization.

```bash
python -m tools.repo_evidence.workflow study \
  --repo /path/to/public-repo \
  --authorize-repo /path/to/public-repo \
  --public \
  --authorization-note "Human authorizes static public repository study" \
  --state-root /path/to/private-study-state
```

`--authorize-repo` must exactly match the resolved absolute target root.
`--public` is the human's public-repository assertion, not an automatic remote
visibility check. An optional `--source-url https://example.org/public/repo`
records a human-declared origin; it is not remotely verified. URLs containing
credentials, query strings or fragments are refused.

State must be outside the target repository or in a Git-ignored directory.
It contains local paths, evidence, questions and study records and stays local.
Do not publish this state. The same code works for Konoha and another public
repository; there is no Konoha-specific parser.

The result includes `study.study_id`. Reuse that exact ID and the same
authorization arguments for all subsequent commands.

## Explain, repeat and clarify

Replace `study` with `explain` and add `--study-id study-<returned-id>`.
The overview explains components, structural relationships, entrypoints,
test files and documentation statements, with locators and limitations.
Add `--category tests`, `components`, `relationships`, `capabilities`,
`documentation` or `candidates` for more detail in one area. Repeating
`explain` reads the same persisted pack; it does not reacquire evidence.

Replace the command with `respond` to enter one exact human line at `Human>`.
Clarification or repetition requests keep the loop open. Only the exact line
`:entendido` marks repository understanding as complete. Case changes,
surrounding spaces, ordinary “yes”, and model declarations do not close it.
`--human-input` supports an explicitly supplied human response for terminal
automation; it is never populated from model output by this workflow.

Repository understanding grants no execution approval. Existing structured
mission teachback still requires its own execution/review evidence; mission
closure remains a separate gate. This repository loop does not manufacture a
passed mission-teachback record.

## Self-improvement proposals

After human repository teachback, use `recommend` with the same arguments.
The result separates:

- `validated`: deterministic static candidates with provenance, risk and scope;
- `model_suggestions`: supplied API suggestions with verified locator linkage,
  explicitly not deterministic truth;
- `suppressed`: malformed, ungrounded or excess suggestions.

The terminal command generates deterministic candidates without invoking a
model. The Python API can accept suggestions from an independently authorized
caller. Confidence scores grant no authority. An empty result does not prove
that no improvements exist, and an unused-symbol candidate is not proof that
deletion is safe. Every recommendation remains `proposed` with
`authorizes_action=false`.

## Compare a donor with Konoha

Study and explain both local repositories, then complete human teachback for
both. Use the donor's authorization/state arguments as the primary arguments
to `compare`, and add:

```text
--target-repo /path/to/konoha
--authorize-target-repo /path/to/konoha
--target-public
--target-authorization-note "The exact note used for the target study"
--target-state-root /path/to/private-konoha-study-state
--target-study-id study-<target-id>
```

If the target study used a source URL, also repeat `--target-source-url`.
Comparison retains the observed donor fact, its locator/pack/study identity,
the target comparison and its provenance, a candidate lesson, compatibility
and license concerns, and a recommendation. No code is copied or adopted.
An external repository does not become authority over Konoha doctrine.
Adoption requires review and a separately approved implementation mission.

## Exact evidence and failure behavior

Planning acquires one RepositoryEvidencePack. The plan binds its `pack_id`
and the SHA-256 of the complete persisted payload before approval. Execution
and resume reload that exact pack, verify integrity and root identity, then
check currentness. Missing/corrupt/stale packs stop before provider readiness,
Git baseline, executing state or invocation. They are never silently refreshed.
Changed repository content requires a new planning transaction or a new study
and its own human teachback.

The source gate resolves a family's required sources once and retains that
mapping for both availability checks and `resolved_source_bundle`. It does
not resolve again for the prompt. Legacy execution uses the same gate; its
source failure raises `RequiredSourcesError` without fabricated evidence.
Resumable execution returns a stable `required_sources:...` diagnostic and
preserves approval and progress. Legacy plans needing repository evidence must
be replanned because an absent binding cannot authorize acquisition.

## Bounds and limitations

- File material: at most 20,000 bytes per selected file and ten selected items.
  Selected missing/unreadable/empty files fail the source closed. Path traversal,
  private markers, ignored inputs and symlinks are refused.
- Text material: 2,000 characters; lists: ten items, with explicit omission
  metadata. The original human request is exact or unavailable: over-2,000-
  character requests fail closed rather than being summarized or truncated.
- Original requests come from canonical durable `continuity.original_request`.
  Missing/corrupt continuity is not replaced by the plan's understanding.
- Persisted provider output above 200,000 bytes is rejected for materialization;
  malformed JSON and invalid source shapes fail closed. Raw dependency output
  is never copied beside the resolved bundle.
- Studies include at most ten facts in each of six categories, with exact
  locators. Static extraction is primarily Python-oriented; test discovery does
  not prove execution or coverage, and documentation statements are claims.
- State is local and user-owned. Integrity checks detect mismatches with the
  approved reference; they are not authentication against an owner rewriting
  every local record. Repository files must stay stable during inspection.

Schemas live under `schemas/runtime/`: `repository_study_record`,
`repository_teachback`, `self_improvement_recommendations` and
`donor_learning_recommendations`. Canonical implementation is under
`tools/repo_evidence/`, `tools/konoha_v4/required_sources.py`, and the existing
`tools/teachback/manage_teachback.py` and `tools/local_model_audit/` modules.
