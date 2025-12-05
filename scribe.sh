#!/bin/bash

# Open-Scribe bash/zsh helper
# - Supports both YouTube URLs and local audio file paths
# - Expands ~ and env vars for local paths
# - Activates project-local .venv before running
# - Uses OPEN_SCRIBE_HOME for installation directory

function scribe() {
  local INSTALL_DIR="${OPEN_SCRIBE_HOME:-$HOME/.local/share/open-scribe}"
  local ENTRY="${INSTALL_DIR}/main.py"
  local VENV_ACTIVATE="${INSTALL_DIR}/.venv/bin/activate"

  if [[ -z "$1" ]]; then
    echo "❌ Error: YouTube URL or local audio file path required."
    echo "Usage: scribe <YouTube_URL|local_audio_path> [options...]"
    return 1
  fi

  # Check if installation directory exists
  if [[ ! -d "$INSTALL_DIR" ]]; then
    echo "❌ Error: open-scribe not found at $INSTALL_DIR"
    echo "Please run: make install"
    return 1
  fi

  # Activate virtualenv if available
  if [[ -f "$VENV_ACTIVATE" ]]; then
    source "$VENV_ACTIVATE"
  fi

  # Check and update yt-dlp if needed (only for YouTube URLs)
  if [[ "$1" == http://* || "$1" == https://* ]]; then
    _check_and_update_ytdlp "$INSTALL_DIR"
  fi

  # Input normalization: strip quotes and expand ~ / env vars for local paths only
  local RAW_INPUT="$1"; shift
  local EXPANDED_INPUT

  # Only expand for local paths, not URLs
  if [[ "$RAW_INPUT" == http://* || "$RAW_INPUT" == https://* ]]; then
    EXPANDED_INPUT="$RAW_INPUT"
  else
    EXPANDED_INPUT=$(eval echo "$RAW_INPUT")
  fi

  # Run transcription
  python "$ENTRY" "$EXPANDED_INPUT" "$@"
}

# Helper function to check and update yt-dlp
function _check_and_update_ytdlp() {
  local INSTALL_DIR="$1"
  local VENV_ACTIVATE="${INSTALL_DIR}/.venv/bin/activate"
  local VERSION_CHECK_FILE="${INSTALL_DIR}/.ytdlp_version_check"
  local CURRENT_DATE=$(date +%Y%m%d)

  # Check if we already checked today
  if [[ -f "$VERSION_CHECK_FILE" ]]; then
    local LAST_CHECK=$(cat "$VERSION_CHECK_FILE" 2>/dev/null || echo "0")
    if [[ "$LAST_CHECK" == "$CURRENT_DATE" ]]; then
      return 0  # Already checked today
    fi
  fi

  # Activate venv for version check
  if [[ -f "$VENV_ACTIVATE" ]]; then
    source "$VENV_ACTIVATE"
  fi

  echo "🔍 Checking yt-dlp version..."

  # Get current and latest versions
  local CURRENT_VERSION=$(uv pip list 2>/dev/null | grep yt-dlp | awk '{print $2}' || echo "not_found")

  if [[ "$CURRENT_VERSION" == "not_found" ]]; then
    echo "⚠️  yt-dlp not installed. Installing..."
    cd "$INSTALL_DIR"
    uv pip install yt-dlp
    echo "$CURRENT_DATE" > "$VERSION_CHECK_FILE"
    return 0
  fi

  # Check for updates (simplified check - just try to update)
  echo "📦 Checking for yt-dlp updates..."
  cd "$INSTALL_DIR"
  local UPDATE_OUTPUT=$(uv pip install --upgrade yt-dlp 2>&1)

  if echo "$UPDATE_OUTPUT" | grep -q "Successfully installed"; then
    local NEW_VERSION=$(echo "$UPDATE_OUTPUT" | grep -o "yt-dlp==[0-9]\+\.[0-9]\+\.[0-9]\+" | cut -d'=' -f3)
    echo "✅ yt-dlp updated: $CURRENT_VERSION → $NEW_VERSION"
  else
    echo "✅ yt-dlp is up to date: $CURRENT_VERSION"
  fi

  # Mark that we checked today
  echo "$CURRENT_DATE" > "$VERSION_CHECK_FILE"
}

# Optional: alias for convenience
alias oscribe=scribe
