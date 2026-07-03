# Repository audit checklist

This guide defines a manual audit for checking whether the repository structure is coherent.

## Core rule

Audit before release.

Do not assume the tree is coherent because files exist.

## When to use

Use this checklist after:

- adding many files;
- moving templates;
- adding Scrolls;
- creating Clans;
- changing README files;
- preparing a release;
- onboarding a new agent.

## Tree command

PowerShell:

```powershell
tree /F /A
```

WSL:

```bash
find . -not -path "./.git/*" -print | sort
```

If `tree` is installed in WSL:

```bash
tree -a -I ".git"
```

## Root checks

The root should clearly expose:

- `README.md`;
- `LICENSE`;
- `CHANGELOG.md`;
- `AGENTS.md`;
- `.gitignore`;
- `.gitattributes`;
- main folders.

## Folder checks

Check that each main folder has a purpose:

- `core/`;
- `protocols/`;
- `hokage/`;
- `kagebunshin/`;
- `jounin/`;
- `shikamaru/`;
- `council/`;
- `memory/`;
- `missions/`;
- `scrolls/`;
- `clans/`;
- `docs/`;
- `alliance/`;
- `adapters/`;
- `tools/`;
- `evals/`;
- `sandbox/`;
- `telemetry/`;
- `ui/`;
- `shinobi/`;
- `marketplace/`.

## File naming checks

Prefer:

- lowercase file names;
- underscores for multiword policy files;
- `README.md` for folder entry points;
- `_template.md` for templates;
- `_scroll.md` for Scrolls;
- `_policy.md` for policies.

Avoid mixing naming styles without reason.

## Doctrine consistency checks

Confirm that docs do not contradict:

- no assumptions;
- safety overrides autonomy;
- Mission Charter before execution;
- memory does not authorize action;
- learning does not rewrite doctrine;
- local context stays local;
- review depends on risk;
- teachback is required for completion.

## Public safety checks

Confirm the repo does not include:

- private Village context;
- real credentials;
- local secrets;
- customer data;
- private company data;
- copyrighted books or converted paid material;
- franchise specific assets;
- raw logs with sensitive paths;
- generated outputs that should be ignored.

## Navigation checks

A new user should be able to answer:

- what is this repo;
- where do agents start;
- how does a mission start;
- how does review work;
- where are templates;
- where are Scrolls;
- how to create a local Village;
- what must stay private.

## README update checks

After adding new files, check whether these need updates:

- root `README.md`;
- `scrolls/README.md`;
- `clans/README.md`;
- `docs/guides/README.md`;
- `evals/README.md`;
- `CHANGELOG.md`;
- `docs/roadmap.md`.

## Audit result

Use one of:

```text
ready
ready-with-notes
not-ready
blocked
```

## Report format

```text
Tree reviewed:
Missing files:
Duplicated or confusing files:
README updates needed:
Safety concerns:
Naming concerns:
Recommended changes:
Verdict:
```
