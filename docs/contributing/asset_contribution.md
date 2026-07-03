# Asset contribution guide

This guide defines how visual, audio, terminal, ASCII, palette, and theme assets may be contributed to Konoha Agentic Academy.

## Purpose

Konoha may include visual and audio assets to make agent activity easier to understand. These assets support the UI, notifications, telemetry, and Shinobi presentation layer.

Assets are presentation only. They do not authorize actions, change mission scope, approve work, modify doctrine, or affect agent permissions.

## Core rules

Public assets must be original, generic, or license-safe.

Konoha must not ship copyrighted character assets, recognizable franchise designs, protected logos, voice lines, music, sound effects, screenshots, sprites, fan edits, or assets copied from commercial media.

Local Village assets may override public assets, but local assets that reference protected characters, voices, logos, music, or franchise-specific designs must remain private and must not be committed to the public repository.

## Public repository assets

The public repository may include:

- generic terminal layouts;
- generic ninja-village-inspired backgrounds;
- original ASCII art;
- original icons and status markers;
- original notification sounds;
- license-safe palettes;
- placeholder avatars;
- abstract symbols;
- documentation examples using safe assets.

The public repository must not include:

- copyrighted characters;
- recognizable anime, manga, game, movie, or comic designs;
- franchise-specific voices or quotes;
- protected logos;
- copyrighted music or sound effects;
- screenshots or traced artwork;
- assets generated from prompts that explicitly imitate a protected character or franchise style;
- files with unclear license or provenance.

## Local Village assets

Local Villages may define their own private assets under their local ignored folders.

Example:

```text
alliance/<village>/assets/
  ascii/
  sounds/
  palettes/
  themes/
```

These assets are user responsibility and must remain outside the public repository when they include copyrighted, private, sensitive, or project-specific content.

Public Konoha assets are safe defaults. Local Village assets are private overrides.

## Asset resolution

The UI should resolve assets in this order:

1. Local Village assets.
2. User-level assets.
3. Public generic Shinobi assets.
4. Text-only fallback.

If a local asset exists for the requested logical asset name, it may override the generic asset. If it does not exist, Konoha must fall back safely.

Example logical asset name:

```text
avatar.kagebunshin.coding
```

Possible local path:

```text
alliance/kirigakure/assets/ascii/avatars/kagebunshin_coding.txt
```

Possible public fallback:

```text
shinobi/assets/generic/ascii/avatars/worker_coding.txt
```

If neither exists, the UI may render:

```text
[worker: coding]
```

## Required metadata

Every contributed public asset should include clear provenance.

Minimum metadata:

```yaml
asset_name:
asset_type:
created_by:
license:
source:
safe_for_public_repo: true
description:
```

For generated assets, include:

```yaml
generated: true
tool:
prompt_summary:
human_reviewed: true
```

Do not include full prompts if they contain private context or protected franchise imitation.

## License requirements

Public assets should use a license compatible with the repository license.

Preferred options:

- original project asset under the repository license;
- Creative Commons license that allows redistribution and modification;
- public domain or equivalent;
- explicitly permissioned asset with included proof.

Do not contribute assets with uncertain licensing.

If license is unclear, the asset is rejected or kept local only.

## ASCII art rules

ASCII art must be original or license-safe.

Allowed:

- original generic avatars;
- generic cubicles;
- generic mission boards;
- abstract alert icons;
- generic village backgrounds;
- original symbolic effects.

Not allowed in the public repo:

- traced character silhouettes;
- recognizable hairstyles, outfits, symbols, or poses from protected characters;
- copied ASCII art from websites without compatible license;
- direct references to protected catchphrases or scenes.

## Sound rules

Public sounds must be original or license-safe.

Allowed:

- simple generated pings;
- original notification tones;
- original completion sounds;
- abstract alert sounds.

Not allowed in the public repo:

- anime voice clips;
- quotes from shows, movies, or games;
- copyrighted soundtracks;
- ripped game sounds;
- celebrity or character voice imitation;
- generated voice lines imitating a protected character.

## Palette and theme rules

Themes may be inspired by broad concepts, but must not copy protected visual identity.

Allowed:

- terminal dark;
- mist;
- forest;
- sand;
- storm;
- academy;
- minimal;
- high contrast.

Not allowed:

- palettes named after protected characters or franchises when used to imitate them;
- exact color schemes designed to reproduce a protected brand identity;
- logos or symbols from protected works.

## Contribution workflow

Asset contributions follow this flow:

1. Contributor proposes the asset and metadata.
2. Shikamaru checks naming, folder placement, and documentation.
3. Jounin reviews safety, license, and public suitability.
4. Hokage confirms whether the asset fits project scope.
5. Human maintainer approves merge.

Assets with unclear provenance must not be merged.

## Private assets accidentally committed

If private or copyrighted assets are committed by mistake:

1. Stop.
2. Remove the asset from the working tree.
3. Do not copy, preview, or redistribute it unnecessarily.
4. Notify the maintainer.
5. If needed, purge from Git history.
6. Add or tighten `.gitignore` rules.
7. Record a sanitized incident note only if appropriate.

## Sensitive content

Assets must not contain:

- personal data;
- corporate data;
- screenshots of private systems;
- emails;
- credentials;
- file paths that expose private infrastructure;
- internal logos or branding unless explicitly approved for public release.

## Local-only examples

A contributor may document how local overrides work without committing local assets.

Allowed:

```text
Place your private avatar at:
alliance/<village>/assets/ascii/avatars/kagebunshin_coding.txt
```

Not allowed:

```text
Here is a private copyrighted avatar committed as an example.
```

## Review checklist

Before accepting a public asset, confirm:

- the asset is original, generic, or license-safe;
- provenance is documented;
- license is compatible;
- no protected characters, logos, music, voice lines, or franchise-specific designs are included;
- no sensitive or private content is present;
- file size is reasonable;
- naming follows logical asset conventions;
- text-only fallback still works;
- local overrides remain ignored by Git.

## Relationship with other doctrine

This guide extends:

- `core/laws/KONOHA_LAWS.md`
- `core/conduct/AGENT_CONDUCT.md`
- `protocols/safety/safety_policy.md`
- `shinobi/README.md`
- `ui/README.md`

If there is a conflict, safety rules and Konoha Laws win.
