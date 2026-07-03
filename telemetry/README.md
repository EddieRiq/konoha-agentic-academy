# Telemetry

Telemetry is Konoha Agentic Academy's visibility layer.

It records what is happening during a mission so the user, the Hokage, reviewers, UI, notifications, and memory systems can understand the current state without guessing.

Telemetry is not doctrine, memory, approval, or execution. It is observation.

## Core rule

Telemetry observes mission activity.

Telemetry may report states, events, alerts, progress, blockers, and required user input.

Telemetry may not authorize actions, modify mission scope, approve work, store sensitive content by default, or replace the Mission Charter.

## Purpose

Telemetry exists to answer these questions:

- What mission is active?
- Which agent is working?
- What role is the agent playing?
- Which Scroll is active?
- What state is the agent in?
- Is the mission waiting for user input?
- Is the mission blocked?
- Is the mission urgent?
- What review level is required?
- What was the last safe event?
- What should the UI display?
- Should a notification be triggered?

## Relationship to other policies

Telemetry must obey:

- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/safety/safety_policy.md`
- `protocols/context/context_policy.md`
- `protocols/approval/approval_policy.md`
- `protocols/mission-charter/mission_charter.md`
- `protocols/review/review_policy.md`
- `protocols/teachback/teachback_policy.md`
- `ui/voice/voice_layer_policy.md`

If telemetry conflicts with safety or privacy, safety wins.

## Event model

A telemetry event should be structured, minimal, and safe.

Recommended fields:

```yaml
event_id:
timestamp:
mission_id:
village:
agent_id:
agent_role:
agent_rank:
clan:
scroll:
state:
event_type:
message:
urgency:
needs_user_input:
approval_required:
review_required:
sensitive:
safe_to_display:
source:
```

## Event types

Common event types:

```text
mission.created
mission.charter_drafted
mission.charter_approved
mission.blocked
mission.resumed
mission.completed_by_agent
mission.completed_by_user

agent.assigned
agent.started
agent.progress
agent.blocked
agent.waiting_user_input
agent.handoff_ready
agent.failed
agent.completed

approval.requested
approval.granted
approval.denied

review.requested
review.completed
review.changes_requested
review.blocked

scribe.learning_proposal_created
scribe.doctrine_change_proposed
scribe.doctrine_change_applied

memory.context_pack_created
memory.summary_created
memory.archive_reference_created

notification.sent
notification.escalated

voice.transcription_ready
voice.output_played
```

## Agent states

Recommended agent states:

```text
idle
understanding
planning
waiting_user_input
waiting_approval
assigned
working
researching
coding
writing
debugging
testing
reviewing
summarizing
blocked
failed
handoff_ready
done_by_agent
completed_by_user
archived
```

The UI may map these states to terminal panels, ASCII assets, colors, sounds, or animations.

## Notification triggers

Telemetry may trigger notifications when an event requires user awareness.

Allowed notification triggers:

```text
agent.waiting_user_input
approval.requested
mission.blocked
review.changes_requested
mission.urgent_waiting
mission.completed_by_agent
teachback.required
```

Notification escalation must follow the Notification Policy when implemented.

Until then, notification behavior must remain conservative.

## Urgency levels

Recommended urgency levels:

```text
low
normal
high
urgent
critical
```

Urgency affects notification behavior, not permission.

Urgent missions still require the same approvals, reviews, and safety checks as non-urgent missions.

## User input state

When user input is required, telemetry should include:

```yaml
needs_user_input: true
input_reason:
question:
blocking: true
urgency:
first_requested_at:
reminder_count:
```

If the user does not respond, the mission must wait, pause, or escalate according to approved policy.

The agent must not proceed by assumption.

## UI integration

The UI should read telemetry events and display:

- current mission;
- current agents;
- active roles;
- active Scrolls;
- current state;
- waiting input;
- blockers;
- review status;
- approval status;
- urgency;
- recent safe events.

The UI may use generic public assets or local Village assets.

Asset resolution should prefer:

```text
1. Local Village assets
2. User-level assets
3. Public generic Konoha assets
4. Text-only fallback
```

Telemetry must not require visual assets to function.

## Public and local assets

The public repository may include only generic, original, or license-safe assets.

Local Villages may override assets with private or user-selected themes.

Telemetry should reference logical asset names, not franchise-specific names.

Example:

```yaml
asset_hint: "avatar.kagebunshin.coding"
```

The UI resolves this to the best available asset.

## Voice Layer integration

Voice events may be emitted when the Voice Layer is enabled.

The Voice Layer is transport, not memory.

Telemetry may record that transcription was ready or output was played, but it must not store audio.

Voice content follows the same rules as text content.

## Sensitive content

Telemetry must minimize sensitive content.

Do not place secrets, private data, raw emails, personal identifiers, credentials, `.env` content, internal files, or proprietary data in telemetry events unless explicitly allowed by the Mission Charter and Safety Policy.

Prefer safe summaries.

Examples:

```yaml
message: "User input required before accessing local memory."
safe_to_display: true
```

Avoid:

```yaml
message: "Need approval to use a secret from .env."
safe_to_display: false
```

## Storage

Telemetry may be stored as JSONL or another structured event format.

Recommended local paths:

```text
telemetry/events/
alliance/<village>/telemetry/events/
```

Local telemetry stays local by default.

Telemetry from an Allied Village must not be promoted to the public repository unless sanitized, summarized, and approved.

## Completion telemetry

A mission may emit:

```text
mission.completed_by_agent
```

when the assigned work is done and reviewed.

A mission may emit:

```text
mission.completed_by_user
```

only after the required Teachback level is satisfied.

`done_by_agent` is not the same as `completed_by_user`.

## Violations

The following are telemetry violations:

- using telemetry as approval;
- storing sensitive data by default;
- storing raw audio;
- exposing local Village information publicly;
- hiding blockers;
- fabricating events;
- declaring completion without review or Teachback;
- continuing after a waiting-user-input event without user response;
- using urgency to bypass safety.

## Completion checklist

Telemetry is correctly used when:

- events are structured;
- events are minimal;
- events are safe to display or marked unsafe;
- user input requirements are visible;
- urgency is visible but does not bypass policy;
- UI can render state without reading private context;
- memory can reference events without treating them as doctrine;
- no action is authorized by telemetry alone.
