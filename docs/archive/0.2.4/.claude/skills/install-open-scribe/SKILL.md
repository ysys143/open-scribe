---
name: install-open-scribe
description: Install or reinstall open-scribe on macOS from this repo, including global secrets setup, .env wiring, make install with Python 3.13 workaround, scribe wrapper recovery, and shell aliases. Use when the user asks to install/setup/reinstall open-scribe on their machine, fix a broken install, or set up a fresh dev environment for this project.
---

# Install Open-Scribe (macOS, Local Dev Machine)

Step-by-step procedure verified on this machine. Follow stages in order. Each stage has a **verify** step — do not proceed until verification passes.

## Pre-flight checks

```bash
# Must be in project root (has Makefile, .env.example)
test -f Makefile && test -f .env.example || { echo "Not in open-scribe root"; exit 1; }

# Python 3.13 required (3.14+ breaks deps: python-dotenv, youtube-transcript-api)
/opt/homebrew/bin/python3.13 --version || brew install python@3.13

# System binaries required by yt-dlp postprocessing
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || brew install ffmpeg

# JS runtime required by yt-dlp n-challenge solver (see Stage 8 for why)
command -v deno >/dev/null || brew install deno

# Current install state (idempotency check)
ls ~/.local/share/open-scribe/.venv/bin/python 2>/dev/null && echo "ALREADY INSTALLED — confirm with user before reinstalling"
```

## Stage 1 — Global secrets store (skip if already set up)

Location: `~/.config/secrets/.env`. One global file, sourced by zsh into all child processes.

```bash
# Create with restrictive perms
mkdir -p ~/.config/secrets
chmod 700 ~/.config/secrets
touch ~/.config/secrets/.env
chmod 600 ~/.config/secrets/.env
```

Add loader to `~/.zshrc` (only if not already present — `grep -q "config/secrets/.env" ~/.zshrc` to check):

```bash
# Load global secrets (API keys, tokens) from ~/.config/secrets/.env
if [ -f "$HOME/.config/secrets/.env" ]; then
  set -a
  source "$HOME/.config/secrets/.env"
  set +a
fi
```

User edits `~/.config/secrets/.env` to add: `OPENAI_API_KEY=sk-...` (optionally `NOTION_API_KEY=`, `NOTION_DATABASE_ID=`).

**Verify:**
```bash
zsh -c 'source ~/.zshrc && [ -n "$OPENAI_API_KEY" ] && echo "OPENAI_API_KEY: SET (${#OPENAI_API_KEY} chars)" || echo "NOT SET"'
```

**Never echo secret values** when verifying. Use length-only output (`${#VAR}`) or `awk -F= '{print $1": SET ("length($2)" chars)"}'`.

## Stage 2 — Project `.env`

```bash
cp .env.example .env
chmod 600 .env

# Inject key from global secrets (without exposing it)
KEY=$(grep '^OPENAI_API_KEY=' "$HOME/.config/secrets/.env" | cut -d= -f2-)
[ -n "$KEY" ] && sed -i '' "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${KEY}|" .env
```

`.env` is gitignored. `config.py` uses `load_dotenv()` then `os.getenv()` — by default `load_dotenv()` does **not** override existing shell env vars, so the global secrets file always wins on conflict.

**Verify:**
```bash
awk -F= 'NF>=2 && $1=="OPENAI_API_KEY" {print $1": SET ("length($2)" chars)"}' .env
```

## Stage 3 — `make install` with Python 3.13 shim

`make install` uses bare `python3` (PATH-resolved). System default may be 3.14, which breaks deps. Prepend a shim dir that maps `python3 → python3.13`.

```bash
# Clean any prior failed install
rm -rf ~/.local/share/open-scribe

# Create shim
mkdir -p /tmp/py313-shim
ln -sf /opt/homebrew/bin/python3.13 /tmp/py313-shim/python3

# Run install
PATH="/tmp/py313-shim:$PATH" make install
```

**Expected partial failure:** `scripts/install.sh` runs `set -e` and tries to `mkdir ~/.config/fish/conf.d`. If `~/.config/fish/` is root-owned (common on macOS after some Homebrew flows), this fails with `Permission denied` and aborts `install.sh` **before** the wrapper script (`~/.local/bin/scribe`) is created. Exit code 2 is expected in that case — proceed to Stage 4.

**Verify what succeeded:**
```bash
ls ~/.local/share/open-scribe/.venv/bin/python     # should be symlink → python3.13
~/.local/share/open-scribe/.venv/bin/python --version  # should be 3.13.x
grep -q "OPEN_SCRIBE_HOME" ~/.zshrc && echo "zshrc block: OK"
ls ~/.local/bin/scribe 2>/dev/null || echo "wrapper missing → Stage 4"
```

