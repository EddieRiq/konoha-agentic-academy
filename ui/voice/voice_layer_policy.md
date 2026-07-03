# Voice Layer Policy

## Purpose

The Voice Layer allows Konoha Agentic Academy to accept spoken user input and read written agent output aloud.

The Voice Layer is a transport layer only. It does not reason, decide, approve, summarize, remember, or modify content.

## Core rules

Voice Layer is transport, not memory.

Voice input and output must follow the same policies as text input and output.

The Voice Layer may convert speech to text or text to speech, but it may not store, interpret, approve, modify, summarize, or remember content.

The written text remains the official source of truth.

## Scope

This policy applies to:

- speech-to-text transcription;
- text-to-speech playback;
- voice notifications;
- spoken Teachback interactions;
- accessibility-oriented voice input and output.

This policy does not define agent reasoning, mission approval, memory storage, doctrine editing, or task execution.

## Speech-to-text

Speech-to-text converts user voice into plain text.

Pipeline:

```text
User voice
  -> speech-to-text
  -> plain text input
  -> normal Konoha mission flow
```

Rules:

- STT must not store raw audio.
- STT must not store transcripts by itself.
- STT must not infer intent beyond transcription.
- STT must not approve actions.
- STT must not trigger execution directly.
- STT output must enter Konoha as normal user text.
- If the transcribed text is unclear, incomplete, or ambiguous, the system must ask for clarification.

## Text-to-speech

Text-to-speech reads written Konoha output aloud.

Pipeline:

```text
Agent text output
  -> text-to-speech
  -> audio playback
```

Rules:

- TTS must not change the written content.
- TTS must not summarize or rephrase unless another approved agent produced that text first.
- TTS must not store generated audio.
- TTS must not create memory entries.
- The written output remains authoritative.
- If text and audio conflict, the written output wins.

## No storage by default

The Voice Layer must not store:

- raw microphone audio;
- generated speech audio;
- transcripts as an independent memory source;
- voice metadata that can identify the speaker;
- background audio.

If a Village wants to save transcripts, that must happen through the normal Konoha memory flow after explicit approval and must be treated like typed text, not as Voice Layer storage.

## Confirmations and approvals

Voice input does not bypass approval.

Sensitive actions still require the approval level defined by the Approval Policy, Mission Charter, Safety Policy, and local Village rules.

Examples of sensitive actions:

- editing files;
- deleting files;
- running commands;
- installing dependencies;
- committing or pushing to Git;
- reading private files;
- using sensitive context;
- modifying memory;
- modifying doctrine.

For sensitive actions, the system must present the transcribed request as text and require the appropriate approval before proceeding.

## Notifications

Voice or sound notifications may be used to alert the user when input is required.

Rules:

- notification sounds may indicate that input is needed;
- notification sounds must not include private mission content by default;
- urgent notification behavior must be configurable;
- quiet hours and maximum reminders should be respected when configured;
- notifications do not imply approval or completion.

## Teachback

Voice may be used during Teachback.

Pipeline:

```text
Konoha explanation
  -> optional TTS playback
  -> user spoken explanation
  -> STT transcription
  -> normal Teachback evaluation
```

Rules:

- the user's spoken explanation must be transcribed before evaluation;
- the transcript is evaluated as normal text;
- the Voice Layer does not decide whether the user understood;
- the Teachback Policy controls mission completion.

## Local configuration

Voice settings should be configured per Local Village.

Example:

```yaml
voice:
  enabled: true

  input:
    enabled: true
    language: "auto"
    require_text_confirmation_for_sensitive_actions: true

  output:
    enabled: true
    read_agent_responses: false
    read_waiting_input_alerts: true
    read_urgent_alerts: true

  storage:
    save_audio: false
    save_transcripts_by_voice_layer: false

  privacy:
    local_only_preferred: true
    never_record_background_audio: true
```

## Local and external services

Local voice models are preferred when available.

External STT or TTS services may only be used when explicitly configured and approved by the user or Local Village.

If external services are used, the system must disclose that audio or text may leave the local machine before use.

## Relationship with other policies

This policy does not override:

- Konoha Laws;
- Safety Policy;
- Context Policy;
- Approval Policy;
- Mission Charter Policy;
- Teachback Policy;
- Yamanaka Memory Policy;
- local Village rules.

If any policy conflicts with Voice Layer convenience, the stricter policy wins.

## Violations

The following are violations:

- storing raw audio without explicit approval;
- using voice input to bypass approval;
- treating transcription as confirmed when it is unclear;
- allowing TTS to alter the written output;
- saving voice transcripts outside the normal memory flow;
- using external voice services without disclosure and approval;
- letting voice commands execute sensitive actions directly.

## Completion checklist

Before enabling Voice Layer in a Village, confirm:

- voice input is optional;
- voice output is optional;
- raw audio is not stored;
- TTS does not modify output;
- STT output enters the normal text flow;
- sensitive actions still require approval;
- external services are disabled or explicitly approved;
- local settings are documented.
