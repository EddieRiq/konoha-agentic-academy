# v3.4.0 Finished Terminal Product Review Scroll

## Product smoke

```bash
konoha --version
konoha
konoha help
konoha help mission
konoha help maintainer
konoha quickstart --help
konoha next --help
konoha doctor
konoha status
```

## Quickstart

```bash
konoha quickstart \
  --confirm-quickstart \
  --approval-token START_KONOHA_QUICKSTART

konoha next
```

Expected:

```text
QUICKSTART_READY
READY_FOR_FIRST_MISSION
```

## Safety review

Confirm:

- no approval token is injected by the registry;
- no command enables network automatically;
- workspace writes stay below `sandbox/`;
- quickstart does not start a mission;
- next-action output is evidence only;
- package and release commands are absent from default help;
- deprecated commands appear only in full help;
- installer resolves annotated tags without clone warnings;
- upgrade checks out the resolved commit quietly.

## Regression target

```text
53 canonical suites
470 tests
0 failures
0 errors
0 timeouts
```
