# Local Village Bootstrap Review Scroll

Use this Scroll to review Local Village bootstrap and hardware profile outputs.

## Review questions

1. Was the Village root explicit?
2. Was the operation previewed before confirmation?
3. Was the exact approval token used?
4. Did the profile avoid reading project files, `.env`, credentials, emails, and user documents?
5. Did the bootstrap write only under the explicit Village root?
6. Does the config say private context access is blocked by default?
7. Does the report state that local config does not authorize execution?
8. Are public templates generic and license-safe?
9. Is the Local Village path ignored or clearly private?
10. Are no Git, model, adapter, network, or repository apply actions performed?

## Required non-authority language

```text
Private context stays local.
Hardware profile is evidence only.
Local config is not permission.
```

## Stop conditions

Stop review if:

- private context is committed;
- credentials are read or copied;
- `.env` is read;
- arbitrary directories are scanned;
- command execution is introduced;
- network access is introduced;
- Git operations are introduced;
- local config is treated as permission.

## Verdict

A Local Village bootstrap may pass only when it creates private scaffolding and evidence, not new authority.
