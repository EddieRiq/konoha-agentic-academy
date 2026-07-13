# Canonical Konoha CLI Entrypoint

Status: v3.2.6 canonical repository entrypoint.

```bash
konoha --help
```

The future `v3.3.0` distribution will expose the same registry through the
global `konoha` command. `v3.2.6` intentionally does not install anything into
`PATH`.

## Registry

Commands are defined in:

```text
tools/command_registry.py
```

Each entry declares:

```text
public command
delegated script
fixed non-authorizing arguments
mode
network boundary
approval token requirement
active or deprecated state
replacement when deprecated
```

Registry metadata is evidence only.

## Active surface

```bash
konoha doctor
konoha init
konoha status
konoha shell

konoha mission start
konoha mission run
konoha mission plan
konoha mission review
konoha mission teachback-prepare
konoha mission teachback
konoha mission teachback-status
konoha mission close
konoha mission status
konoha mission resume

konoha package status
konoha package install
konoha release status
```

## Delegation rules

The CLI:

- resolves only registered keys;
- constructs argv lists with `shell=False`;
- uses a fixed internal script path;
- propagates the delegated return code;
- does not inject approval tokens;
- does not add `--allow-network`;
- does not convert preview into apply;
- does not convert review display into approval;
- does not infer mission closure consent.

`package install` adds only the semantic `--apply` mode. The package installer
still requires its own explicit approval token.

`release status` adds only `--status`. Network remains optional and read-only
when the user explicitly supplies `--allow-network`.

## Registry inspection

```bash
konoha --registry-json
konoha --validate-registry
```

The validator checks active script paths and registry shape. Deprecated commands
remain compatibility routes and name their replacement.

## Versions

The repository CLI reports:

```bash
konoha --version
```

Expected for this release:

```text
3.2.6
```

The Product Runtime and historical tools may retain their own component
versions. They no longer compete as public entrypoints.

## Exit behavior

```text
0  delegated command passed
1  delegated gate blocked or failed
2  command resolution or CLI usage failed
```

## Boundary

The CLI improves coherence, not autonomy. The delegated tool remains the source
of truth for approval, path, filesystem, model, Git and network boundaries.
