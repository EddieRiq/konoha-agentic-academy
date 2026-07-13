# Finished Local-First Terminal Product

Konoha v3.4.0 presents one user-facing command:

```bash
konoha
```

The default invocation inspects local product readiness and prints one next
action. It does not authorize that action.

## First use

```bash
konoha quickstart \
  --confirm-quickstart \
  --approval-token START_KONOHA_QUICKSTART
```

Quickstart creates only the configured workspace below `sandbox/`. It does not
start a mission, invoke a model, enable network, modify Git, or read private
memory.

Then:

```bash
konoha next
konoha mission start --help
```

## Product flow

```text
quickstart
  ↓
mission start
  ↓
mission plan / explicitly approved execution
  ↓
human review
  ↓
Teachback
  ↓
human closure
  ↓
next mission
```

At any point:

```bash
konoha next
konoha status
konoha doctor
konoha shell
```

## Help surfaces

```bash
konoha help
konoha help mission
konoha help maintainer
konoha help --all
```

The default help hides package and release maintenance commands. It also hides
deprecated compatibility commands unless `--all` is requested.

## Error recovery

Unknown commands show close matches and direct the operator to `konoha help`.
Managed installation status, upgrade and uninstall retain their explicit
safety gates.
