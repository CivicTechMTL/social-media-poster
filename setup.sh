# Set up the project and activate its virtual environment in the current shell.
#
#   source setup.sh        (or:  . setup.sh)
#
# Safe to re-run: it reuses .venv and only installs what's missing or out of date.
# Works on macOS/Linux and in Git Bash on Windows.

_ctmtl_setup() {
    local root
    root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)" || return 1

    # 1. Find a Python 3.10+ to build the venv with.
    local py=""
    for cand in python3 python py; do
        if command -v "$cand" >/dev/null 2>&1 &&
            "$cand" -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
            py="$cand"
            break
        fi
    done

    # 2. Create .venv if it doesn't exist.
    if [ ! -d "$root/.venv" ]; then
        if [ -z "$py" ]; then
            echo "✗ Python 3.10 or newer is required (https://www.python.org/downloads/)." >&2
            return 1
        fi
        echo "→ Creating .venv with $("$py" --version)"
        "$py" -m venv "$root/.venv" || return 1
    fi

    # 3. Activate it (Scripts/ on Windows, bin/ elsewhere).
    if [ -f "$root/.venv/Scripts/activate" ]; then
        . "$root/.venv/Scripts/activate"
    else
        . "$root/.venv/bin/activate"
    fi || return 1

    # 4. Python packages, then the headless Chromium used to render the images.
    echo "→ Installing Python packages"
    python -m pip install --quiet --upgrade pip || return 1
    python -m pip install --quiet -r "$root/requirements.txt" || return 1
    echo "→ Installing Chromium for Playwright"
    python -m playwright install chromium || return 1

    # 5. .env for Bluesky credentials.
    if [ ! -f "$root/.env" ]; then
        cp "$root/.env.example" "$root/.env"
        echo "→ Created .env from .env.example. Fill in BLUESKY_HANDLE and BLUESKY_APP_PASSWORD to post."
    fi

    echo "✓ Ready. The .venv is active in this shell; try: poe render data/100 (or poe to list tasks)"
}

# Being executed (not sourced) would set up everything but leave the venv inactive afterwards.
if [ -n "${BASH_SOURCE[0]:-}" ] && [ "${BASH_SOURCE[0]}" = "$0" ]; then
    echo "Note: run this as 'source setup.sh' so the venv stays active in your shell." >&2
fi

_ctmtl_setup
_ctmtl_status=$?
unset -f _ctmtl_setup
return $_ctmtl_status 2>/dev/null || exit $_ctmtl_status
