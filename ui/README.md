# Konoha UI

## Purpose

The Konoha UI is the human oversight layer for Konoha Agentic Academy.

It shows what is happening during a Mission without changing Mission scope, approving actions, modifying files, storing sensitive content, or replacing the Hokage, Mission Charter, Approval Policy, Safety Policy, Review Policy, or Teachback Policy.

The UI exists to make agent activity visible, understandable, and interruptible.

## Core rule

The UI observes and communicates.

The UI may not authorize actions, expand scope, approve work, modify doctrine, store sensitive content by default, or declare a Mission complete.

If the UI shows an action as available, that action must still pass the required Konoha policies.

## UI modes

Konoha may support multiple UI modes:

```text
terminal
ascii-dashboard
web-dashboard
desktop-dashboard
text-only
```

The first implementation should prefer a simple terminal or ASCII dashboard.

Advanced visual modes may be added later, but they must consume the same telemetry events and follow the same safety rules.

## Required visibility

The UI should make the following visible when available:

```text
current Mission
Mission state
active Hokage
active Local Kage
assigned Kagebunshin
active Clan
active Scroll
review level
approval level
context confidence
waiting user input
blocked actions
urgent status
latest evidence
latest review result
teachback state
memory/write status
```

The UI should not require the user to inspect raw logs to know whether Konoha is waiting, blocked, reviewing, executing, or asking for approval.

## Agent states

The UI may represent agent states using text, icons, ASCII art, or theme-specific assets.

Common states:

```text
idle
understanding
planning
waiting_user_input
awaiting_approval
assigned
executing
researching
coding
writing
debugging
testing
reviewing
blocked
escalated
learning
archiving
teachback
completed
failed
```

Theme-specific visual states must map to these logical states.

## Theme and asset resolution

Konoha ships only generic, original, or license-safe public assets.

Local Villages may override generic assets with private or user-provided assets.

Asset resolution order:

```text
1. Local Village assets
2. User-level Konoha assets
3. Public generic Konoha assets
4. Text-only fallback
```

If a requested asset is missing, the UI must fall back safely.

The UI must not fail because a visual asset is unavailable.

## Public assets

The public repository may include:

```text
generic terminal layouts
generic cubicle backgrounds
generic shinobi-inspired symbols
generic status indicators
generic ASCII workers
generic sounds created for the project
license-safe palettes
placeholders
```

The public repository must not include copyrighted characters, franchise-specific art, recognizable protected designs, voice lines, logos, music, or copied fan assets.

## Local assets

Local Village assets may include user-provided themes, avatars, sounds, and animations.

Local assets must remain local by default and should be ignored by Git unless the user explicitly chooses to publish license-safe assets.

A Local Village may define its own visual identity without changing Konoha core behavior.

## Notifications

The UI should notify the user when Konoha needs human input.

Notification events include:

```text
user_input_required
approval_required
urgent_user_input_required
mission_blocked
review_blocked
teachback_required
kage_summit_required
```

Notifications may include visual alerts, terminal messages, sounds, or Voice Layer output if enabled.

Notifications do not grant permission. They only request attention.

## Urgency escalation

Urgent Missions may increase notification intensity over time, within user-configured limits.

The UI should support:

```text
soft notification
reminder notification
urgent notification
mission paused after max reminders
```

Urgency escalation must respect quiet hours or local user settings when configured.

## Voice Layer integration

The UI may connect to the Voice Layer.

Voice input and output must follow the Voice Layer Policy:

```text
Speech-to-text only transcribes.
Text-to-speech only reads.
Voice Layer is transport, not memory.
```

The written text remains the official input and output.

Voice features must not bypass approvals, Mission Charters, Safety Policy, or Teachback.

## Teachback display

When Teachback is required, the UI should clearly show:

```text
agent explanation provided
user explanation pending
user explanation submitted
understanding accepted
understanding needs clarification
mission mastered
```

Optional reward animations may be shown only after the required understanding level is met.

Reward animations are visual feedback only. They do not replace policy checks.

## Sensitive content

The UI must minimize sensitive content.

By default, it should prefer:

```text
file names instead of full paths when possible
summaries instead of raw sensitive text
redacted secrets
sanitized snippets
status indicators instead of raw private content
```

The UI must not display secrets, credentials, private keys, tokens, raw personal data, or sensitive local memory unless explicitly allowed by the Mission Charter and Safety Policy.

## Telemetry source

The UI should be driven by telemetry events.

The UI should not infer hidden agent activity that was not emitted as telemetry.

If telemetry is missing or contradictory, the UI should display uncertainty rather than inventing a state.

## Text-only fallback

Konoha must remain usable without graphics, sounds, or voice.

If themes, assets, sounds, or visual dashboards are unavailable, Konoha must fall back to clear text output.

Example:

```text
Mission: build-readme-draft
State: waiting_user_input
Agent: Hokage
Reason: approval required before editing README.md
Question: Do you approve the Mission Charter?
```

## Forbidden UI behavior

The UI must not:

```text
approve actions automatically
hide blocked states
hide uncertainty
hide policy violations
summarize sensitive content without permission
store private content by default
show copyrighted public assets from the Konoha repository
claim a Mission is complete before review and Teachback requirements are met
replace the written Mission Report
```

## Completion

A UI event or animation may indicate that work appears complete, but official Mission completion still requires:

```text
required execution completed
required review completed
required safety checks passed
required Teachback completed
required memory handling completed
Hokage closure
```

The UI may celebrate completion, but it does not define completion.
