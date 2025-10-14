# Open-Scribe zsh helper
# - Supports both YouTube URLs and local audio file paths
# - Expands ~ and env vars for local paths
# - Activates project-local .venv before running
# - No hardcoded paths: resolves repo dir from this file path or $OPEN_SCRIBE_REPO_DIR

function scribe() {
  # Allow override via env var; fallback to default project path
  local DEFAULT_REPO_DIR="/Users/jaesolshin/Documents/GitHub/open-scribe"
  local REPO_DIR="${OPEN_SCRIBE_REPO_DIR:-$DEFAULT_REPO_DIR}"
  local ENTRY="${REPO_DIR}/main.py"
  local VENV_ACTIVATE="${REPO_DIR}/.venv/bin/activate"

  if [[ -z "$1" ]]; then
    echo "❌ 오류: YouTube URL 또는 로컬 오디오 파일 경로를 지정해주세요."
    echo "사용법: scribe <YouTube_URL|local_audio_path> [옵션들...]"
    return 1
  fi

  # Activate virtualenv if available
  if [[ -f "$VENV_ACTIVATE" ]]; then
    source "$VENV_ACTIVATE"
  fi

  # Check and update yt-dlp if needed (only for YouTube URLs)
  if [[ "$1" == http://* || "$1" == https://* ]]; then
    _check_and_update_ytdlp "$REPO_DIR"
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

  # Decide whether URL or local file
  if [[ "$EXPANDED_INPUT" == http://* || "$EXPANDED_INPUT" == https://* ]]; then
    python "$ENTRY" "$EXPANDED_INPUT" "$@"
  else
    # Treat as local audio path (main.py will revalidate)
    python "$ENTRY" "$EXPANDED_INPUT" "$@"
  fi
}

# Helper function to check and update yt-dlp
function _check_and_update_ytdlp() {
  local REPO_DIR="$1"
  local VENV_ACTIVATE="${REPO_DIR}/.venv/bin/activate"
  local VERSION_CHECK_FILE="${REPO_DIR}/.ytdlp_version_check"
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
  
  echo "🔍 yt-dlp 버전 확인 중..."
  
  # Get current and latest versions
  local CURRENT_VERSION=$(uv pip list 2>/dev/null | grep yt-dlp | awk '{print $2}' || echo "not_found")
  
  if [[ "$CURRENT_VERSION" == "not_found" ]]; then
    echo "⚠️  yt-dlp가 설치되지 않았습니다. 설치 중..."
    cd "$REPO_DIR"
    uv pip install yt-dlp
    echo "$CURRENT_DATE" > "$VERSION_CHECK_FILE"
    return 0
  fi
  
  # Check for updates (simplified check - just try to update)
  echo "📦 yt-dlp 업데이트 확인 중..."
  cd "$REPO_DIR"
  local UPDATE_OUTPUT=$(uv pip install --upgrade yt-dlp 2>&1)
  
  if echo "$UPDATE_OUTPUT" | grep -q "Successfully installed"; then
    local NEW_VERSION=$(echo "$UPDATE_OUTPUT" | grep -o "yt-dlp==[0-9]\+\.[0-9]\+\.[0-9]\+" | cut -d'=' -f3)
    echo "✅ yt-dlp가 업데이트되었습니다: $CURRENT_VERSION → $NEW_VERSION"
  else
    echo "✅ yt-dlp가 최신 버전입니다: $CURRENT_VERSION"
  fi
  
  # Mark that we checked today
  echo "$CURRENT_DATE" > "$VERSION_CHECK_FILE"
}

# Optional: alias for convenience
alias oscribe=scribe


