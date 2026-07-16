# v3.6.0 Supervised Mission Runtime

## Flow

1. The user submits a request.
2. The Hokage interprets intent.
3. The decision engine classifies the mission.
4. Konoha proposes a provider, model, strategy and economy estimate.
5. A Mission Charter is generated.
6. The human approves or rejects the Charter.
7. Each execution action remains a separate approval gate.
8. Jōnin reviews evidence independently.
9. Teachback and closure remain human-controlled.

## Provider selection

- Software and repository work prefers Codex when ready.
- Research and general reasoning prefers Claude when ready.
- Low-risk knowledge processing prefers Ollama when ready.
- High-complexity local execution requires superior review.
- No ready provider results in STOP and escalation.

## Anti-loop

Retries require new root-cause evidence. Repeated error signatures stop the
mission and escalate to the Hokage and human authority.

## Telemetry

Konoha records provider, model, tokens when available, duration, outcome and
error signature in private state only.

## Doctrine evolution

Shikamaru may propose an Instruction Delta. It cannot apply or approve it.
Independent review and human approval are required.