## Stage 4 — Recover wrapper (only if missing after Stage 3)

```bash
cat > ~/.local/bin/scribe << 'EOF'
#!/bin/bash
INSTALL_DIR="${OPEN_SCRIBE_HOME:-$HOME/.local/share/open-scribe}"
if [[ -f "$INSTALL_DIR/scribe.sh" ]]; then
    source "$INSTALL_DIR/scribe.sh"
    scribe "$@"
else
    echo "❌ Error: open-scribe not found at $INSTALL_DIR"
    exit 1
fi
EOF
chmod +x ~/.local/bin/scribe
```

Cleanup shim: `rm -rf /tmp/py313-shim`

## Stage 5 — `scr` alias + zsh URL globbing fix

`scribe.sh` is auto-sourced by the Open-Scribe block in `~/.zshrc` (added by `install.sh`), so `scribe` becomes a shell function. Add aliases **after** that block.

**Critical**: zsh's `NOMATCH` option (on by default) treats `?` in YouTube URLs (`?si=...`, `?v=...`) as a glob char and refuses to run if no file matches. User would see `zsh: no matches found: https://...`. Fix by prepending `noglob` to the call site via alias.

Append to `~/.zshrc` (only if not already present — `grep -q "noglob scribe" ~/.zshrc`):

```
alias scribe='noglob scribe'
alias scr='noglob scribe'
```

The alias on `scribe` itself is safe — zsh expands aliases once per command line, so `scribe URL` → `noglob scribe URL`, where the second `scribe` resolves to the function (not re-expanded).

**Verify:**
```bash
zsh -i -c '
  source ~/.zshrc
  alias scribe
  alias scr
  noglob printf "%s\n" "https://youtu.be/abc?si=xyz"  # should print URL literally
'
```

## Stage 6 — Permission fix for scribe's cached env

On first `scribe` invocation, `scribe.sh:_initialize_env` creates `~/.open-scribe/.env` from the `OPENAI_API_KEY` env var, but with default umask perms (644 — world-readable). Tighten:

```bash
# Trigger creation if not yet run, then fix perms
zsh -c 'source ~/.zshrc; scribe --help >/dev/null 2>&1 || true'
[ -f ~/.open-scribe/.env ] && chmod 600 ~/.open-scribe/.env
ls -la ~/.open-scribe/.env  # expect -rw-------
```

## Stage 7 — YouTube cookies (required for actual YouTube use)

Since late 2024, YouTube blocks unauthenticated yt-dlp traffic with `Please sign in. Use --cookies-from-browser or --cookies for authentication`. The project supports this via `OPEN_SCRIBE_COOKIES_BROWSER` → yt-dlp's `cookiesfrombrowser` option (see `src/downloader.py:43`).

Pick the browser where the user is logged into YouTube. Detect what's available:

```bash
ls ~/Library/Application\ Support/Google/Chrome/Default/Cookies 2>/dev/null && echo "chrome: present"
ls ~/Library/Application\ Support/Firefox/Profiles/*/cookies.sqlite 2>/dev/null && echo "firefox: present"
ls ~/Library/Application\ Support/BraveSoftware/Brave-Browser/Default/Cookies 2>/dev/null && echo "brave: present"
ls -d ~/Library/Cookies 2>/dev/null && echo "safari: present"
```

Set in `~/.open-scribe/.env` (the runtime config file scribe sources every call — *not* the global secrets file, since this is config not secret):

```bash
BROWSER=chrome  # or firefox, safari, brave, edge
if grep -q '^OPEN_SCRIBE_COOKIES_BROWSER=' ~/.open-scribe/.env; then
  sed -i '' "s/^OPEN_SCRIBE_COOKIES_BROWSER=.*/OPEN_SCRIBE_COOKIES_BROWSER=${BROWSER}/" ~/.open-scribe/.env
else
  echo "OPEN_SCRIBE_COOKIES_BROWSER=${BROWSER}" >> ~/.open-scribe/.env
fi
chmod 600 ~/.open-scribe/.env
```

**macOS Chrome caveat**: Chrome encrypts cookies with a Keychain-stored key. On first `scribe` invocation a Keychain prompt will appear asking permission to read the cookie-encryption key — click **Always Allow**. Safari/Firefox don't have this step.

No `source ~/.zshrc` needed — `scribe.sh` re-reads `~/.open-scribe/.env` on every call (line 32: `export $(grep -v '^#' "$ENV_FILE" | xargs)`).

## Stage 8 — JavaScript runtime (required for YouTube n-challenge)

Since late 2025, YouTube serves media URLs with an obfuscated `n=` parameter that must be solved with JavaScript. Without a local JS runtime, yt-dlp falls back to "images only" formats — `WARNING: n challenge solving failed: ... Only images are available for download`.

