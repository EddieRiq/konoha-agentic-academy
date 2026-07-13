#!/usr/bin/env bash
set -euo pipefail

VERSION="v3.3.0"
REPOSITORY="https://github.com/EddieRiq/konoha-agentic-academy.git"
INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/konoha-agentic-academy"
BIN_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
STATE_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/konoha/install.json"
CONFIRM_INSTALL="false"
APPROVAL_TOKEN=""
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
  cat <<'EOF'
Konoha Agentic Academy managed terminal installer

Usage:
  install.sh \
    --version v3.3.0 \
    --confirm-install \
    --approval-token INSTALL_KONOHA_CLI

Options:
  --version <vMAJOR.MINOR.PATCH>
  --repository <git-url>
  --install-root <absolute-or-home-relative-path>
  --bin-dir <path>
  --state-file <path>
  --python <python3-executable>
  --confirm-install
  --approval-token <token>
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      VERSION="${2:?missing version}"
      shift 2
      ;;
    --repository)
      REPOSITORY="${2:?missing repository}"
      shift 2
      ;;
    --install-root)
      INSTALL_ROOT="${2:?missing install root}"
      shift 2
      ;;
    --bin-dir)
      BIN_DIR="${2:?missing bin dir}"
      shift 2
      ;;
    --state-file)
      STATE_FILE="${2:?missing state file}"
      shift 2
      ;;
    --python)
      PYTHON_BIN="${2:?missing python executable}"
      shift 2
      ;;
    --confirm-install)
      CONFIRM_INSTALL="true"
      shift
      ;;
    --approval-token)
      APPROVAL_TOKEN="${2:?missing approval token}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'BLOCKED: unknown installer argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

case "$VERSION" in
  v[0-9]*.[0-9]*.[0-9]*) ;;
  *)
    printf 'BLOCKED: version must use vMAJOR.MINOR.PATCH\n' >&2
    exit 2
    ;;
esac

if [ "$CONFIRM_INSTALL" != "true" ]; then
  printf 'BLOCKED: --confirm-install is required\n' >&2
  exit 1
fi

if [ "$APPROVAL_TOKEN" != "INSTALL_KONOHA_CLI" ]; then
  printf 'BLOCKED: --approval-token INSTALL_KONOHA_CLI is required\n' >&2
  exit 1
fi

if [ "$REPOSITORY" != "https://github.com/EddieRiq/konoha-agentic-academy.git" ]; then
  printf 'BLOCKED: repository must be the canonical public Konoha repository\n' >&2
  exit 1
fi

for command in git "$PYTHON_BIN"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'BLOCKED: required command not found: %s\n' "$command" >&2
    exit 1
  fi
done

if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
  printf 'BLOCKED: Python venv support is required\n' >&2
  exit 1
fi

INSTALL_ROOT="$("$PYTHON_BIN" - "$INSTALL_ROOT" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"
BIN_DIR="$("$PYTHON_BIN" - "$BIN_DIR" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"
STATE_FILE="$("$PYTHON_BIN" - "$STATE_FILE" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).expanduser().resolve())
PY
)"

HOME_RESOLVED="$("$PYTHON_BIN" - <<'PY'
from pathlib import Path
print(Path.home().resolve())
PY
)"

