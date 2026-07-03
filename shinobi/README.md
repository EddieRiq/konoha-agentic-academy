# Shinobi Theme

Shinobi is Konoha Agentic Academy's presentation layer.

It provides generic, license-safe terminal, ASCII, sound, palette, and animation assets for showing mission activity in a human-friendly way.

Shinobi may make the system easier to understand, but it does not control the system.

## Core rule

Shinobi is a presentation layer, not an execution layer.

The Shinobi theme may display state, urgency, progress, waiting input, review status, teachback status, or mission completion signals.

It may not authorize actions, modify mission scope, approve work, change doctrine, store sensitive content, or declare a mission complete.

## Public asset rule

The public Konoha Agentic Academy repository must only include assets that are:

- original;
- generic;
- license-safe;
- free to distribute;
- not based on protected characters, voices, logos, music, dialogue, or franchise-specific designs.

Public assets may be shinobi-inspired, but they must not copy or closely reproduce protected material.

## Local Village asset rule

Local Villages may define their own private assets.

Local assets may include custom avatars, sounds, animations, palettes, or project-specific visual themes.

If a local asset references a protected character, franchise, voice line, logo, soundtrack, or recognizable design, it must stay local and must never be committed to the public Konoha repository.

Local assets are the responsibility of the local user or team.

## Asset resolution order

The UI must resolve assets in this order:

1. Local Village assets.
2. User-level assets.
3. Public generic Shinobi assets.
4. Text-only fallback.

If a local asset exists, the UI should prefer it.

If no local asset exists, the UI should fall back to the public generic asset.

If no asset exists, the UI must still work in text-only mode.

## Recommended public structure

```text
shinobi/
  README.md
  assets/
    generic/
      ascii/
        backgrounds/
        avatars/
        status/
        animations/
      sounds/
      palettes/
```

## Recommended local structure

```text
alliance/<village>/
  assets/
    ascii/
      backgrounds/
      avatars/
      status/
      animations/
    sounds/
    palettes/
```

Local Village asset folders should normally be ignored by Git.

## Logical asset names

The UI should request assets by logical name, not by hardcoded file path.

Example:

```text
avatar.kagebunshin.coding
avatar.kagebunshin.waiting_input
background.village.idle
background.village.active
status.mission_complete
status.urgent
sound.input_required
sound.mission_complete
```

The asset resolver maps the logical name to the best available file.

Example resolution:

```text
avatar.kagebunshin.coding
  -> alliance/kirigakure/assets/ascii/avatars/kagebunshin_coding.txt
  -> ~/.konoha/assets/ascii/avatars/kagebunshin_coding.txt
  -> shinobi/assets/generic/ascii/avatars/worker_coding.txt
  -> text-only fallback: [kagebunshin: coding]
```

## Asset categories

### Backgrounds

Backgrounds represent mission spaces or UI scenes.

Examples:

```text
village_idle
village_active
mission_board
council_room
cubicles_idle
cubicles_active
```

### Avatars

Avatars represent agent roles and states.

Examples:

```text
hokage_idle
kagebunshin_coding
kagebunshin_debugging
kagebunshin_waiting_input
jounin_reviewing
shikamaru_writing
clerk_summarizing
```

Public avatars must be generic and original.

### Status assets

Status assets represent state transitions.

Examples:

```text
waiting_input
urgent
mission_complete
mission_failed
teachback_passed
review_requested
review_blocked
```

### Animations

Animations represent repeated UI actions.

Examples:

```text
spawn_worker
input_needed
mission_mastered
review_completed
learning_detected
```

Animations are optional.

A mission must remain understandable without animations.

### Sounds

Sounds may notify the user about mission events.

Examples:

```text
soft_ping
reminder_ping
urgent_ping
mission_complete
teachback_passed
```

Sounds must be optional and configurable.

The user must be able to disable sound.

## Notifications

Shinobi assets may be used by the notification layer for:

- waiting user input;
- approval required;
- urgent mission waiting;
- review completed;
- mission blocked;
- teachback ready;
- mission completed.

Notifications must follow the notification and telemetry policies.

A notification may alert the user, but it may not approve or execute anything.

## Voice layer

Shinobi may include visual or sound assets used by the Voice Layer.

The Voice Layer is transport, not memory.

Shinobi may show that voice input is active, transcription is ready, or text-to-speech is playing.

Shinobi may not store audio, store transcripts, interpret intent, or approve actions.

## Sensitive content

Shinobi assets must not display sensitive content unless the Mission Charter explicitly allows it.

Sensitive content includes:

- secrets;
- credentials;
- personal data;
- private emails;
- internal project context;
- confidential business information;
- local Village memory.

When in doubt, the UI must show a sanitized status instead of raw content.

Example:

```text
[waiting for user input]
```

instead of:

```text
[waiting for approval to use <private file name>]
```

## Text-only fallback

Text-only fallback is mandatory.

Konoha must remain usable in environments where:

- assets are missing;
- terminal rendering is limited;
- sound is disabled;
- UI rendering fails;
- local assets are not installed;
- accessibility requires plain text.

Example fallback:

```text
Mission: active
Hokage: planning
Kagebunshin: coding
Jounin: waiting
User input: required
```

## Relationship with telemetry

Telemetry is the source of truth for UI state.

Shinobi renders telemetry events.

Shinobi does not create mission state.

Example telemetry-to-asset mapping:

```text
agent_state_changed: kagebunshin -> coding
  -> avatar.kagebunshin.coding

user_input_required
  -> status.waiting_input
  -> sound.input_required

mission_completed
  -> status.mission_complete
  -> sound.mission_complete
```

## Relationship with doctrine

Shinobi must follow Konoha doctrine.

If Shinobi conflicts with Konoha Laws, Safety Policy, Approval Policy, Context Policy, Mission Charter, or local Village rules, doctrine wins.

Presentation never overrides governance.

## Completion checklist

Before adding a public Shinobi asset, verify:

- the asset is original, generic, or license-safe;
- the asset does not copy protected characters, logos, music, voices, dialogue, or designs;
- the asset has a logical name;
- a text-only fallback exists;
- the asset does not expose sensitive content;
- local override behavior remains supported;
- the asset is optional and does not affect mission execution.
