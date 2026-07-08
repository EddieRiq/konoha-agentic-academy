# Asset Resolver and Local Visual Layer

Konoha uses logical asset names instead of hard-coded file paths.

The resolver supports a local-first visual layer while keeping public assets generic, original, and license-safe.

## Core rule

```text
UI display is evidence only.
A visual asset is not permission.
```

## Resolution order

```text
1. local_village
2. user
3. public_generic
4. text_fallback
```

Examples:

```text
status.waiting_user_input
status.waiting_approval
status.blocked
status.ready_for_review
status.ready_for_teachback
status.closed
avatar.kagebunshin.coding
background.cubicles_active
```

## Public asset policy

Public assets must be generic and original.

Public assets must not include:

```text
copyrighted character art
franchise logos
recognizable protected designs
voice lines
soundtrack material
private local assets
company-private assets
```

## Local asset policy

Local Village assets may override public generic assets from ignored local paths.

Example:

```text
alliance/kirigakure/assets/
```

Local assets must not be committed to the public repository.

## CLI

Resolve an asset:

```powershell
python .\tools\assets\resolve_asset.py `
  --logical-name "status.waiting_user_input" `
  --repo-root "." `
  --sandbox-root ".\sandbox" `
  --write-report `
  --json
```

Resolve with a local Village override:

```powershell
python .\tools\assets\resolve_asset.py `
  --logical-name "status.waiting_user_input" `
  --repo-root "." `
  --village-assets-root ".\alliance\kirigakure\assets" `
  --sandbox-root ".\sandbox" `
  --json
```

## Safety boundary

The resolver may:

```text
read configured asset registries
read registered asset files
prefer local assets over user assets
prefer user assets over public assets
fallback to text when no asset exists
write an asset resolution report under sandbox reports
redact local/user paths by default
```

The resolver may not:

```text
execute commands
invoke models
invoke adapters
use network access
apply files to the repository
stage files
commit files
push files
access private context beyond configured asset roots
treat UI display as approval
close missions
```

## UI relationship

The Local Web UI may call the asset service to display logical assets for mission states.

The UI must not treat rendered assets as permission.
