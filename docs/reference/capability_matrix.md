# Konoha Capability Matrix

## Canonical operator surfaces

| Capability | Canonical command | Delegated component | Mutation | Network | Approval |
|---|---|---|---|---|---|
| Doctor | `doctor` | Product Runtime | read-only | blocked | none |
| Operator status | `status` | Hokage Shell | read-only | blocked | none |
| Terminal shell | `shell` | Hokage Shell | supervised local | explicit delegated only | delegated |
| Mission start | `mission start` | Beta Runtime | mission workspace | blocked | `START_BETA_MISSION` |
| Mission runtime | `mission run` | Unified Mission Runtime | mission workspace | blocked | `START_UNIFIED_MISSION_RUNTIME` |
| Mission plan | `mission plan` | Beta Runtime | mission workspace | blocked | `PLAN_BETA_MISSION` |
| Human review | `mission review` | Beta Runtime | human evidence | blocked | `RECORD_BETA_REVIEW` |
| Teachback | `mission teachback` | Teachback Gate | human evidence | blocked | `RECORD_TEACHBACK_EVIDENCE` |
| Mission closure | `mission close` | Mission Closure | mission + explicit memory | blocked | `CLOSE_MISSION_WITH_TEACHBACK` |
| Package status | `package status` | Package Installation | read-only | blocked | none |
| Package install | `package install` | Package Installation | exact manifest scope | blocked | `APPLY_SUPERVISED_PACKAGE_INSTALLATION` |
| Release status | `release status` | Release Workflow | read-only | optional read-only | none |

## Component roles

```text
tools/konoha_cli.py
  public repository entrypoint

tools/command_registry.py
  command and delegation metadata

tools/beta_runtime/run_konoha_beta.py
  supervised mission start, plan, evidence, review and Git gates

tools/mission_runtime/run_unified_mission.py
  mission charter, plan, proposals and runtime evidence

tools/hokage_shell/run_hokage_shell.py
  terminal UX, inspection, continuity and human review recording

tools/teachback/manage_teachback.py
  structured human understanding evidence

tools/mission_closure/close_mission.py
  evidence composition and final human closure

tools/package_installation/run_supervised_package_installation.py
  exact direct/helper/public package scope

tools/release_workflow/run_supervised_release.py
  Acceptance → Git → tag → GitHub Release closure
```

## Deprecated compatibility

Deprecated CLI commands remain routed only for compatibility. They are not the
recommended product surface. Their replacements are listed by:

```bash
python tools/konoha_cli.py --registry-json
```

## Authority

No row grants permission. The delegated tool validates all tokens, paths,
network flags and evidence.