yt-dlp's Python API default is `js_runtimes = {'deno': {}}` — i.e. it auto-detects **deno** in PATH but nothing else. Install deno via Homebrew (single ~30MB binary):

```bash
brew install deno
```

**Verify auto-detection:**
```bash
~/.local/share/open-scribe/.venv/bin/yt-dlp -v --cookies-from-browser chrome \
  --list-formats "https://youtu.be/<any-video-id>" 2>&1 \
  | grep -E "JS runtimes|Solving"
# Expect:
#   [debug] JS runtimes: deno-X.Y.Z
#   [youtube] [jsc:deno] Solving JS challenges using deno
```

**Alternative (no brew install)**: If user has node via nvm and refuses to install deno, patch `src/downloader.py:_base_opts()` to add:
```python
opts['js_runtimes'] = {'node': {}}
```
…then sync to install dir. Less robust — `js_runtimes` is a yt-dlp Python-API option (not read from `~/.config/yt-dlp/config`), so it must live in code, and nvm's node may move between versions.

## Final verification

```bash
zsh -i -c '
  source ~/.zshrc 2>/dev/null
  echo "=== scribe function ==="
  type scribe | head -1
  echo "=== scr alias ==="
  alias scr
  echo "=== OPENAI_API_KEY ==="
  [ -n "$OPENAI_API_KEY" ] && echo "SET (${#OPENAI_API_KEY} chars)" || echo "NOT SET"
  echo "=== scribe --help ==="
  scribe --help 2>&1 | head -5
'
```

All four sections must show success. `scribe --help` exits non-zero (argparse behavior) — that is **not** a failure; check the visible output instead.

## Known issues / gotchas

| Issue | Cause | Workaround |
|---|---|---|
| `youtube-transcript-api==1.2.2` fails to install | Requires Python `<3.14`; system has 3.14 | Stage 3 PATH shim with Python 3.13 |
| `mkdir: ~/.config/fish/conf.d: Permission denied` | `~/.config/fish/` owned by root from prior install | Ignore (we skip fish); user uses zsh. If needed: `sudo chown -R $USER ~/.config/fish` |
| Key rotation not picked up by scribe | `scribe.sh` caches key at `~/.open-scribe/.env`, only regenerates if file missing | `rm ~/.open-scribe/.env` after updating `~/.config/secrets/.env` |
| `~/.open-scribe/.env` is world-readable after first run | scribe.sh's env-var path skips `chmod 600` (only the interactive prompt path sets it) | Stage 6 |
| `cp -r * $(INSTALL_DIR)/` in Makefile doesn't copy `.env` | Shell glob excludes dotfiles | Intentional — system install relies on shell env var; project `.env` stays in repo dir for dev |
| `zsh: no matches found` on YouTube URLs with `?si=...` | zsh `NOMATCH` option treats `?` as glob char | Stage 5 — `noglob` alias prefix |
| `ERROR: [youtube] ...: Please sign in. Use --cookies-from-browser` | YouTube blocks unauthenticated yt-dlp since late 2024 | Stage 7 — set `OPEN_SCRIBE_COOKIES_BROWSER` |
| Keychain prompt appears on first `scribe` run | Chrome on macOS encrypts cookies with Keychain-stored key; yt-dlp needs to read it | Click "Always Allow"; one-time. Or use Safari/Firefox (no prompt) |
| `WARNING: n challenge solving failed ... Only images are available` (or `Requested format is not available` after retry-with-cookies) | YouTube's `n=` param needs JS execution; yt-dlp's Python API defaults to deno-only and finds nothing if deno isn't installed | Stage 8 — `brew install deno` |
| yt-dlp self-reports "up to date: 2025.9.23" while actually being newer | `_check_and_update_ytdlp` in `scribe.zsh` shows the requirements.txt-pinned version, not the live `yt-dlp --version` | Cosmetic — actual updates happen via `uv pip install --upgrade --resolution=highest yt-dlp` (upstream commit `105f3e3`) |
| `ERROR: Postprocessing: ffprobe and ffmpeg not found` after download succeeds | yt-dlp invokes ffmpeg/ffprobe for audio extraction; not installed by default on macOS | Pre-flight — `brew install ffmpeg` |

## Three locations of the key (after full setup)

| Path | Role | Perms |
|---|---|---|
| `~/.config/secrets/.env` | Master — sourced into shell by `~/.zshrc` | 600 |
| `<repo>/.env` | Project-local copy for dev; loaded by `load_dotenv()` but shell env wins | 600 |
| `~/.open-scribe/.env` | scribe.sh runtime cache, sourced on every `scribe` invocation | 600 (must enforce — Stage 6) |

When rotating the key, update **all three** or delete the latter two so they regenerate.
