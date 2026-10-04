# Konoha Interactive Shell

The Interactive Shell is the normal `konoha` entry when both standard input
and standard output are human TTYs. From a project directory:

```bash
cd <repo>
konoha
```

You can also request it explicitly with `konoha shell`. With non-TTY input or
output, the existing conversational CLI behavior remains in place. Explicit
CLI commands and scripts remain available.

## Project and workspace boundary

At startup, the shell reads Git metadata such as the repository root, branch,
worktree status, and origin identity. It sanitizes terminal-facing metadata.
It does not read repository files or inspect mission/provider readiness.
Detecting a project does not grant permission to inspect its contents, invoke a
model, or mutate files.

Project state is scoped under the user state directory, normally
`${XDG_STATE_HOME:-~/.local/state}/konoha/projects/<project-id>`. The shell
asks before creating a missing project workspace. Declining leaves it
uncreated and does not submit the pending natural-language request. By
default, workspace state is kept outside the repository. `KONOHA_PROJECT_STATE_ROOT`
or `KONOHA_STATE_ROOT` can explicitly override the state root.

Natural-language requests enter the existing supervised flows. They express
intent only; plan approval, execution approval, review, Teachback, and mission
closure remain separate gates.

## Shell controls

Enter each control as its own line:

| Control | Action |
| --- | --- |
| `:help` | Show shell controls and input guidance. |
| `:status` | Refresh and display safe project metadata and workspace status. |
| `:study` | Start the existing bounded repository study. A missing workspace requires confirmation first. |
| `:mission` | Explain how to enter a natural-language mission, ending with `:fin`. |
| `:review` | Explain the current review view limitation; it records no review evidence. |
| `:providers` | Show local provider executable presence only; it does not invoke providers or check authentication. |
| `:memory` | Show whether local project state exists; it does not read private memory. |
| `:git` | Refresh and display safe Git metadata. |
| `:exit` | Close the shell cleanly. |

Colon controls are recognized as shell controls only in the Interactive Shell.
Legacy conversation framing remains compatible; mission text continues to use
the existing `:fin` terminator.

## Display options and local art

- `--no-splash` suppresses the wordmark and mascot.
- `--no-color` disables terminal color.
- `NO_COLOR` disables color when set.
- `KONOHA_NO_SPLASH` suppresses the splash when set.
- `KONOHA_ART_DIR` optionally points to a local directory of images. If the
  directory contains supported image files and `chafa` is already installed,
  Konoha may render the first eligible local image. Symlinked images are
  ignored. Missing art or `chafa` falls back to the built-in generic text
  mascot.

Konoha never installs or downloads `chafa` or artwork automatically. The
shipped wordmark and text mascots are original generic designs; no
franchise artwork is included.

## Compatibility and limits

The shell is a terminal interface over existing supervised workflows. Startup
does not invoke a provider, create a workspace without confirmation, or grant
repository access. The shell does not provide a Web UI, daemon, or background
autonomy. Its review view is informational and does not read or record review
state.
