# Konoha v4 provider diagnostics candidate

## Objective

Preserve actionable diagnostics from Codex, Claude and Ollama provider failures.

## Scope

- Structured `ProviderError`.
- Codex JSONL failure-event extraction.
- Schema existence and JSON validation before invoking Codex.
- Timeout, process, unavailable and empty-output classifications.
- Token usage normalization including cached and reasoning token fields.
- Regression tests.

## Non-goals

- No change to mission planning semantics.
- No doctrine changes.
- No release tag.
- No automatic commit or push.
- No fallback that silently disables `--output-schema`.

## Qualification

A real KCQ-400 run must still prove the planner schema is accepted by the installed
Codex CLI. If the schema is rejected, the resulting error must now include the
provider event or stdout diagnostic needed for the next bounded fix.
