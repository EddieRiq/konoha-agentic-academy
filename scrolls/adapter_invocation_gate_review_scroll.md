# Adapter Invocation Gate Review Scroll

Status: pre-release / review Scroll.

## Purpose

Review Adapter Invocation Gate behavior before any adapter-shaped workflow is accepted.

## Review checklist

Confirm that:

- real adapter execution remains disabled by default;
- mock invocation requires explicit confirmation;
- mock invocation requires the exact `INVOKE_ADAPTER_GATE` approval token;
- mock invocation requires `--enable-mock-adapter`;
- outputs are written only inside the sandbox run;
- outputs are marked as review-required;
- the gate does not execute shell commands;
- the gate does not use network access;
- the gate does not perform Git operations;
- the gate does not access private Village context;
- real adapter requests are blocked.

## Required evidence

A review should include:

- command used;
- run ID;
- whether invocation was preview or confirmed;
- report path;
- output path if mock invocation occurred;
- test results;
- safety grep result.

## Blockers

Block the release if:

- a real adapter can be invoked;
- network access is used;
- shell execution is introduced;
- output can escape the sandbox run;
- missing approval still invokes the mock adapter;
- private or ignored paths are read as context;
- Git operations are performed.

## Closure

This Scroll does not authorize adapter execution. It only reviews whether the gate preserves the disabled-by-default adapter boundary.
