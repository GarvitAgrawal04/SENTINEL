#!/usr/bin/env bash
# One command: create the virtual environment, install pinned dependencies, create .env, start the API.
#
#   bash setup.sh                  set everything up, then serve http://127.0.0.1:8000
#   bash setup.sh --install-only   set everything up and stop
#   bash setup.sh --test           set everything up and run the test suite
#   PORT=8001 bash setup.sh        use another port        PYTHON=python3.12 bash setup.sh   pick an interpreter
#
# Works on macOS, Linux and Git Bash on Windows. Needs only Python 3.10+ and Git.
set -eu
cd "$(dirname "$0")"

say()  { printf '\033[1m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# 1. find a Python that is new enough ------------------------------------------------------------------------------
PY=""
for candidate in "${PYTHON:-}" python3 python py; do
  [ -n "$candidate" ] || continue
  if command -v "$candidate" >/dev/null 2>&1 && \
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PY="$candidate"; break
  fi
done
[ -n "$PY" ] || fail "Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/ and run this again."
say "Using $("$PY" --version 2>&1) ($PY)"

# 2. virtual environment -------------------------------------------------------------------------------------------
if [ ! -d .venv ]; then
  say "Creating the virtual environment in .venv"
  "$PY" -m venv .venv || fail "could not create a virtual environment. On Debian/Ubuntu run: sudo apt install python3-venv"
fi
if   [ -f .venv/bin/activate ];     then . .venv/bin/activate          # macOS, Linux
elif [ -f .venv/Scripts/activate ]; then . .venv/Scripts/activate      # Git Bash on Windows
else fail ".venv exists but has no activate script. Delete the .venv folder and run this again."; fi

# 3. dependencies (pinned) -----------------------------------------------------------------------------------------
say "Installing dependencies"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements-dev.txt
python -m pip install --quiet --no-deps -e .           # puts the `sentinel` command on PATH inside the venv

# 4. .env ----------------------------------------------------------------------------------------------------------
if [ ! -f .env ]; then
  cp .env.example .env
  say "Created .env from .env.example (nothing in it is required; see the comments inside)"
fi
while IFS= read -r line || [ -n "$line" ]; do            # export KEY=value pairs; tolerate Windows line endings
  line="${line%$(printf '\r')}"
  case "$line" in ''|\#*) continue ;; esac
  key="${line%%=*}"; value="${line#*=}"
  case "$key" in ''|*[!A-Za-z0-9_]*) continue ;; esac
  if [ -n "$value" ] && [ -z "$(eval "printf '%s' \"\${$key:-}\"")" ]; then export "$key=$value"; fi
done < .env

# 5. go ------------------------------------------------------------------------------------------------------------
say "Self-test"
python -m sentinel.cli selftest | tail -n 1

case "${1:-}" in
  --install-only) say "Done. Activate with: source .venv/bin/activate   then try: sentinel scan ."; exit 0 ;;
  --test)         exec python -m pytest -q ;;
esac

HOST="${HOST:-127.0.0.1}"; PORT="${PORT:-8000}"
say "Starting the API on http://$HOST:$PORT   (interactive docs: http://$HOST:$PORT/docs, stop with Ctrl+C)"
exec python -m uvicorn sentinel.api:app --host "$HOST" --port "$PORT"
