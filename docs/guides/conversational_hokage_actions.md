# Conversational Hokage Actions

## Slice 2

Slice 2 connects the chat-oriented Hokage to the existing supervised beta
runtime.

After the exact Mission Charter approval, Hokage creates the runtime mission
and plan, translates registered capabilities into immutable action proposals,
and waits for an exact approval phrase:

```text
APROBAR ACCION-...
```

The approval is bound to the action argument hash. Any argument change
invalidates approval.

## Initial skills

- `inspect_python_runtime`
- `inspect_git_status`
- `invoke_local_model` when Ollama is available and requested

Every Slice 2 skill is non-mutating and requires no external network.

## Runtime bridge

Hokage supplies the beta runtime's internal approval token only after the
conversational approval phrase and argument hash are validated. The user does
not need to know runtime subcommands or technical tokens.

Command and model results remain evidence only.

## Next slice

Slice 3 adds deterministic result validation, human review, Teachback and
mission closure through the same `Mission>` conversation.