case "$INSTALL_ROOT" in
  "$HOME_RESOLVED"/*) ;;
  *)
    printf 'BLOCKED: install root must stay under current user home\n' >&2
    exit 1
    ;;
esac

case "$BIN_DIR" in
  "$HOME_RESOLVED"/*) ;;
  *)
    printf 'BLOCKED: bin dir must stay under current user home\n' >&2
    exit 1
    ;;
esac

case "$STATE_FILE" in
  "$HOME_RESOLVED"/*) ;;
  *)
    printf 'BLOCKED: state file must stay under current user home\n' >&2
    exit 1
    ;;
esac

if [ -e "$INSTALL_ROOT" ]; then
  printf 'BLOCKED: install root already exists: %s\n' "$INSTALL_ROOT" >&2
  printf 'Use `konoha upgrade` for an existing managed installation.\n' >&2
  exit 1
fi

if [ -e "$STATE_FILE" ]; then
  printf 'BLOCKED: managed state already exists: %s\n' "$STATE_FILE" >&2
  exit 1
fi

WRAPPER="$BIN_DIR/konoha"
if [ -e "$WRAPPER" ] || [ -L "$WRAPPER" ]; then
  printf 'BLOCKED: command path already exists: %s\n' "$WRAPPER" >&2
  exit 1
fi

mkdir -p "$(dirname "$INSTALL_ROOT")" "$BIN_DIR" "$(dirname "$STATE_FILE")"

cleanup() {
  rc=$?
  if [ "$rc" -ne 0 ]; then
    rm -f "$WRAPPER" "$STATE_FILE"
    rm -rf "$INSTALL_ROOT"
  fi
  exit "$rc"
}
trap cleanup EXIT

git clone \
  --quiet \
  --depth 1 \
  --branch "$VERSION" \
  "$REPOSITORY" \
  "$INSTALL_ROOT"

TAG_TARGET="$(git -C "$INSTALL_ROOT" rev-parse "${VERSION}^{}" 2>/dev/null || true)"
if [ -z "$TAG_TARGET" ]; then
  TAG_TARGET="$(git -C "$INSTALL_ROOT" rev-parse HEAD)"
fi
HEAD_COMMIT="$(git -C "$INSTALL_ROOT" rev-parse HEAD)"
TAG_TYPE="$(git -C "$INSTALL_ROOT" cat-file -t "$VERSION")"

if [ "$TAG_TYPE" != "tag" ]; then
  printf 'BLOCKED: requested version is not an annotated tag\n' >&2
  exit 1
fi

if [ "$HEAD_COMMIT" != "$TAG_TARGET" ]; then
  printf 'BLOCKED: cloned HEAD does not match requested tag\n' >&2
  exit 1
fi

GIT_EXCLUDE="$INSTALL_ROOT/.git/info/exclude"
for pattern in "/.venv/" "/.konoha-managed-install.json"; do
  if ! grep -Fqx "$pattern" "$GIT_EXCLUDE" 2>/dev/null; then
    printf '%s\n' "$pattern" >>"$GIT_EXCLUDE"
  fi
done

"$PYTHON_BIN" -m venv "$INSTALL_ROOT/.venv"

VENV_PYTHON="$INSTALL_ROOT/.venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
  printf 'BLOCKED: virtual environment python missing\n' >&2
  exit 1
fi

MARKER_ID="$("$VENV_PYTHON" - <<'PY'
import uuid
print(uuid.uuid4().hex)
PY
)"

WRAPPER_TMP="$BIN_DIR/.konoha.tmp.$$"

cat >"$WRAPPER_TMP" <<EOF
#!/usr/bin/env sh
exec env PYTHONDONTWRITEBYTECODE=1 "$VENV_PYTHON" "$INSTALL_ROOT/tools/konoha_cli.py" "\$@"
EOF
chmod 0755 "$WRAPPER_TMP"
mv "$WRAPPER_TMP" "$WRAPPER"

WRAPPER_SHA256="$("$VENV_PYTHON" - "$WRAPPER" <<'PY'
import hashlib
import sys
from pathlib import Path

digest = hashlib.sha256()
with Path(sys.argv[1]).open("rb") as handle:
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
print(digest.hexdigest())
PY
)"

INSTALLED_AT="$("$VENV_PYTHON" - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).replace(microsecond=0).isoformat())
PY
)"

"$VENV_PYTHON" - \
  "$STATE_FILE" \
  "$INSTALL_ROOT" \
  "$INSTALL_ROOT/.venv" \
  "$WRAPPER" \
  "$MARKER_ID" \
  "$WRAPPER_SHA256" \
  "$VERSION" \
  "$HEAD_COMMIT" \
  "$INSTALLED_AT" <<'PY'
import json
import os
import sys
from pathlib import Path

(
    state_file,
    install_root,
    venv_root,
    bin_path,
    marker_id,
    wrapper_sha256,
    version,
    commit,
    installed_at,
) = sys.argv[1:]

payload = {
    "schema_version": "1.0.0",
    "report_type": "managed_konoha_install_state",
    "managed": True,
    "repository": "EddieRiq/konoha-agentic-academy",
    "version": version,
    "commit": commit,
    "install_root": install_root,
    "venv_root": venv_root,
    "bin_path": bin_path,
    "state_file": state_file,
    "marker_id": marker_id,
    "wrapper_sha256": wrapper_sha256,
    "installed_at": installed_at,
}

def atomic_write(path, data):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temp, target)

atomic_write(state_file, payload)
atomic_write(
    Path(install_root) / ".konoha-managed-install.json",
    {
        "schema_version": "1.0.0",
        "report_type": "managed_konoha_install_marker",
        "repository": payload["repository"],
        "version": version,
        "commit": commit,
        "install_root": install_root,
        "marker_id": marker_id,
        "wrapper_sha256": wrapper_sha256,
        "installed_at": installed_at,
    },
)
PY

OBSERVED_VERSION="$("$WRAPPER" --version)"
if [ "$OBSERVED_VERSION" != "${VERSION#v}" ]; then
  printf 'BLOCKED: installed command version mismatch\n' >&2
  exit 1
fi

"$WRAPPER" --validate-registry >/dev/null

trap - EXIT

printf 'KONOHA TERMINAL INSTALLATION PASSED\n'
printf 'version: %s\n' "$VERSION"
printf 'commit: %s\n' "$HEAD_COMMIT"
printf 'command: %s\n' "$WRAPPER"
printf 'state: %s\n' "$STATE_FILE"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    printf 'PATH NOTICE: add %s to PATH\n' "$BIN_DIR"
    ;;
esac
