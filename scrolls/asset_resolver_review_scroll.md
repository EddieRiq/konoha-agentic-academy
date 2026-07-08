# Asset Resolver Review Scroll

Use this Scroll to review Konoha asset resolver changes.

## Review checks

```text
1. Logical asset names are explicit and safe.
2. Resolution order is local_village -> user -> public_generic -> text_fallback.
3. Public assets are generic, original, and license-safe.
4. Local/private assets are not committed.
5. Path traversal is blocked.
6. Private paths are redacted by default.
7. The resolver does not execute commands.
8. The resolver does not use network access.
9. The resolver does not invoke models or adapters.
10. Asset display is not treated as permission.
```

## Required statement

```text
UI display is evidence only.
A visual asset is not permission.
```

## Blockers

Stop the release if:

```text
copyrighted/protected assets are committed
local Village assets are committed
asset paths can escape configured roots
the resolver executes shell commands
the resolver fetches remote assets
the UI treats visual state as approval
```
